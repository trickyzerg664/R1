"""顺序运行已冻结的父评价/B/T验证；默认只检查，不复制训练或评分算法。"""
import argparse,datetime,fcntl,hashlib,json,math,os,re,signal,subprocess,time
from pathlib import Path

def now():
    """@brief 返回当前UTC记录时间。
    @return ISO格式时间字符串。
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def save(path, value):
    """@brief 原子发布小型状态，避免读到半个JSON。
    @param path 目标Path。
    @param value JSON兼容对象。
    @return 无。
    @raises OSError 写入失败。
    """
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2));temporary.replace(path)

def rows(path):
    """@brief 读取已闭合JSONL行，未完成尾部不作为进度。
    @param path 日志Path。
    @return 完整JSON记录列表。
    @raises ValueError 完整行损坏。
    """
    if not path.exists():return []
    return [json.loads(line) for line in path.read_text().splitlines(keepends=True)
            if line.endswith('\n') and line.strip()]

def verify(plan):
    """@brief 核对冻结代码/配置/数据与父模型验收，拒绝运行中漂移。
    @param plan 已冻结运行方案映射。
    @return 无。
    @raises RuntimeError 哈希不符或父Actor未验收。
    """
    # 大父权重已单独流式核验；本函数只重复核对小型冻结清单。
    for name,digest in plan['hashes'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Frozen content changed: '+name)
    if not json.loads(Path(plan['parent_verification']).read_text())['successful']:
        raise RuntimeError('Parent actor verification missing')

def training_summary(directory):
    """@brief 读取真实训练事件，核验有限更新及指标覆盖，不把计划值写成完成值。
    @param directory 当前组产物Path。
    @return 实测训练步数、最新指标和已发布checkpoint列表。
    @raises RuntimeError 非有限指标、跳过更新或微批覆盖不完整。
    """
    trained=[e for e in rows(directory/'metrics.jsonl') if e.get('event')=='train']
    for event in trained:
        m=event['metrics']
        # 每rank两次mini更新；全八rank微批观测共256，任意跳过均停止该组。
        if m.get('actor/optimizer_step')!=1 or m.get('actor/optimizer_updates_per_rank')!=2:
            raise RuntimeError('Optimizer update incomplete at step '+str(event['step']))
        # 错误同时报告预期/实测及步数，保留256门限便于定位覆盖丢失。
        if m.get('actor/observations/micro_batches_sum')!=256:
            raise RuntimeError('Microbatch observation coverage differs at step '+str(event['step'])+
                               ': expected=256 actual='+str(m.get('actor/observations/micro_batches_sum')))
        for key in ('actor/total_loss','actor/grad_norm','actor/entropy_token_weighted','actor/kl_loss'):
            if not math.isfinite(m.get(key,float('nan'))):raise RuntimeError('Nonfinite '+key)
    points=sorted(int(p.parent.name.split('_')[-1]) for p in (directory/'checkpoints').glob('step_*/COMPLETE.json'))
    return dict(trained_step=trained[-1]['step'] if trained else 0,
                latest_metrics=trained[-1]['metrics'] if trained else {},published_checkpoint_steps=points)

def evaluation_summary(directory, count):
    """@brief 核验完整独立评价，汇总原EM、缺答案及原生终止覆盖。
    @param directory 独立评价产物Path。
    @param count 固定评价题数，本轮256。
    @return 实际评价与原生终止覆盖统计。
    @raises RuntimeError 题目缺失、重复或出现训练事件。
    """
    answers=rows(directory/'answers.jsonl')
    if len(answers)!=count or len({x['question_id'] for x in answers})!=count:
        raise RuntimeError('Evaluation incomplete/duplicated')
    if any(e.get('event')=='train' for e in rows(directory/'metrics.jsonl')):
        raise RuntimeError('val_only performed training')
    reports=[x['report'] for x in rows(directory/'process-audit.jsonl')
             if x['phase']=='validation' and 'original_em' in x['report']]
    tokens=[t for r in reports for t in r.get('token_diagnostics',[])]
    known=sum(t.get('finish_reason') in ('stop','length') for t in tokens)
    return dict(count=count,correct=sum(x['reward'] for x in answers),
        missing=sum(not x['extracted_answer'] for x in answers),parameter_updates=0,
        native_events=len(tokens),known_finish_events=known,
        native_coverage=known/len(tokens) if tokens else 0.,
        stop_events=sum(t.get('finish_reason')=='stop' for t in tokens))

def publish(run, state):
    """@brief 发布实测状态并更新本次运行记录/台账的独立区块。
    @param run 产物根Path。
    @param state 当前真实状态对象。
    @return 无。
    @raises OSError 持久化失败。
    @note 保留手工历史，仅替换本run自动区块。
    """
    state=dict(state,checked_utc=now());save(run/'status.json',state)
    plan=json.loads((run/'plan.json').read_text())
    begin='<!-- '+run.name+'-current -->';end='<!-- /'+run.name+'-current -->'
    # 两份文档只展示实测阶段/步数，长指标留在status.json。
    compact={k:v for k,v in state.items() if k!='latest_metrics'}
    block=begin+'\n\n'+json.dumps(compact,ensure_ascii=False,indent=2)+'\n\n'+end
    for name in plan['documents']:
        path=Path(name);text=path.read_text()
        if begin in text:
            a=text.index(begin);b=text.index(end,a)+len(end);text=text[:a]+block+text[b:]
        else:text+='\n\n'+block+'\n'
        temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(text);temporary.replace(path)

def interrupt(signum, frame):
    """@brief 将显式停止信号转为可清理的异常，使所属子进程正常收尾。
    @param signum POSIX信号号。
    @param frame 信号调用栈，仅接口兼容。
    @return 无。
    @raises RuntimeError 收到停止信号。
    """
    raise RuntimeError('Supervisor interrupted: '+str(signum))

def owned_processes(ray_directory, proc_root=Path('/proc')):
    """@brief 只读枚举唯一Ray环境标记的进程身份，不暴露其余环境变量。
    @param ray_directory 本阶段独占Ray目录字符串。
    @param proc_root proc文件系统根；CPU测试可用目录夹具。
    @return (pid,启动ticks)列表。
    """
    owned=[]
    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or int(entry.name)==os.getpid():continue
        try:
            if ('RAY_TMPDIR='+ray_directory).encode() not in entry.joinpath('environ').read_bytes().split(b'\0'):
                continue
            # comm字段允许空格，先从右括号分割再定位第22字段，避免PID复用判断错位。
            ticks=entry.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
            owned.append((int(entry.name),ticks))
        except OSError:continue
    return owned

def cleanup_owned(ray_directory):
    """@brief 清理本阶段唯一RAY_TMPDIR标记的进程，保留独立检索与其他任务。
    @param ray_directory 本阶段独占Ray目录字符串。
    @return 已通知终止的进程数量。
    @note 比对完整环境值及/proc启动身份，禁止全局ray stop或按进程名清理。
    """
    owned=owned_processes(ray_directory)
    for pid,ticks in owned:
        try:os.kill(pid,signal.SIGTERM)
        except (OSError,ProcessLookupError):pass
    # 给正常退出留时间，残留PID仅在启动身份仍相同的情况下强制终止。
    time.sleep(10)
    for pid,ticks in owned:
        try:
            if Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]==ticks:os.kill(pid,signal.SIGKILL)
        except (OSError,ProcessLookupError):pass
    return len(owned)

def run_phase(run, phase, plan, deadline):
    """@brief 启动冻结阶段并持续核验真实进度、显存和总时间，异常保留现场。
    @param run 本次产物根Path。
    @param phase 含名称、目录、命令及训练/评价类型的阶段映射。
    @param plan 冻结的运行方案。
    @param deadline 总预算截止Unix时间，已预留收尾时间。
    @return 阶段实测结果对象。
    @raises RuntimeError 子进程失败、预算/显存/数值异常。
    @note 只终止本次子进程组及本阶段唯一Ray环境对应进程。
    """
    verify(plan);directory=Path(phase['directory']);directory.mkdir(parents=True,exist_ok=True)
    ray_directory=plan['ray_base']+'-'+phase['name']
    # 原环境可能已有RAY_TMPDIR，分步覆盖避免重复关键字且明确独占阶段。
    environment=dict(os.environ);environment.update(plan['environment']);environment['RAY_TMPDIR']=ray_directory
    environment.pop('RAY_ADDRESS',None)
    with (directory/'console.log').open('ab',buffering=0) as output:
        child=subprocess.Popen(phase['argv'],cwd=plan['repository'],env=environment,
                               stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    identity=dict(pid=child.pid,started_utc=now(),proc_start_ticks=Path('/proc',str(child.pid),'stat').read_text().split()[21],argv=phase['argv'])
    save(directory/'process.json',identity);next_report=0
    try:
        while child.poll() is None:
            # 驱动总显存包含检索服务；不降batch/上下文来掩盖超限。
            readings=[int(x) for x in re.findall(r'(\d+)/65536 MiB',subprocess.check_output(['mx-smi'],text=True,timeout=15))]
            if len(readings)!=8 or max(readings)>56*1024:raise RuntimeError('GPU memory budget exceeded/unknown')
            if time.time()>=deadline:raise RuntimeError('Wall-clock budget reached')
            summary=training_summary(directory) if phase['kind']=='train' else dict(trained_step=0)
            if time.time()>=next_report:
                publish(run,dict(status='running',phase=phase['name'],child_pid=child.pid,
                                 gpu_current_MiB=readings,**summary))
                next_report=time.time()+60
            time.sleep(10)
        if child.wait()!=0:raise RuntimeError('Stage failed: '+phase['name']+' exit='+str(child.returncode))
        if phase['kind']=='train':
            summary=training_summary(directory)
            if summary['trained_step']!=20:raise RuntimeError('Training did not reach20')
            # 冷评价前复用原完整checkpoint逐文件校验，包括所有rank状态。
            from verl.experimental.difficulty.checkpoint import read_checkpoint
            metadata=read_checkpoint(directory/'checkpoints/step_20')
            if metadata['step']!=20:raise RuntimeError('Checkpoint step differs')
        else:summary=evaluation_summary(directory,256)
        save(directory/'summary.json',summary);return summary
    finally:
        # 正常或失败都清理自己的Ray环境，防止顺序下一阶段显存被残留占用。
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=60)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        cleanup_owned(ray_directory)

def parent_evaluation(run, plan, deadline):
    """@brief 复用显式绑定且重新验收的父评价，默认仍执行原父评价阶段。
    @param run 当前运行产物根Path。
    @param plan 冻结运行计划，可包含verified_parent_evaluation目录。
    @param deadline 总预算截止Unix时间。
    @return 通过完整性及零更新检查的父评价结果。
    @raises RuntimeError 缓存评价缺失、非完整或含训练更新。
    @note 缓存原始文件须纳入plan.hashes；复用信息单独落盘不改旧实验。
    """
    cached = plan.get('verified_parent_evaluation')
    # 默认仍创建原父评价任务；复用只能由冻结计划显式指定。
    if not cached:
        return run_phase(run, plan['phases'][0], plan, deadline)
    # 外部评价只在显式冻结所有原始证据后复用，不能相信单个summary文件。
    verify(plan)
    directory = Path(cached)
    for filename in ('answers.jsonl', 'metrics.jsonl', 'process-audit.jsonl'):
        if str(directory/filename) not in plan['hashes']:
            raise RuntimeError('Cached parent evidence is not frozen: '+filename)
    summary = evaluation_summary(directory, 256)
    target = Path(plan['phases'][0]['directory'])
    target.mkdir(parents=True, exist_ok=True)
    save(target/'summary.json', summary)
    save(target/'reused-evaluation.json', dict(source=str(directory), verified_utc=now(),
                                             parameter_updates=0))
    return summary

def main():
    """@brief 默认检查冻结计划；显式--launch才顺序执行父评价和两组20步。
    @return 无。
    @raises RuntimeError 已有训练、重复运行或阶段验收失败。
    @note 持有八卡独占锁；20步结果完成后留待分析，不自动扩展40/60步。
    """
    parser=argparse.ArgumentParser();parser.add_argument('--run-directory',required=True);parser.add_argument('--launch',action='store_true')
    args=parser.parse_args();run=Path(args.run_directory).resolve();plan=json.loads((run/'plan.json').read_text());verify(plan)
    if not args.launch:print(json.dumps(dict(check='passed',gpu_started=False)));return
    started=datetime.datetime.fromisoformat(json.loads((run/'started.json').read_text())['utc']).timestamp()
    deadline=started+46*3600
    with (run.parent/'.process-train-g8.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (run/'supervisor-process.json').exists():raise RuntimeError('Already launched')
        if any('-m verl.trainer.main_ppo' in line for line in subprocess.check_output(['ps','-eo','args'],text=True).splitlines()):
            raise RuntimeError('Another trainer is running')
        # 启动时再次核实八卡仅有已知独立检索，不抢占其他GPU任务。
        gpu_text=subprocess.check_output(['mx-smi'],text=True)
        section=gpu_text.split('| Process:',1)[1] if '| Process:' in gpu_text else ''
        gpu_pids={int(p) for p in re.findall(r'\|\s+\d+\s+(\d+)\s+',section)}
        if gpu_pids-{plan['retriever_pid']}:raise RuntimeError('GPU occupied by another task')
        save(run/'supervisor-process.json',dict(pid=os.getpid(),started_utc=now()))
        signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
        try:
            # 显式缓存先重验，随后仍按同一健康/终止门限选择两臂。
            parent=parent_evaluation(run,plan,deadline)
            # 健康验收预先固定：缺答案不超过5%，父评价无更新；未通过便停止锁定新父模型。
            if parent['missing']>12:raise RuntimeError('Parent generation failed health gate')
            bounded=parent['native_coverage']>=.95 and parent['stop_events']>0
            selected=plan['phases'][1:3]+(plan['phases'][3:5] if bounded else plan['fallback_phases'])
            save(run/'selected-design.json',dict(bounded_reward_enabled=bounded,reason='native termination coverage gate',parent=parent))
            for phase in selected:run_phase(run,phase,plan,deadline)
            publish(run,dict(status='completed_first20',phase='analysis_pending',bounded_reward_enabled=bounded,
                             B=json.loads((run/'B-eval/summary.json').read_text()),
                             T=json.loads((run/('T-eval' if bounded else 'T-LK-eval')/'summary.json').read_text()),
                             next='Compare paired D256 and rollout evidence before extending to40/60'))
        except Exception as exc:
            publish(run,dict(status='failed',phase='stopped',error=str(exc)));raise

if __name__=='__main__':
    main()
