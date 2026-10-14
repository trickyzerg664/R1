# T1024语义复核：official_grpo_v02

标准：T1024-equivalence-v1

原始EM不变；只对明确等价的最终答案加分。标签错误、歧义、缺关键字段不计新增正确。

{
  "model": "official_grpo_v02",
  "policy": "T1024-equivalence-v1",
  "evaluation_complete": true,
  "review_complete": true,
  "n": 1024,
  "original_correct": 456,
  "equivalent_added": 131,
  "incorrect": 335,
  "uncertain": 87,
  "label_issue": 15,
  "pending": 0,
  "original_em": 0.4453125,
  "semantic_correct_confirmed": 587,
  "semantic_accuracy": 0.5732421875,
  "records_digest": "29b077346c29816132765665e8a416541a156a2618e1970cd4def79c265e4ee0",
  "sources": {
    "nq": {
      "n": 335,
      "original_correct": 173,
      "semantic_correct": 200
    },
    "hotpotqa": {
      "n": 689,
      "original_correct": 283,
      "semantic_correct": 387
    }
  }
}

## EM错题逐项裁定

### row 3：uncertain
wal-mart is a prime example of which type organization?
标准：["multinational retail corporation"]
答案：retail organization
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 5：incorrect
what is the highest base on the ph scale?
标准：["greater than 14"]
答案：14
理由：逐题审阅最终答案：14；标准：["greater than 14"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 6：incorrect
where are antibodies made and by what type of lymphocyte?
标准：["B cells", "lymph"]
答案：bone marrow
理由：逐题审阅最终答案与标准：bone marrow / ["B cells", "lymph"]；实体、数值、时间或所問字段不一致，维持错误。

### row 9：incorrect
the creation of human beings in the kumulipo happens during which wā or period of creation?
标准：["In the ninth wā", "the ninth wā,", "the ninth wā", "the ninth"]
答案：ao
理由：逐题审阅最终答案：ao；标准：["In the ninth wā", "the ninth wā,", "the ninth wā", "the ninth"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 11：incorrect
number of employees in the department of health and human services?
标准：["79,540 (2015)", "79,540"]
答案：70,000
理由：逐题审阅最终答案与标准：70,000 / ["79,540 (2015)", "79,540"]；实体、数值、时间或所問字段不一致，维持错误。

### row 15：equivalent
how did the dominican republic get its name?
标准：["patron saint, Saint Dominic"]
答案：Saint Dominic
理由：Saint Dominic直接指标准的patron saint Saint Dominic；不要求重复patron saint修饰。

### row 21：incorrect
when was the last time an american won the new york marathon?
标准：["2009", "2017"]
答案：1977
理由：逐题审阅最终答案与标准：1977 / ["2009", "2017"]；实体、数值、时间或所問字段不一致，维持错误。

### row 26：equivalent
who has majority in the house and senate?
标准：["Republican"]
答案：Republicans
理由：Republicans与Republican均指同一共和党阵营，单复数形式不同。

### row 29：equivalent
when did reba mcentire record back to god?
标准：["February 3, 2017", "2017"]
答案：January 20, 2017
理由：January 20, 2017与标准允许的2017年份相容；问题未要求某一特定日期版本。

### row 31：uncertain
list of strict nature reserve in the philippines?
标准：["Palawan", "Lake Malimanga", "Olango Island", "Calauit Safari Park", "Lake Buluan", "Calavite and FB Harrison"]
答案：Palawan Biosphere Reserve
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 33：incorrect
when do you pray the chaplet of divine mercy?
标准：["Good Friday"]
答案：Divine Mercy Sunday
理由：逐题审阅最终答案：Divine Mercy Sunday；标准：["Good Friday"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 34：uncertain
what hangs from the trees in the bayou?
标准：["Spanish moss"]
答案：moss
理由：moss比Spanish moss宽泛，无法唯一指认该植物。

### row 37：incorrect
who does bryce dallas howard play in the grinch?
标准：["Surprised Who"]
答案：Cindy Lou Who
理由：逐题审阅最终答案：Cindy Lou Who；标准：["Surprised Who"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 39：equivalent
who was the declaration of independence written for?
标准：["the Second Continental Congress"]
答案：Congress
理由：独立宣言语境中的Congress指标准的Second Continental Congress，省略届次不改变指代。

### row 40：incorrect
what disney cartoon character's middle name is fauntleroy?
标准：["Donald Duck", "Donald Fauntleroy Duck"]
答案：Little Lord Fauntleroy
理由：逐题审阅最终答案与标准：Little Lord Fauntleroy / ["Donald Duck", "Donald Fauntleroy Duck"]；实体、数值、时间或所問字段不一致，维持错误。

### row 42：incorrect
communities of similar organisms found in a particular environment are called?
标准：["species", "habitat"]
答案：ecosystem
理由：逐题审阅最终答案与标准：ecosystem / ["species", "habitat"]；实体、数值、时间或所問字段不一致，维持错误。

### row 48：uncertain
who died in the first episode of stranger things?
标准：["Benny"]
答案：the owner
理由：the owner未说明哪位店主，角色描述不足以唯一确定标准Benny。

### row 49：incorrect
when did equus first appear in fossil record?
标准：["1820s", "~3.5 million years old", "about 3.5 mya"]
答案：Eocene
理由：逐题审阅最终答案与标准：Eocene / ["1820s", "~3.5 million years old", "about 3.5 mya"]；实体、数值、时间或所問字段不一致，维持错误。

### row 52：uncertain
where is wake forest located in north carolina?
标准：["78.51889°W", "in Franklin and Wake counties", "35.97333°N"]
答案：Wake County
理由：Wake County仅给两个标准县中的一个，保留地点字段不全。

### row 55：incorrect
what episode does goku give up against cell?
标准：["165", "180"]
答案：Episode 88
理由：逐题审阅最终答案与标准：Episode 88 / ["165", "180"]；实体、数值、时间或所問字段不一致，维持错误。

### row 59：incorrect
who invented the chip in. debit cards?
标准：["Helmut Gröttrup", "Jürgen Dethloff"]
答案：Forrest Parry
理由：逐题审阅最终答案与标准：Forrest Parry / ["Helmut Gröttrup", "Jürgen Dethloff"]；实体、数值、时间或所問字段不一致，维持错误。

### row 60：uncertain
who made the song we are the world?
标准：["produced by Quincy Jones"]
答案：Michael Jackson
理由：Michael Jackson是共同词曲作者，标准为制作人Quincy Jones；made问法含角色歧义，不按同人等价。

### row 65：incorrect
what was the tower of london originally used for?
标准：["a royal residence", "as a royal residence"]
答案：military reasons
理由：逐题审阅最终答案与标准：military reasons / ["a royal residence", "as a royal residence"]；实体、数值、时间或所問字段不一致，维持错误。

### row 66：uncertain
what type of boundary was the mexico earthquake?
标准：["a subduction zone"]
答案：convergent
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 68：incorrect
where are they playing the superbowl at this year?
标准：["Minneapolis, Minnesota"]
答案：Los Angeles Stadium at Hollywood Park
理由：逐题审阅最终答案与标准：Los Angeles Stadium at Hollywood Park / ["Minneapolis, Minnesota"]；实体、数值、时间或所問字段不一致，维持错误。

### row 69：label_issue
who bowled the last over of the 2007 world twenty20 that india won?
标准：["Pakistan"]
答案：Joginder Sharma
理由：金标准Pakistan为国家，题目问投球者；轨迹支持Joginder Sharma。标签类型错误单列，不计等价加分。

### row 72：incorrect
what is the angle of the tower of pisa?
标准：["about 3.99 degrees", "3.99 degrees", "at about 3.99 degrees"]
答案：5.5 degrees
理由：逐题审阅最终答案：5.5 degrees；标准：["about 3.99 degrees", "3.99 degrees", "at about 3.99 degrees"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 73：incorrect
who sold the most records elvis or the beatles?
标准：["The Beatles"]
答案：Elvis
理由：逐题审阅最终答案与标准：Elvis / ["The Beatles"]；实体、数值、时间或所問字段不一致，维持错误。

### row 74：incorrect
who has the most followers in the world on instagram?
标准：["Instagram's own account", "Instagram"]
答案：Selena Gomez
理由：逐题审阅最终答案：Selena Gomez；标准：["Instagram's own account", "Instagram"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 75：incorrect
who does stefan marry in the vampire diaries?
标准：["Caroline Forbes"]
答案：Elena
理由：逐题审阅最终答案：Elena；标准：["Caroline Forbes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 76：incorrect
how much is the united states in debt to china?
标准：["$1.06 trillion", "1,200.5"]
答案：$1.18 trillion
理由：逐题审阅最终答案：$1.18 trillion；标准：["$1.06 trillion", "1,200.5"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 77：equivalent
where in the bible is the book of revelation?
标准：["last book", "in the New Testament"]
答案：New Testament
理由：New Testament与in the New Testament相同，只省略介词。

### row 79：incorrect
who are the nbc olympic ice skating commentators?
标准：["Jonny Moseley", "Tanith White", "Chris Vosters", "Luke Van Valin", "Charlie White", "Johnny Weir", "Tara Lipinski", "Andrea Joyce", "Terry Gannon"]
答案：Tom Hammond
理由：逐题审阅最终答案：Tom Hammond；标准：["Jonny Moseley", "Tanith White", "Chris Vosters", "Luke Van Valin", "Charlie White", "Johnny Weir", "Tara Lipinski", "Andrea Joyce", "Terry Gannon"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 83：incorrect
how many episodes of season 5 of curse of oak island?
标准：["18"]
答案：13
理由：逐题审阅最终答案与标准：13 / ["18"]；实体、数值、时间或所問字段不一致，维持错误。

### row 84：uncertain
where is a simple gear train used in real life?
标准：["Automobile drivetrains"]
答案：bicycle
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 87：incorrect
who plays charles on have and have nots?
标准：["Nick Sager", "Nick Sagar"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 88：uncertain
when is the publishers clearing house sweepstakes drawing?
标准：["just after the Super Bowl"]
答案：Super Bowl
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 89：incorrect
who plays connor's mom in madeas christmas?
标准：["Kathy Najimy"]
答案：Tika Sumpter
理由：逐题审阅最终答案与标准：Tika Sumpter / ["Kathy Najimy"]；实体、数值、时间或所問字段不一致，维持错误。

### row 90：equivalent
which animal is the carrier of the h1n1 virus?
标准：["Pig", "pigs"]
答案：swine
理由：swine与pigs同义，所问病毒动物载体一致。

### row 94：incorrect
where does the red river start and end in louisiana?
标准：["the Texas Panhandle"]
答案：Louisiana
理由：逐题审阅最终答案与标准：Louisiana / ["the Texas Panhandle"]；实体、数值、时间或所問字段不一致，维持错误。

### row 95：equivalent
who invented the first home video security system?
标准：["her husband Albert Brown", "Marie Van Brittan Brown"]
答案：Marie Brown
理由：轨迹明确该安全系统发明者称Marie Brown；与Marie Van Brittan Brown同一人。

### row 97：incorrect
in the dynastic cycle what is the right to rule called?
标准：["the Mandate of Heaven", "Mandate of Heaven"]
答案：dynastéia
理由：逐题审阅最终答案：dynastéia；标准：["the Mandate of Heaven", "Mandate of Heaven"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 101：incorrect
when was you'll never walk alone first released?
标准：["1945"]
答案：1963
理由：逐题审阅最终答案：1963；标准：["1945"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 105：equivalent
who took part in the american civil war?
标准：["nationalists of the Union"]
答案：Union
理由：Union与nationalists of the Union指同一内战参战方。

### row 107：equivalent
who became king of erebor after thorin dies?
标准：["Dáin", "his cousin Dáin"]
答案：Dáin Ironfoot
理由：Dáin Ironfoot与Dáin为同一角色的完整名和短名。

### row 112：incorrect
what is the rank of india in economic growth?
标准：["12 / 225", "12"]
答案：100th
理由：逐题审阅最终答案与标准：100th / ["12 / 225", "12"]；实体、数值、时间或所問字段不一致，维持错误。

### row 114：incorrect
ajay devgan preity zinta and madhuri dixit movie?
标准：["Yeh Raaste Hain Pyaar Ke"]
答案：Dedh Ishqiya
理由：逐题审阅最终答案与标准：Dedh Ishqiya / ["Yeh Raaste Hain Pyaar Ke"]；实体、数值、时间或所問字段不一致，维持错误。

### row 118：incorrect
who did the chiefs play in the playoffs?
标准：["the Tennessee Titans"]
答案：Houston Texans
理由：逐题审阅最终答案：Houston Texans；标准：["the Tennessee Titans"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 120：incorrect
where will the first round of march madness be played?
标准：["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]
答案：Alamodome
理由：逐题审阅最终答案与标准：Alamodome / ["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]；实体、数值、时间或所問字段不一致，维持错误。

### row 121：incorrect
where can you find convergent boundaries on earth?
标准：["Mariana Trench"]
答案：Earth
理由：逐题审阅最终答案与标准：Earth / ["Mariana Trench"]；实体、数值、时间或所問字段不一致，维持错误。

### row 123：uncertain
what is the central idea of the poem the rime of ancient mariner?
标准：["a violation of nature"]
答案：punishment and redemption
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 124：equivalent
what is katie running from in safe haven?
标准：["her abusive husband"]
答案：abusive and alcoholic husband
理由：abusive and alcoholic husband保留标准的abusive husband指代，并附加不冲突描述。

### row 125：incorrect
who plays the mouse in alice in wonderland?
标准：["Barbara Windsor"]
答案：Alan Rickman
理由：逐题审阅最终答案与标准：Alan Rickman / ["Barbara Windsor"]；实体、数值、时间或所問字段不一致，维持错误。

### row 126：equivalent
who is the girl who played in the grinch?
标准：["Taylor Michel Momsen"]
答案：Taylor Momsen
理由：Taylor Momsen与Taylor Michel Momsen为同一演员，省略中间名。

### row 129：uncertain
who made the movie fifty shades of grey?
标准：["Universal Pictures and Focus Features", "Sam Taylor-Johnson"]
答案：Universal Pictures
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 130：uncertain
what song did the titanic band play when it sank?
标准：["\"Autumn\""]
答案：Nearer, My God, to Thee
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 131：uncertain
when do willow and tara get back together?
标准：["Entropy", "Seeing Red"]
答案：season 6
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 132：incorrect
when was the bridge over the hoover dam built?
标准：["2010"]
答案：February 2005
理由：逐题审阅最终答案与标准：February 2005 / ["2010"]；实体、数值、时间或所問字段不一致，维持错误。

### row 138：incorrect
when did the celebrities enter the big brother house?
标准：["February 7, 2018", "2017"]
答案：June 20, 2014
理由：逐题审阅最终答案：June 20, 2014；标准：["February 7, 2018", "2017"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 139：incorrect
who said some are born great in twelfth night?
标准：["Malvolio", "letter that Maria wrote"]
答案：Feste
理由：逐题审阅最终答案与标准：Feste / ["Malvolio", "letter that Maria wrote"]；实体、数值、时间或所問字段不一致，维持错误。

### row 140：equivalent
where does the edinburgh fringe festival take place?
标准：["in Edinburgh, Scotland"]
答案：Edinburgh
理由：问题限定Edinburgh Fringe Festival，Edinburgh为标准Edinburgh, Scotland中的同一城市。

### row 142：uncertain
what is the job of the whip in congress?
标准：["to ensure party discipline"]
答案：leader
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 146：incorrect
who carried the usa flag in opening ceremony?
标准：["Erin Hamlin"]
答案：Dawn Staley
理由：逐题审阅最终答案：Dawn Staley；标准：["Erin Hamlin"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 151：incorrect
what is the speed of the nascar pace car?
标准：["pit road speed"]
答案：118 mph
理由：逐题审阅最终答案：118 mph；标准：["pit road speed"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 152：equivalent
what kind of book is where's waldo?
标准：["puzzle"]
答案：puzzle book
理由：puzzle book与puzzle在书籍类型问题中同义，附加类别单位。

### row 153：incorrect
who sang oh annie i not your daddy?
标准：["Kid Creole and the Coconuts", "Kid Creole & The Coconuts"]
答案：Aretha Franklin
理由：逐题审阅最终答案与标准：Aretha Franklin / ["Kid Creole and the Coconuts", "Kid Creole & The Coconuts"]；实体、数值、时间或所問字段不一致，维持错误。

### row 155：incorrect
ben 10 ultimate alien episode 2 season 1?
标准：["Duped"]
答案：Ultimate Alien
理由：逐题审阅最终答案与标准：Ultimate Alien / ["Duped"]；实体、数值、时间或所問字段不一致，维持错误。

### row 157：incorrect
who played the music producer in pitch perfect 2?
标准：["Keegan-Michael Key"]
答案：Adam Levine
理由：逐题审阅最终答案与标准：Adam Levine / ["Keegan-Michael Key"]；实体、数值、时间或所問字段不一致，维持错误。

### row 158：incorrect
for complaints of sudden chest pain patients should take a?
标准：["Aspirin"]
答案：blood tests
理由：逐题审阅最终答案与标准：blood tests / ["Aspirin"]；实体、数值、时间或所問字段不一致，维持错误。

### row 159：incorrect
who sang last night on saturday night live?
标准：["Childish Gambino"]
答案：Katy Perry
理由：逐题审阅最终答案与标准：Katy Perry / ["Childish Gambino"]；实体、数值、时间或所問字段不一致，维持错误。

### row 160：equivalent
who want to be a millionaire calls his dad?
标准：["Carpenter"]
答案：John Carpenter
理由：John Carpenter与Carpenter在题目限定的百万富翁选手语境下指同一人。

### row 161：uncertain
who won the battle of britain in ww2?
标准：["Britain", "the United Kingdom", "British"]
答案：Royal Air Force
理由：Royal Air Force为参战军种，Britain为国家；相关但未按同一命名实体加分。

### row 162：equivalent
who has the talismans in sailor moon s?
标准：["Haruka and Michiru", "Haruka", "Michiru", "Sailor Pluto"]
答案：Haruka Tenoh
理由：Haruka Tenoh为标准Haruka同一角色完整名；标准已把Haruka作为可接受单项答案。

### row 164：incorrect
who wins the final fight in real steel?
标准：["Zeus"]
答案：Atom
理由：逐题审阅最终答案：Atom；标准：["Zeus"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 165：incorrect
who abolished the monarchy and declared france a republic?
标准：["Convention", "France's Legislative Assembly"]
答案：Georges Danton
理由：逐题审阅最终答案与标准：Georges Danton / ["Convention", "France's Legislative Assembly"]；实体、数值、时间或所問字段不一致，维持错误。

### row 166：uncertain
where does water come from in new york city?
标准：["The Catskill Aqueduct", "The Delaware Aqueduct", "The New Croton Aqueduct"]
答案：Catskill Mountains watershed
理由：Catskill Mountains watershed为水源区，标准为输水设施名称，相关但非同一对象。

### row 167：incorrect
who played ice queen in chronicles of narnia?
标准：["Tilda Swinton", "Laura Brent"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 172：equivalent
where was 2017 beauty and the beast filmed?
标准：["Surrey, United Kingdom"]
答案：Shepperton Studios
理由：轨迹明确拍摄在Shepperton Studios in Surrey, England；回答具体拍摄场地，与标准地点相容且更具体。

### row 175：incorrect
who negotiated an agreement with japan concerning the future of korea?
标准：["the Korean Empire", "Empire of Japan", "Taft", "Korean Empire"]
答案：Syngman Rhee
理由：逐题审阅最终答案与标准：Syngman Rhee / ["the Korean Empire", "Empire of Japan", "Taft", "Korean Empire"]；实体、数值、时间或所問字段不一致，维持错误。

### row 176：incorrect
when did indoor toilets become common in america?
标准：["After World War I"]
答案：1890
理由：逐题审阅最终答案：1890；标准：["After World War I"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 177：incorrect
who won an oscar for schindler's list?
标准：["Steven Zaillian", "Michael Kahn", "Steven Spielberg", "Janusz Kamiński", "John Williams", "Ewa Braun", "Gerald R. Molen", "Branko Lustig", "Allan Starski"]
答案：Liam Neeson
理由：逐题审阅最终答案：Liam Neeson；标准：["Steven Zaillian", "Michael Kahn", "Steven Spielberg", "Janusz Kamiński", "John Williams", "Ewa Braun", "Gerald R. Molen", "Branko Lustig", "Allan Starski"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 178：incorrect
who has won the most united states championships?
标准：["Lex Luger", "Ric Flair"]
答案：Pete Sampras
理由：逐题审阅最终答案：Pete Sampras；标准：["Lex Luger", "Ric Flair"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 181：incorrect
who was the winner of the first indianapolis 500?
标准：["Ray Harroun"]
答案：Louis Meyer
理由：逐题审阅最终答案与标准：Louis Meyer / ["Ray Harroun"]。实体、数值、时间或所问字段不一致，维持错误。

### row 182：incorrect
who played charles on when calls the heart?
标准：["Steve Bacic"]
答案：Daniel Lissing
理由：逐题审阅最终答案：Daniel Lissing；标准：["Steve Bacic"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 185：incorrect
book series about the end of the world?
标准：["Left Behind"]
答案：Endworld
理由：逐题审阅最终答案：Endworld；标准：["Left Behind"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 186：incorrect
when does star trek discovery air on tv?
标准：["September 19, 2017"]
答案：September 24, 2017
理由：逐题审阅最终答案：September 24, 2017；标准：["September 19, 2017"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 187：equivalent
how many quarterbacks have a receiving touchdown in the superbowl?
标准：["1"]
答案：one
理由：one与1是相同数量。

### row 188：uncertain
who used to present i'm a celebrity now?
标准：["Ant & Dec"]
答案：Vicky Pattison
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 193：incorrect
who owns the biggest house in beverly hills?
标准：["Anthony Pritzker"]
答案：Petra Stunt
理由：逐题审阅最终答案：Petra Stunt；标准：["Anthony Pritzker"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 194：incorrect
who has the most international goals of all time?
标准：["Ali Daei"]
答案：Josef Bican
理由：逐题审阅最终答案：Josef Bican；标准：["Ali Daei"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 197：incorrect
who is the head a in pretty little liars?
标准：["CeCe Drake"]
答案：I. Marlene King
理由：逐题审阅最终答案与标准：I. Marlene King / ["CeCe Drake"]；实体、数值、时间或所問字段不一致，维持错误。

### row 198：incorrect
who does the voice of little chef in ratatouille?
标准：["Ian Holm"]
答案：Lou Romano
理由：逐题审阅最终答案：Lou Romano；标准：["Ian Holm"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 199：incorrect
what are the 5 prohibitions of yom kippur?
标准：["No marital relations", "No wearing of leather shoes", "No eating and drinking", "No bathing or washing"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 201：equivalent
the first permanent european settlement on future united states soil was located where?
标准：["Jamestown", "St. Augustine", "Puerto Rico"]
答案：St. Augustine, Florida
理由：St. Augustine, Florida保留标准St. Augustine实体，并补充州名。

### row 202：uncertain
when did hollywood become the centre of the film industry?
标准：["1912", "By 1912"]
答案：1910s
理由：1910s仅提供覆盖1912的十年范围，未定位标准年份。

### row 204：incorrect
the length and direction of a straight line between two locations or positions?
标准：["displacement"]
答案：straight-line distance
理由：逐题审阅最终答案与标准：straight-line distance / ["displacement"]；实体、数值、时间或所問字段不一致，维持错误。

### row 205：incorrect
what is the first line of an http request to the server?
标准：["A request line", "the status line"]
答案：GET
理由：逐题审阅最终答案与标准：GET / ["A request line", "the status line"]；实体、数值、时间或所問字段不一致，维持错误。

### row 208：incorrect
a player that can shoot pass or dribble is considered to be?
标准：["Triple threat"]
答案：point guard
理由：逐题审阅最终答案与标准：point guard / ["Triple threat"]；实体、数值、时间或所問字段不一致，维持错误。

### row 211：uncertain
what level is a city and guilds qualification?
标准：["entry level to level 7"]
答案：level 2
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 212：uncertain
where is iodine found in the periodic table?
标准：["heaviest of the stable halogens"]
答案：group 17
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 214：uncertain
what is the job of justice of the peace?
标准：["dispense summary justice"]
答案：preside over cases
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 215：equivalent
where was held the first session of muslim league?
标准：["Dhaka, Bangladesh", "Lucknow"]
答案：Dhaka
理由：Dhaka与Dhaka, Bangladesh指同一城市，省略国家。

### row 217：incorrect
who sings what the world needs now in boss baby?
标准：["Missi Hale", "Steve Mazzaro", "Hans Zimmer"]
答案：Jackie DeShannon
理由：逐题审阅最终答案：Jackie DeShannon；标准：["Missi Hale", "Steve Mazzaro", "Hans Zimmer"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 218：incorrect
who played maudie in the movie el dorado?
标准：["Charlene Holt"]
答案：Michele Carey
理由：逐题审阅最终答案与标准：Michele Carey / ["Charlene Holt"]。实体、数值、时间或所问字段不一致，维持错误。

### row 221：incorrect
who is the best director in bollywood 2017?
标准：["Nitesh Tiwari"]
答案：Ashwiny Iyer Tiwari
理由：逐题审阅最终答案与标准：Ashwiny Iyer Tiwari / ["Nitesh Tiwari"]；实体、数值、时间或所問字段不一致，维持错误。

### row 223：incorrect
when was the cleveland browns last winning game?
标准：["2016"]
答案：2018
理由：逐题审阅最终答案与标准：2018 / ["2016"]；实体、数值、时间或所問字段不一致，维持错误。

### row 224：incorrect
who is in charge of new issues not mentioned in the constitution?
标准：["Congress"]
答案：judiciary
理由：逐题审阅最终答案与标准：judiciary / ["Congress"]；实体、数值、时间或所問字段不一致，维持错误。

### row 225：uncertain
what color is the golden gate bridge in san francisco?
标准：["orange vermilion called international orange", "red", "International Orange"]
答案：orange
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 227：uncertain
when was the peak to peak gondola built?
标准：["in 2007 and 2008"]
答案：2007
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 229：equivalent
what us president is the only president to become an eagle scout?
标准：["Ford"]
答案：Gerald Ford
理由：Gerald Ford与Ford指同一总统。

### row 234：equivalent
why the hole in the ozone layer over antarctica?
标准：["bromine", "chlorine", "methyl bromide", "CFCs", "halons"]
答案：chlorofluorocarbons
理由：chlorofluorocarbons是CFCs的完整名称。

### row 235：incorrect
when did david akers kick the 63 yard field goal?
标准：["September 9, 2012"]
答案：November 27, 2011
理由：逐题审阅最终答案与标准：November 27, 2011 / ["September 9, 2012"]；实体、数值、时间或所問字段不一致，维持错误。

### row 236：equivalent
the secret of crickley hall how many episodes?
标准：["3"]
答案：three
理由：three与3是相同数量。

### row 239：incorrect
which president of the united states was a boy scout?
标准：["Gerald Ford", "President Gerald Ford"]
答案：William Howard Taft
理由：逐题审阅最终答案与标准：William Howard Taft / ["Gerald Ford", "President Gerald Ford"]。实体、数值、时间或所问字段不一致，维持错误。

### row 241：incorrect
what is the most common blood type in sweden?
标准：["A+", "AB+"]
答案：O
理由：逐题审阅最终答案：O；标准：["A+", "AB+"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 242：uncertain
when did the first battle of ypres end?
标准：["22 November 1914"]
答案：mid-November 1914
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 243：label_issue
what is the term of an official in the house of representatives?
标准：["two-year", "Speaker of the House", "Two years", "Representatives"]
答案：Speaker of the United States House of Representatives
理由：标准把任期two years与Speaker of the House职位混在允许集合；回答职位未答任期，单列标签类型问题不加分。

### row 244：uncertain
when did the tradition of self government began in america?
标准：["1783"]
答案：18th century
理由：18th century仅覆盖1783，未定位标准年份。

### row 245：incorrect
who is emma dating in once upon a time?
标准：["Hook"]
答案：Christopher Gorham
理由：逐题审阅最终答案：Christopher Gorham；标准：["Hook"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 246：equivalent
who cracked the enigma code in world war 2?
标准：["Turing"]
答案：Alan Turing
理由：Alan Turing与Turing指同一密码学家。

### row 247：incorrect
what is the name of the muslim dress?
标准：["hijab"]
答案：abaya
理由：逐题审阅最终答案与标准：abaya / ["hijab"]；实体、数值、时间或所問字段不一致，维持错误。

### row 249：incorrect
who wrote the first declaration of human rights?
标准：["Cyrus"]
答案：John Peters Humphrey
理由：逐题审阅最终答案：John Peters Humphrey；标准：["Cyrus"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 250：incorrect
who is currently serving as president of the senate?
标准：["Orrin Hatch", "Patrick Leahy"]
答案：Mike Pence
理由：逐题审阅最终答案与标准：Mike Pence / ["Orrin Hatch", "Patrick Leahy"]。实体、数值、时间或所问字段不一致，维持错误。

### row 251：uncertain
when did michael jordan return to the nba?
标准：["2001", "1995", "March 1995", "in March 1995"]
答案：summer of 2001
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 255：incorrect
when did teenage mutant ninja turtles come out?
标准：["1984"]
答案：1990
理由：逐题审阅最终答案与标准：1990 / ["1984"]；实体、数值、时间或所問字段不一致，维持错误。

### row 256：equivalent
what was the emperor name in star wars?
标准：["Darth Sidious", "Sheev Palpatine"]
答案：Emperor Palpatine
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 258：incorrect
number of degree of freedom for plane mechanism?
标准：["six", "two"]
答案：3
理由：逐题审阅最终答案与标准：3 / ["six", "two"]；实体、数值、时间或所問字段不一致，维持错误。

### row 259：equivalent
where is the oldest civilization known to man?
标准：["Mesopotamia"]
答案：southern Mesopotamia
理由：southern Mesopotamia为标准Mesopotamia的具体地区限定，地点指代不冲突。

### row 261：incorrect
name three large lakes other than the great lakes in the united states?
标准：["Iliamna Lake", "Great Salt Lake", "Lake of the Woods"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 270：incorrect
who sings so come and dance with me jai ho?
标准：["Mahalaxmi Iyer", "Vijay Prakash", "Tanvi Shah", "Sukhvinder Singh"]
答案：The Pussycat Dolls
理由：逐题审阅最终答案：The Pussycat Dolls；标准：["Mahalaxmi Iyer", "Vijay Prakash", "Tanvi Shah", "Sukhvinder Singh"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 273：incorrect
where does half life 2 episode 2 take place?
标准：["outside City 17"]
答案：City 17
理由：逐题审阅最终答案：City 17；标准：["outside City 17"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 276：uncertain
what is the first step in the evolution of the eye?
标准：["photoreceptor proteins that sense light", "eyespots"]
答案：simple light detection
理由：simple light detection只给功能，未给所问演化初期的eyespots/photoreceptor结构。

### row 277：uncertain
when did john hart play the lone ranger?
标准：["from 1952 until 1953"]
答案：1952
理由：1952未完整回答1952 until 1953的时间段。

### row 278：uncertain
tools made from high-speed tool steel are generally used for what type of machining operations?
标准：["milling"]
答案：cutting operations
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 279：incorrect
when does season 3 of the riveras start?
标准：["March 11, 2018"]
答案：October 10, 2018
理由：逐题审阅最终答案与标准：October 10, 2018 / ["March 11, 2018"]；实体、数值、时间或所問字段不一致，维持错误。

### row 282：incorrect
who lived in jamestown before the arrival of the english?
标准：["uninhabited"]
答案：Virginia Algonquians
理由：逐题审阅最终答案：Virginia Algonquians；标准：["uninhabited"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 283：incorrect
nearest metro station to gandhi nagar in delhi?
标准：["Shastri Park metro station"]
答案：Adarsh Nagar metro station
理由：逐题审阅最终答案与标准：Adarsh Nagar metro station / ["Shastri Park metro station"]。实体、数值、时间或所问字段不一致，维持错误。

### row 285：incorrect
when do new episodes of ncis los angeles return?
标准：["May 13, 2018", "October 1, 2017"]
答案：September 30, 2018
理由：逐题审阅最终答案：September 30, 2018；标准：["May 13, 2018", "October 1, 2017"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 287：equivalent
who said if a tree falls in the woods and nobody hears it?
标准：["Philosopher George Berkeley", "Charles Riborg Mann", "George Ransom Twiss"]
答案：George Berkeley
理由：George Berkeley与Philosopher George Berkeley仅职业修饰语不同。

### row 291：equivalent
who got the first nobel prize in physics?
标准：["Wilhelm Conrad Röntgen"]
答案：Wilhelm Röntgen
理由：Wilhelm Röntgen与Wilhelm Conrad Röntgen是同一人，省略中间名。

### row 298：uncertain
which central american nations border the pacific ocean and the caribbean sea?
标准：["Nicaragua", "Costa Rica"]
答案：Panama
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 299：incorrect
where did the name huey helicopter come from?
标准：["originally designated HU-1"]
答案：Gustave Ponton d'Amécourt
理由：逐题审阅最终答案与标准：Gustave Ponton d'Amécourt / ["originally designated HU-1"]；实体、数值、时间或所問字段不一致，维持错误。

### row 303：incorrect
when did the democratic party change its name?
标准：["the 1830s"]
答案：1844
理由：逐题审阅最终答案：1844；标准：["the 1830s"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 304：incorrect
who used morse code in world war 2?
标准：["naval bases", "warships"]
答案：Nazi German Wehrmacht
理由：逐题审阅最终答案与标准：Nazi German Wehrmacht / ["naval bases", "warships"]；实体、数值、时间或所問字段不一致，维持错误。

### row 305：incorrect
who shot first in the shot heard around the world?
标准：["Americans acting under orders"]
答案：British soldiers
理由：逐题审阅最终答案与标准：British soldiers / ["Americans acting under orders"]；实体、数值、时间或所問字段不一致，维持错误。

### row 306：incorrect
where did the ashes from ash wednesday originate?
标准：["Pope Gregory I the Great"]
答案：palm leaves
理由：逐题审阅最终答案与标准：palm leaves / ["Pope Gregory I the Great"]；实体、数值、时间或所問字段不一致，维持错误。

### row 307：uncertain
who wrote the song i hate you i love you?
标准：["Garrett Nash", "Olivia O'Brien", "Angel Benitez"]
答案：Gnash
理由：轨迹称Gnash演唱该歌，但此轨迹未给其本名Garrett Nash；需别名直接证据后再加分。

### row 308：incorrect
who has said that caste is a closed class?
标准：["Frederik Barth"]
答案：B. R. Ambedkar
理由：逐题审阅最终答案：B. R. Ambedkar；标准：["Frederik Barth"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 309：incorrect
when was zero first used in mathematical operations?
标准：["By 1770 BC", "7th century"]
答案：598–668
理由：逐题审阅最终答案与标准：598–668 / ["By 1770 BC", "7th century"]；实体、数值、时间或所問字段不一致，维持错误。

### row 311：incorrect
who plays matthew on anne with an e?
标准：["R. H. Thomson"]
答案：Martin Sheen
理由：逐题审阅最终答案：Martin Sheen；标准：["R. H. Thomson"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 312：uncertain
who sings far from the home i love in fiddler on the roof?
标准：["Hodel"]
答案：Michele Marsh
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 314：incorrect
who played the detective in little boy blue?
标准：["Stephen Graham"]
答案：Brían F. O'Byrne
理由：逐题审阅最终答案与标准：Brían F. O'Byrne / ["Stephen Graham"]；实体、数值、时间或所問字段不一致，维持错误。

### row 316：incorrect
when did virgin australia (formerly virgin blue) commence flying in australia?
标准：["November 1999"]
答案：August 2000
理由：逐题审阅最终答案：August 2000；标准：["November 1999"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 317：incorrect
who played the jewish man in coming to america?
标准：["Eddie Murphy"]
答案：John Amos
理由：逐题审阅最终答案：John Amos；标准：["Eddie Murphy"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 318：incorrect
who presides over the highest criminal court in a district?
标准：["District Judge"]
答案：Chief Judge
理由：逐题审阅最终答案与标准：Chief Judge / ["District Judge"]；实体、数值、时间或所問字段不一致，维持错误。

### row 319：incorrect
legislation regarding data protection and security in uk?
标准：["The Data Protection Act 1998", "Data Protection Act 1998"]
答案：Data Protection Act 2018
理由：逐题审阅最终答案：Data Protection Act 2018；标准：["The Data Protection Act 1998", "Data Protection Act 1998"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 320：incorrect
when did the first immigrants come to hawaii?
标准：["Around 1200"]
答案：124
理由：逐题审阅最终答案与标准：124 / ["Around 1200"]；实体、数值、时间或所問字段不一致，维持错误。

### row 326：incorrect
what is the salary of the ceo of microsoft?
标准：["$84.3 million", "$84.3 million (2018)"]
答案：$18 million
理由：逐题审阅最终答案：$18 million；标准：["$84.3 million", "$84.3 million (2018)"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 328：incorrect
how long has tom brady been the patriots quarterback?
标准：["2001", "16 seasons"]
答案：18 seasons
理由：逐题审阅最终答案：18 seasons；标准：["2001", "16 seasons"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 329：uncertain
architectural elements forming rib vaults eg wells cathedral?
标准：["an armature of piped masonry", "barrel vaults", "two to three barrel vaults"]
答案：lierne ribs
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 331：incorrect
when was the last easter fell on april 1?
标准：["2018"]
答案：2011
理由：逐题审阅最终答案：2011；标准：["2018"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 332：incorrect
south african tree with thorns on the trunk?
标准：["silk floss tree"]
答案：Ziziphus mucronata
理由：逐题审阅最终答案与标准：Ziziphus mucronata / ["silk floss tree"]。实体、数值、时间或所问字段不一致，维持错误。

### row 335：incorrect
Are Leopold Lummerstorfer and Valeria Sarmiento both authors?
标准：["no"]
答案：yes
理由：逐题审阅最终答案与标准：yes / ["no"]；实体、数值、时间或所問字段不一致，维持错误。

### row 337：incorrect
The Missouri attorney general election of 2012 ended in a loss for which attorney and CNN contributor?
标准：["Edward Robert Martin Jr."]
答案：Chris Koster
理由：逐题审阅最终答案：Chris Koster；标准：["Edward Robert Martin Jr."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 338：incorrect
Who was the film which was Kim Dae-woo's directing debut about ?
标准：["a scholar"]
答案：Forbidden Quest
理由：逐题审阅最终答案：Forbidden Quest；标准：["a scholar"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 339：equivalent
Which astronaut, Jean-François Clervoy or Ulrich Walter, was born first?
标准：["Prof. Dr. Ulrich Hans Walter"]
答案：Ulrich Walter
理由：Ulrich Walter与Prof. Dr. Ulrich Hans Walter同一宇航员，省略头衔及中间名。

### row 341：incorrect
What vocalist and pianist was recorded by Modular Recordings?
标准：["Karen O"]
答案：Ben Lee
理由：逐题审阅最终答案：Ben Lee；标准：["Karen O"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 343：incorrect
What is the colloquial name of the professional football team in which striker Frederico Chaves Guedos played?
标准：["Rooster"]
答案：Raposa
理由：逐题审阅最终答案与标准：Raposa / ["Rooster"]；实体、数值、时间或所問字段不一致，维持错误。

### row 344：incorrect
Who wrote the book that inspired the name of the CD/DVD "Here at the End of All Things"?
标准：["J. R. R. Tolkien"]
答案：Stephen King
理由：逐题审阅最终答案与标准：Stephen King / ["J. R. R. Tolkien"]；实体、数值、时间或所問字段不一致，维持错误。

### row 345：incorrect
What park is just south of the location where the New York Jets played prior to moving to Shea Stadium?
标准：["Central Park"]
答案：Citi Field
理由：逐题审阅最终答案与标准：Citi Field / ["Central Park"]；实体、数值、时间或所問字段不一致，维持错误。

### row 346：equivalent
What was the birth name of the ex-slave abolitionist featured in the art installation The Dinner Party?
标准：["Isabella (Belle) Baumfree"]
答案：Isabella Baumfree
理由：Isabella Baumfree与Isabella (Belle) Baumfree同一出生名，括号昵称可省略。

### row 347：incorrect
William Novac co-wrote the memoir of what American retired professional basketball player who is current president of basketball operations for the Los Angeles Lakers?
标准：["Earvin \"Magic\" Johnson Jr."]
答案：Mitch Kupchak
理由：逐题审阅最终答案与标准：Mitch Kupchak / ["Earvin \"Magic\" Johnson Jr."]；实体、数值、时间或所問字段不一致，维持错误。

### row 348：label_issue
How old was William DuVall when Black Gives Way to Blue was certified gold by the RIAA?
标准：["William Bradley DuVall (born September 6, 1967)"]
答案：79
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 349：incorrect
Which movie produced by Esta Malka Charkham was the first to star a woman as the lead role?
标准：["Supergirl"]
答案：Shall We Gather at the River
理由：逐题审阅最终答案：Shall We Gather at the River；标准：["Supergirl"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 351：equivalent
The current coach of the Los Angeles Clippers was signed as a free agent to the San Antonio Spurs during what season?
标准：["1994–95 NBA season"]
答案：1994–95
理由：1994–95与1994–95 NBA season同一赛季，省略题目已限定的赛季类别。

### row 352：incorrect
Where does the train that runs from NYC and Miami station at in Florida?
标准：["Jacksonville station"]
答案：Miami
理由：逐题审阅最终答案：Miami；标准：["Jacksonville station"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 353：uncertain
Ali Eren Balıkel started a restaurant which hosted a number of famous figures including an English actor who won three consecutive what?
标准：["BAFTA Awards for Best Actress"]
答案：BAFTA Film Award
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 355：incorrect
Who was the secretary to the Winter Queen?
标准：["Sir Francis Nethersole"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 362：incorrect
James Stuart became a specialist of a rhythmic pattern charecterised by what?
标准：["characterised by a moderately fast to very fast tempo"]
答案：shuffle
理由：逐题审阅最终答案与标准：shuffle / ["characterised by a moderately fast to very fast tempo"]；实体、数值、时间或所問字段不一致，维持错误。

### row 363：equivalent
Cave-In-Rock, Illinois was a stronghold for serial killer/bandit brothers who operated in which century?
标准：["who operated in Tennessee, Kentucky, Illinois, and Mississippi, in the late eighteenth century."]
答案：18th century
理由：题目只问century，18th century完整提取长标准late eighteenth century中的世纪。

### row 364：incorrect
Dan Scalco is best known as a contributing author for a magazine owned by who?
标准：["Peter Shea"]
答案：Morningstar
理由：逐题审阅最终答案：Morningstar；标准：["Peter Shea"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 365：incorrect
Angelo Francesco Lavignino scored a 1965 English-language Spanish-Swiss co-produced film that was directed by and also starred who?
标准：["Orson Welles"]
答案：Giorgio Simonelli
理由：逐题审阅最终答案与标准：Giorgio Simonelli / ["Orson Welles"]；实体、数值、时间或所問字段不一致，维持错误。

### row 366：incorrect
Jacques Sernas, actor in Fugitive in Trieste, was of what nationality?
标准：["Lithuanian-born French"]
答案：Lithuanian
理由：逐题审阅最终答案与标准：Lithuanian / ["Lithuanian-born French"]；实体、数值、时间或所問字段不一致，维持错误。

### row 367：uncertain
Which ground force of the Austro-Hungarian Dual Monarchy did Jan Romer joined?
标准：["The Austro-Hungarian Army"]
答案：Common Army
理由：Common Army是Austro-Hungarian Army的具体组成部分，先不把上下级军制直接判等价。

### row 369：incorrect
What year was the essay which Henry Louis Gates and Cornel West criticized in their book, "The Future of the Race" first published?
标准：["1903"]
答案：1994
理由：逐题审阅最终答案：1994；标准：["1903"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 370：equivalent
The languages Hussein Ali Mahfouz studied are spoken by how many people?
标准：["more than 330 million people"]
答案：more than 330 million
理由：more than 330 million与more than 330 million people同一数量下界，单位由题目限定。

### row 371：incorrect
What is common between Matt Vasgersian and Michael Casey?
标准：["American"]
答案：sports
理由：逐题审阅最终答案与标准：sports / ["American"]；实体、数值、时间或所問字段不一致，维持错误。

### row 372：equivalent
Is Ashland, New Hampshire or Plymouth Regional High School located near the Scribner-Fellows State Forest?
标准：["Ashland is home to Scribner-Fellows State Forest"]
答案：Ashland, New Hampshire
理由：题目让二选一，Ashland, New Hampshire与标准描述Ashland is home to...同一选项。

### row 373：equivalent
Who was born first, Jorge Amado or James Leo Herlihy?
标准：["Jorge Leal Amado de Faria"]
答案：Jorge Amado
理由：Jorge Amado与Jorge Leal Amado de Faria同一作家的常用名和全名。

### row 375：incorrect
What man with a lazy left eye starred in Sacred Ground?
标准：["Jack Elam"]
答案：Tim McIntire
理由：逐题审阅最终答案：Tim McIntire；标准：["Jack Elam"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 376：uncertain
What languages did the son of Sacagawea speak?
标准：["French and English"]
答案：French
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 379：equivalent
What Kenya-based company owns the Tusker beer brand?
标准：["East African Breweries Limited"]
答案：East African Breweries
理由：East African Breweries与East African Breweries Limited同一公司，省略法律后缀。

### row 380：incorrect
Not About Angels was used in the film adaptation of what novel by John Green?
标准：["The Fault in Our Stars"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 381：equivalent
What sport do Straight Blast Gym - Ireland and John Kavanagh have in common?
标准：["martial arts"]
答案：mixed martial arts
理由：mixed martial arts明确回答同一题目中的martial arts运动，并给出更具体类别。

### row 382：incorrect
What film did the sound editor for a 2013 Hong Kong-Chinese martial arts drama film based on the life story of the Wing Chun grandmaster Ip Man win two Academy Awards for?
标准：["\"Hacksaw Ridge\""]
答案：The Hunt for Red October
理由：逐题审阅最终答案与标准：The Hunt for Red October / ["\"Hacksaw Ridge\""]；实体、数值、时间或所問字段不一致，维持错误。

### row 384：equivalent
What Deepdale area football club did Andy Pilling play for?
标准：["Preston North End"]
答案：Preston North End F.C.
理由：Preston North End F.C.与Preston North End同一足球俱乐部，附加后缀。

### row 385：label_issue
Were Maurice Tourneur and Greg Mottola both American film directors?
标准：["French film director"]
答案：no
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 386：incorrect
What is the birthday of the Earl of Merioneth?
标准：["10 June 1921"]
答案：28 October 1980
理由：逐题审阅最终答案与标准：28 October 1980 / ["10 June 1921"]；实体、数值、时间或所問字段不一致，维持错误。

### row 388：incorrect
From 2003 to 2008 Tom Holland was responsible for what  ?
标准：["for crafting and voting on legislation"]
答案：Spider-Man
理由：逐题审阅最终答案：Spider-Man；标准：["for crafting and voting on legislation"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 391：incorrect
What profession did Alan Crosland and Kurt Voss both hold?
标准：["film director"]
答案：veterinarian
理由：逐题审阅最终答案与标准：veterinarian / ["film director"]；实体、数值、时间或所問字段不一致，维持错误。

### row 392：incorrect
Which town was home to a forward for the Western New York Flash?
标准：["Oyster Bay"]
答案：Elma
理由：逐题审阅最终答案：Elma；标准：["Oyster Bay"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 393：equivalent
Which team based in South Wales participated in a final game of 1980 Welsh Cup Final?
标准：["Newport County"]
答案：Newport County A.F.C.
理由：Newport County A.F.C.与Newport County同一足球俱乐部，附加后缀。

### row 394：incorrect
What man, born in 1963, was instrumental in bringing the Boston Red Sox to the stadium City of Palms Park in Fort Myers, Florida?
标准：["Mike Greenwell"]
答案：Jason Hochberg
理由：逐题审阅最终答案与标准：Jason Hochberg / ["Mike Greenwell"]；实体、数值、时间或所問字段不一致，维持错误。

### row 395：equivalent
Which musician's band contains more letters in it's name, Micky Dolenz or Jesse James Dupree?
标准：["George Michael Dolenz"]
答案：Micky Dolenz
理由：Micky Dolenz与George Michael Dolenz同一音乐人的常用名和出生名。

### row 396：uncertain
Tui Flower and Julia child were both known for what?
标准：["Cooking"]
答案：food writing
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 397：uncertain
What are some foods that may have been served at the Hawaiin Cottage?
标准：["poi, Kalua pig, poke, lomi salmon, opihi, haupia"]
答案：laulau
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 400：incorrect
Which band, Letters to Cleo or Screaming Trees, had more members?
标准：["Letters to Cleo"]
答案：Screaming Trees
理由：逐题审阅最终答案：Screaming Trees；标准：["Letters to Cleo"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 401：incorrect
What surrounding river in a Canadian province was Erin Wall born near?
标准：["Bow River"]
答案：South Saskatchewan River
理由：逐题审阅最终答案与标准：South Saskatchewan River / ["Bow River"]；实体、数值、时间或所問字段不一致，维持错误。

### row 402：incorrect
Who was this American Founding Father, a proponent of democracy, republicanism, and individual rights, examined Ice Age fossils of Kentucky's Big Bone Lick?
标准：["Thomas Jefferson"]
答案：Benjamin Franklin
理由：逐题审阅最终答案与标准：Benjamin Franklin / ["Thomas Jefferson"]；实体、数值、时间或所問字段不一致，维持错误。

### row 403：equivalent
What was Thomas Boutflower Bennet's role at The Collegiate School of St Peter?
标准：["schoolmaster at J. L. Young's Adelaide Educational Institution and at Saint Peter's College."]
答案：schoolmaster
理由：schoolmaster直接提取标准长描述中的岗位，地点及另一个学校不是所问岗位必需字段。

### row 404：incorrect
Nikhil Nanda is the son of the insurance advisor in what business?
标准：["life insurance"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 406：label_issue
Which director, Chris O'Dea or Lucky McKee,  is a Master of Fine Arts graduate of the UCLA School of Theater, Film and Television?
标准：["Edward Lucky McKee"]
答案：Chris O'Dea
理由：轨迹支持Chris O'Dea为UCLA MFA毕业生，与金标准Lucky McKee冲突；标签疑误单列。

### row 407：incorrect
Who designed the hotel that held the IFBB professional bodybuilding competition in September 1991?
标准：["architect Michael Graves"]
答案：Henry Janeway Hardenbergh
理由：逐题审阅最终答案与标准：Henry Janeway Hardenbergh / ["architect Michael Graves"]；实体、数值、时间或所問字段不一致，维持错误。

### row 410：uncertain
What athletic team has its football and basketball games broadcast on KFST and has a mascot who is named Bevo?
标准：["Texas Longhorns"]
答案：University of Texas at Austin
理由：University of Texas at Austin为大学，标准Texas Longhorns为校运动队，相关机构不直接互换。

### row 412：incorrect
Which characters are akin to goblins and were added to a Tilted Mill Entertainment video game in 2009?
标准：["Orc characters"]
答案：Goblin Explosioneers
理由：逐题审阅最终答案与标准：Goblin Explosioneers / ["Orc characters"]；实体、数值、时间或所問字段不一致，维持错误。

### row 414：incorrect
what species of plants are Chamelaucium and Vanilla derived from?
标准：["flowers"]
答案：Myrtaceae
理由：逐题审阅最终答案与标准：Myrtaceae / ["flowers"]；实体、数值、时间或所問字段不一致，维持错误。

### row 417：uncertain
Illmatic, the debut studio album by Nas which featured the song "N.Y. State of Mind", was released on what date by which record label?
标准：["April 19, 1994, by Columbia Records"]
答案：April 19, 1994
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 418：incorrect
An American who is a German literature translator and did a thesis on an Austrian prodigy born in 1874 taught at which university?
标准：["University of Vienna"]
答案：New York University
理由：逐题审阅最终答案与标准：New York University / ["University of Vienna"]。实体、数值、时间或所问字段不一致，维持错误。

### row 419：incorrect
What is the name of one the ex-security officials that means The Institute?
标准：["Mossad"]
答案：Oldřich Černý
理由：逐题审阅最终答案与标准：Oldřich Černý / ["Mossad"]；实体、数值、时间或所問字段不一致，维持错误。

### row 420：incorrect
How many albums have been released by the same band that released the "Trance" EP?
标准：["4 albums"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 421：incorrect
After partially sinking in 1994, Celestyal Crystal was rebuilt for the purpose of what Bermudian company?
标准：["Norwegian Cruise Line Holdings Ltd."]
答案：Celestyal Cruises
理由：逐题审阅最终答案：Celestyal Cruises；标准：["Norwegian Cruise Line Holdings Ltd."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 422：incorrect
Radio shack made a line of computers in the 1980's which was marketed as the TRS-80 Color Computer or the Interact Home Computer?
标准：["TRS-80 Color Computer"]
答案：TRS-80 Micro Computer System
理由：逐题审阅最终答案与标准：TRS-80 Micro Computer System / ["TRS-80 Color Computer"]；实体、数值、时间或所問字段不一致，维持错误。

### row 424：equivalent
Kasper Peter Schmeichel is the son of a professional footballer who was voted what in 1992 and 1993?
标准：["IFFHS World's Best Goalkeeper"]
答案：World's Best Goalkeeper
理由：World's Best Goalkeeper与IFFHS World's Best Goalkeeper在1992/1993奖项语境下同一荣誉。

### row 426：equivalent
Was Kanako Momota or Mark Hollis born first?
标准：["Mark David Hollis"]
答案：Mark Hollis
理由：Mark Hollis与Mark David Hollis同一人，省略中间名。

### row 428：incorrect
The team that would become the Little Giants was located in the county seat of which Ohio county?
标准：["Mahoning County"]
答案：Lorain County
理由：逐题审阅最终答案与标准：Lorain County / ["Mahoning County"]；实体、数值、时间或所問字段不一致，维持错误。

### row 429：incorrect
Thor Equities owns properties in Soho, which became known for what type of rental properties?
标准：["artists' lofts"]
答案：retail
理由：逐题审阅最终答案与标准：retail / ["artists' lofts"]；实体、数值、时间或所問字段不一致，维持错误。

### row 430：equivalent
The 1948 Commonwealth Prime Ministers' Conference was hosted by the Prime Minister from what British party?
标准：["Labour"]
答案：Labour Party
理由：Labour Party与Labour同一政党。

### row 433：incorrect
Psycho-physical Awareness was developed into an original and dependable method by a Russian-American actor who was referred to by Konstantin Stanislavski as what?
标准：["his most brilliant student"]
答案：the actor in the future
理由：逐题审阅最终答案与标准：the actor in the future / ["his most brilliant student"]；实体、数值、时间或所問字段不一致，维持错误。

### row 436：equivalent
What season of the Indian reality TV series "Big Boss" did the model Lopamundra Raut compete in?
标准：["the tenth season"]
答案：Bigg Boss 10
理由：Bigg Boss 10与the tenth season同一节目季数。

### row 437：uncertain
Criss Angel generated $150 million in tourist revenue for his live performance show in what city?
标准：["Paradise, Nevada"]
答案：Las Vegas
理由：Las Vegas与Paradise, Nevada存在都会区及行政城界差异，保留地理精度争议。

### row 438：uncertain
What career titles do Ed Wood and Fernand Rivers share?
标准：["actor, writer, producer, and director"]
答案：film director
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 439：uncertain
What is the pioneer who has a park dedicated to him near Lexington, North Carolina famous for?
标准：["Wilderness Road"]
答案：exploration and settlement of what is now Kentucky
理由：exploration and settlement of Kentucky为人物事业描述，未直接给标准Wilderness Road事迹。

### row 440：incorrect
The Gate is a song from the album scheduled for release in what month?
标准：["November 2017"]
答案：September
理由：逐题审阅最终答案与标准：September / ["November 2017"]。实体、数值、时间或所问字段不一致，维持错误。

### row 441：incorrect
Who developed the jet fighters operated by the 41st Tactical Squadron of the Polish Air Force?
标准：["the Mikoyan design bureau"]
答案：General Dynamics
理由：逐题审阅最终答案：General Dynamics；标准：["the Mikoyan design bureau"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 442：incorrect
The Porsche 968 was the last in a line of front-engined sports cars following the 944 and which earlier model?
标准：["924"]
答案：944
理由：逐题审阅最终答案与标准：944 / ["924"]；实体、数值、时间或所問字段不一致，维持错误。

### row 443：incorrect
In what country did Gildo Siopaes win a bronze medal for bobsledding in the 1964 Winter Olympics?
标准：["Austria"]
答案：Italy
理由：逐题审阅最终答案与标准：Italy / ["Austria"]；实体、数值、时间或所問字段不一致，维持错误。

### row 444：incorrect
The subject of the biography "Name Dropper" was born in what year?
标准：["1961"]
答案：1922
理由：逐题审阅最终答案与标准：1922 / ["1961"]；实体、数值、时间或所問字段不一致，维持错误。

### row 448：incorrect
Which plant genus is part of a family with a longer name, Morning glory or Rothmannia?
标准：["Morning glory"]
答案：Rothmannia
理由：逐题审阅最终答案与标准：Rothmannia / ["Morning glory"]。实体、数值、时间或所问字段不一致，维持错误。

### row 449：uncertain
What band did both Delores Holmes and an inductee to the Rock and Roll Hall of Fame sing in?
标准：["E Street Band"]
答案：Bruce Springsteen Band
理由：Bruce Springsteen Band与E Street Band并非可直接假定同一时期同一乐队。

### row 451：equivalent
Bridge of Spies stars a Soviet intelligence officer with what name?
标准：["Rudolf Abel"]
答案：Vilyam Genrikhovich Fisher
理由：Vilyam Genrikhovich Fisher与Rudolf Abel为同一人的本名和化名，ckpt80轨迹明确Fisher/Abel身份。

### row 453：incorrect
How many albums had been recorded by Talking Heads by November, 1980?
标准：["four"]
答案：three
理由：逐题审阅最终答案与标准：three / ["four"]；实体、数值、时间或所問字段不一致，维持错误。

### row 454：incorrect
In what year did the American Record company established in 1958 release a record co-produced by Adam Faith?
标准：["January 1974"]
答案：1958
理由：逐题审阅最终答案：1958；标准：["January 1974"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 456：incorrect
What is Diego Tonetto's Italian passport called?
标准：["Italian nationality law"]
答案：Italian passport
理由：逐题审阅最终答案与标准：Italian passport / ["Italian nationality law"]；实体、数值、时间或所問字段不一致，维持错误。

### row 457：incorrect
What year was Playford B Power Station permanently closed in by its Australian operator?
标准：["2015"]
答案：2016
理由：逐题审阅最终答案：2016；标准：["2015"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 459：incorrect
Wheelock Whitney is just one member of the Whitney Family. Where did this American family originate from?
标准：["London, England"]
答案：Massachusetts
理由：逐题审阅最终答案：Massachusetts；标准：["London, England"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 460：incorrect
What city did the musician whose debut album shares its title with the 1959 Alfred Hitchcock hail from?
标准：["Chicago, IL"]
答案：Los Angeles
理由：逐题审阅最终答案与标准：Los Angeles / ["Chicago, IL"]；实体、数值、时间或所問字段不一致，维持错误。

### row 461：incorrect
Which star in the Maltese Bippy died in 1987?
标准：["Dan Rowan"]
答案：Charles Thake
理由：逐题审阅最终答案与标准：Charles Thake / ["Dan Rowan"]；实体、数值、时间或所問字段不一致，维持错误。

### row 462：equivalent
What country of origin does Eric Lucassen and Party for Freedom have in common?
标准：["Dutch"]
答案：Netherlands
理由：Netherlands与Dutch在country of origin字段指同一国家。

### row 467：incorrect
The historical Nimavar school in the Nimavar Bazaar, or bazar, is located in which country?
标准：["Iran"]
答案：India
理由：逐题审阅最终答案与标准：India / ["Iran"]；实体、数值、时间或所問字段不一致，维持错误。

### row 469：incorrect
Who was the brother of the wife of the Democratic Party nomination for Vice President in 1972?
标准：["President John F. Kennedy"]
答案：Theodore Mondale
理由：逐题审阅最终答案与标准：Theodore Mondale / ["President John F. Kennedy"]；实体、数值、时间或所問字段不一致，维持错误。

### row 470：incorrect
What is the name of  rocker, who was awarded "Rock Goddess of the Year" in the Annual Loudwide Music Awards, who sang with high pitched screams in her band's albums?
标准：["Maria Brink"]
答案：Jody Turner
理由：逐题审阅最终答案与标准：Jody Turner / ["Maria Brink"]；实体、数值、时间或所問字段不一致，维持错误。

### row 474：equivalent
Who was born first Al-Karaji or Masatoshi Gündüz Ikeda?
标准：["Abū Bakr ibn Muḥammad ibn al Ḥusayn al-Karajī"]
答案：Al-Karaji
理由：Al-Karaji与标准长阿拉伯人名指同一数学家。

### row 477：uncertain
What were the nations after 1722 that composed a culture that was extensively studied by William N. Fenton?
标准：["Mohawk, Onondaga, Oneida, Cayuga, Seneca, and Tuscarora"]
答案：Mohawk
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 479：incorrect
In what year was the football club for which Reuven Niemeijer plays founded?
标准：["1903"]
答案：1900
理由：逐题审阅最终答案：1900；标准：["1903"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 481：uncertain
Where is the company that owns thanKing Horse pub restaurant chain based ?
标准：["Bury St Edmunds,"]
答案：United Kingdom
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 482：incorrect
Where is the University Joe Odom played football for located?
标准：["West Lafayette, Indiana"]
答案：Louisiana
理由：逐题审阅最终答案与标准：Louisiana / ["West Lafayette, Indiana"]；实体、数值、时间或所問字段不一致，维持错误。

### row 483：incorrect
In the animal kingdom what type of sexuality is described as sexual behavior toward both male and females?
标准：["bisexual"]
答案：homosexual sexual behavior
理由：逐题审阅最终答案与标准：homosexual sexual behavior / ["bisexual"]；实体、数值、时间或所問字段不一致，维持错误。

### row 489：uncertain
Where did the tribe Mato-tope chief over reside?
标准：["North Dakota"]
答案：Mitutanka
理由：Mitutanka为村落，标准为North Dakota；尚未检查该具体地点与时代范围。

### row 490：uncertain
What Swedish songwriter worked with Taylor Swift?
标准：["Shellback"]
答案：Jörgen Elofsson
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 491：equivalent
Which author has won more Pulitzer Prizes, Thomas Friedman or Henri Bergson?
标准：["Thomas Loren Friedman"]
答案：Thomas Friedman
理由：Thomas Friedman与Thomas Loren Friedman同一人，省略中间名。

### row 492：incorrect
What studio album did Kanye West record with Roc-A-Fella Records and soul singer Dwele?
标准：["My Beautiful Dark Twisted Fantasy"]
答案：Late Registration
理由：逐题审阅最终答案与标准：Late Registration / ["My Beautiful Dark Twisted Fantasy"]；实体、数值、时间或所問字段不一致，维持错误。

### row 493：equivalent
Whose given first name is longer, Theo Angelopoulos and Budd Boetticher (nicknames)?
标准：["Theodoros \"Theo\" Angelopoulos"]
答案：Theo Angelopoulos
理由：Theo Angelopoulos与Theodoros Theo Angelopoulos同一导演的昵称和全名。

### row 494：incorrect
What year did a Russian soprano opera singer born in October 1926 leave Russia with her cellist husband and daughter?
标准：["1974"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 497：incorrect
What month did the an online adult website whose last print magazine was published in the summer of 2007 recognize Nikita Gross?
标准：["January"]
答案：August
理由：逐题审阅最终答案与标准：August / ["January"]；实体、数值、时间或所問字段不一致，维持错误。

### row 498：incorrect
Which airport is busier, Palm Springs International Airport or Trenton–Mercer Airport?
标准：["Trenton–Mercer Airport"]
答案：Palm Springs International Airport
理由：逐题审阅最终答案：Palm Springs International Airport；标准：["Trenton–Mercer Airport"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 500：incorrect
What was the third studio album released by Richard Melville Hall?
标准：["Everything Is Wrong"]
答案：Juju
理由：逐题审阅最终答案与标准：Juju / ["Everything Is Wrong"]；实体、数值、时间或所問字段不一致，维持错误。

### row 504：incorrect
Where is the headquarters for the service broadcaster the show Tenko is on?
标准：["Broadcasting House in London"]
答案：Tokyo
理由：逐题审阅最终答案与标准：Tokyo / ["Broadcasting House in London"]；实体、数值、时间或所問字段不一致，维持错误。

### row 505：incorrect
Francisco Mela performed with which American Jazz bassist and singer born in 1984 ?
标准：["Esperanza Spalding"]
答案：Kenny Barron
理由：逐题审阅最终答案与标准：Kenny Barron / ["Esperanza Spalding"]；实体、数值、时间或所問字段不一致，维持错误。

### row 509：uncertain
Where is the closest relative to the whale located?
标准：["sub-Saharan Africa"]
答案：Africa
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 510：incorrect
What English campaigner for the suffragette movement did Angela Down portray?
标准：["Sylvia Pankhurst"]
答案：Emmeline Pankhurst
理由：逐题审阅最终答案：Emmeline Pankhurst；标准：["Sylvia Pankhurst"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 511：incorrect
Christopher Oscar Pena was recognized by an entertainment-industry brand aimed at what?
标准：["people working in film and the performing arts"]
答案：LGBT
理由：逐题审阅最终答案与标准：LGBT / ["people working in film and the performing arts"]；实体、数值、时间或所問字段不一致，维持错误。

### row 517：equivalent
What is the English translation of the tier four league that TSV Schilksee was promoted to in 2014, following a league championship in the Schleswig-Holstein-Liga?
标准：["Regional League North"]
答案：Regionalliga Nord
理由：Regionalliga Nord与Regional League North指同一联赛名称，德文原名与英文直译语义一致。

### row 518：uncertain
Umi-a-Liloa inherited authority of a kind which is a belief in what?
标准：["belief in many deities and spirits"]
答案：Hawaiian religion
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 521：equivalent
What sport do The Basham Brothers and Doug Basham have in common?
标准：["wrestling"]
答案：professional wrestling
理由：professional wrestling与wrestling在职业摔跤人物语境中同一运动。

### row 523：incorrect
Which genus of plant grows originally in Mexico and Guatemala, Phylica or Weldenia?
标准：["Weldenia"]
答案：Phylica
理由：逐题审阅最终答案：Phylica；标准：["Weldenia"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 526：equivalent
Q:The 7.92×57mm Mauser rifle cartridge was used by which country's military in the 20th century?
标准：["German service cartridge"]
答案：Germany
理由：问题问国家，Germany提取标准German service cartridge中的国家身份。

### row 529：incorrect
Which company used a voice actor who also voiced He-Man?
标准：["9Lives"]
答案：Filmation Productions
理由：逐题审阅最终答案与标准：Filmation Productions / ["9Lives"]；实体、数值、时间或所問字段不一致，维持错误。

### row 531：equivalent
What prominent Soviet director worked frequently with Composer Isaak Dunayevsky?
标准：["Grigori Vasilyevich Aleksandrov"]
答案：Grigori Aleksandrov
理由：Grigori Aleksandrov与Grigori Vasilyevich Aleksandrov同一导演，省略父称。

### row 532：equivalent
Where is the headquarter of the American multinational chemical corporation who's part is Dow AgroSciences?
标准：["Midland, Michigan, United States"]
答案：Midland, Michigan
理由：Midland, Michigan与Midland, Michigan, United States同一总部城市，省略国家。

### row 534：incorrect
What is the prefix given to the end of the name to avoid confusion for the winner of the 1996 Record of the Year Grammy?
标准：["II"]
答案：Grammy
理由：逐题审阅最终答案与标准：Grammy / ["II"]。实体、数值、时间或所问字段不一致，维持错误。

### row 535：incorrect
When was the movie released that starred an American male actor born on February 28, 1923 and was written by Christopher Knopf?
标准：["December 23, 1977"]
答案：1951
理由：逐题审阅最终答案与标准：1951 / ["December 23, 1977"]；实体、数值、时间或所問字段不一致，维持错误。

### row 537：incorrect
The 2015 American drama film, Being Charlie, stars which Canadian actor that appeared in "Adoration" and "Saw VI"?
标准：["Devon Bostick"]
答案：Nick Robinson
理由：逐题审阅最终答案与标准：Nick Robinson / ["Devon Bostick"]；实体、数值、时间或所問字段不一致，维持错误。

### row 538：equivalent
What is the official currency in the country that hosts the Asahi-Ryokuken Yomiuri Memorial tournament?
标准：["yen"]
答案：Japanese yen
理由：Japanese yen与yen在题目限定日本货币语境下同一币种。

### row 539：equivalent
What collegiate division does the team coached by P.W. Underwood play in?
标准：["Division I"]
答案：NCAA Division I
理由：NCAA Division I与Division I同一大学体育分级，附加联盟限定。

### row 540：incorrect
"I Will Not Say Goodbye" is a song written in part by a music artist who first gained national attention as a winner of what talent competition?
标准：["You Can Be a Star"]
答案：American Idol
理由：逐题审阅最终答案：American Idol；标准：["You Can Be a Star"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 541：incorrect
What two singers who worked together on the song I Would Like to See You Again also performed as part of a country music group which was active between 1985 and 1995?
标准：["Johnny Cash, Waylon Jennings"]
答案：Waylon Jennings
理由：逐题审阅最终答案：Waylon Jennings；标准：["Johnny Cash, Waylon Jennings"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 542：incorrect
The M104 155mm Projectile was specifically designed to carry about 11.7 pounds of what prototypical substance?
标准：["mustard gas"]
答案：white phosphorus
理由：逐题审阅最终答案：white phosphorus；标准：["mustard gas"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 544：incorrect
In what part of England is John Folwes' country house located?
标准：["West Dorset, South West England."]
答案：Berkshire
理由：逐题审阅最终答案：Berkshire；标准：["West Dorset, South West England."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 545：incorrect
What is the global rank by population of the city that Daewoong Pharmaceutical Co., Ltd is based in?
标准：["world's 16th largest city"]
答案：10th
理由：逐题审阅最终答案与标准：10th / ["world's 16th largest city"]；实体、数值、时间或所問字段不一致，维持错误。

### row 546：equivalent
what year was the cover artist of Multiverse: Exploring Poul Anderson's Worlds born ?
标准：["September 13, 1960"]
答案：1960
理由：题目只问year，1960完整提取标准September 13, 1960中的年份。

### row 547：incorrect
The producer of "Live By NIght" began his film career playing what role in "Critters 3"?
标准：["Josh"]
答案：Charlie
理由：逐题审阅最终答案与标准：Charlie / ["Josh"]；实体、数值、时间或所問字段不一致，维持错误。

### row 548：incorrect
An actress in Strange Fruit was better known for a role in CBS sitcom.  Which sitcom is this actress better known for than her role in Strange Fruit?
标准：["The Jeffersons"]
答案：The Mary Tyler Moore Show
理由：逐题审阅最终答案与标准：The Mary Tyler Moore Show / ["The Jeffersons"]；实体、数值、时间或所問字段不一致，维持错误。

### row 549：incorrect
Who was born first Doug Liman or Saul Metzstein?
标准：["Douglas Eric \"Doug\" Liman"]
答案：Saul Metzstein
理由：逐题审阅最终答案：Saul Metzstein；标准：["Douglas Eric \"Doug\" Liman"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 550：incorrect
What year was George Harrison's top UK charted song voted the nations 11th favorite 1980s number?
标准：["2015"]
答案：1987
理由：逐题审阅最终答案与标准：1987 / ["2015"]；实体、数值、时间或所問字段不一致，维持错误。

### row 553：incorrect
The Environment Act 1995 passed under the tutelage of a politician associated with what political party?
标准：["British Conservative Party"]
答案：Labour Party
理由：逐题审阅最终答案：Labour Party；标准：["British Conservative Party"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 556：uncertain
the work of The Last Poets and Gil Scott Heron inspired music that fits under what larger sub-genre?
标准：["underground hip hop"]
答案：political hip hop
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 557：incorrect
Which date occurred first the end of Riley Hawk's amateur career or end of production of Skateboard Magazine ?
标准：["October 15, 2013"]
答案：end of production of Skateboard Magazine
理由：逐题审阅最终答案与标准：end of production of Skateboard Magazine / ["October 15, 2013"]；实体、数值、时间或所問字段不一致，维持错误。

### row 558：incorrect
What team was formed in 1996 that starred players like Robert Parish?
标准：["50 Greatest Players in National Basketball Association History"]
答案：Chicago Bulls
理由：逐题审阅最终答案：Chicago Bulls；标准：["50 Greatest Players in National Basketball Association History"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 559：equivalent
What was the name of the company that produced  the first practical jet aircraft that first flew on 27 August 1939?
标准：["Heinkel Flugzeugwerke"]
答案：Heinkel
理由：Heinkel与Heinkel Flugzeugwerke同一飞机制造企业，采用常用短名。

### row 560：uncertain
What is the name of the largest publicly owned company in Minnesota that is situated in Minnesota's most populous county?
标准：["United Healthcare"]
答案：UnitedHealth Group
理由：UnitedHealth Group与United Healthcare为母公司与业务品牌关系；轨迹支持前者但不与后者直接等价。

### row 561：incorrect
What Hong Kong actor born in 1980 will star in "Heart and Greed"?
标准：["Bosco Wong Chung-chak"]
答案：Nicholas Tse
理由：逐题审阅最终答案与标准：Nicholas Tse / ["Bosco Wong Chung-chak"]；实体、数值、时间或所問字段不一致，维持错误。

### row 563：incorrect
Before moving to Boston to play at the New England Patriots, in which city did Dean Caliguire play his college and NFL football?
标准：["Pittsburgh"]
答案：Raleigh
理由：逐题审阅最终答案与标准：Raleigh / ["Pittsburgh"]；实体、数值、时间或所問字段不一致，维持错误。

### row 566：equivalent
Which film was was made first The Young Black Stallion or Wild Hearts Can't Be Broken?
标准：["Wild Hearts Can’t Be Broken"]
答案：Wild Hearts Can't Be Broken
理由：Wild Hearts Can't Be Broken与Wild Hearts Can’t Be Broken仅撇号编码不同。

### row 568：equivalent
At least how many countries does the company that bought Oil Can Henry's operate in?
标准：["100 countries"]
答案：more than 100
理由：题目问至少多少国家；more than 100包含标准的100个国家下界，未减少覆盖数。

### row 570：incorrect
What railroad in which Challengers were most common was completed in 1915?
标准：["Clinchfield Railroad"]
答案：Milwaukee Road
理由：逐题审阅最终答案与标准：Milwaukee Road / ["Clinchfield Railroad"]。实体、数值、时间或所问字段不一致，维持错误。

### row 571：incorrect
What component was included on the iPad4 that is now a registered trademark in Jamaica?
标准：["Retina Display"]
答案：Lightning connector
理由：逐题审阅最终答案：Lightning connector；标准：["Retina Display"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 572：incorrect
Rejuvelac is kind of grain water invented and promoted by a "holistic health" practitioner born in which year ?
标准：["1909"]
答案：1957
理由：逐题审阅最终答案：1957；标准：["1909"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 573：uncertain
What is the nationality of the author of Fifty Shades Freed?
标准：["English"]
答案：British
理由：British比English范围更宽，严格等价主分数暂不增加。

### row 574：uncertain
The Church of St Peter in Pertenhall, Bedfordshire, England was added to this register on 13 July 1964.?
标准：["Statutory List of Buildings of Special Architectural or Historic Interest"]
答案：National Heritage List for England
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 577：incorrect
What is Rachelle Amy Beinart's role in the film that follows a group of rebels on a mission?
标准：["stunt performances"]
答案：Sabine
理由：逐题审阅最终答案与标准：Sabine / ["stunt performances"]；实体、数值、时间或所問字段不一致，维持错误。

### row 578：incorrect
The water-based dark ride in Walt Disney is connected to a song known for what?
标准：["most performed song of all time"]
答案：a pirate's life for me
理由：逐题审阅最终答案与标准：a pirate's life for me / ["most performed song of all time"]；实体、数值、时间或所問字段不一致，维持错误。

### row 579：incorrect
What is this fictional scientifically and technologically advanced militaristic alien race, from which Sequoia descends, is called?
标准：["the Ruul"]
答案：Kree
理由：逐题审阅最终答案：Kree；标准：["the Ruul"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 581：label_issue
Who did the Star and Dagger bass player marry?
标准：["Sean Yseult."]
答案：Alison Statton
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 582：incorrect
Which American pro basketball player who won gold at the 2008 Summer Olympics was signed by the Utah Jazz during the 2005-05 offseason?
标准：["Carlos Austin Boozer Jr."]
答案：Deron Williams
理由：逐题审阅最终答案：Deron Williams；标准：["Carlos Austin Boozer Jr."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 591：equivalent
The Lowry Hotel is named after an artist, many of whose drawings and paintings depict what town?
标准：["Pendlebury, Lancashire"]
答案：Pendlebury
理由：题目问town，Pendlebury完整给出标准Pendlebury, Lancashire中的城镇名。

### row 592：incorrect
Where is the company owning Reliance Cricket Stadium ranked on the Fortune Global 500 list as of 2016?
标准：["215th"]
答案：203rd
理由：逐题审阅最终答案：203rd；标准：["215th"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 593：incorrect
Alex Jesaulenko, former Australian rules footballer and coach won the award The Goal of the Year. In what year did he win that award?
标准：["2001"]
答案：1970
理由：逐题审阅最终答案：1970；标准：["2001"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 594：label_issue
What city does Paul Clyne and David Soares have in common?
标准：["New York"]
答案：Albany
理由：两人关联Albany但金标准New York，城市和州字段存在标签歧义。

### row 596：incorrect
A Japanese manga series based on a 16 year old high school student Ichitaka Seto, is written and illustrated by someone born in what year?
标准：["1962"]
答案：1974
理由：逐题审阅最终答案与标准：1974 / ["1962"]；实体、数值、时间或所問字段不一致，维持错误。

### row 597：incorrect
What wrestling team is Mathew Thomas Rehwoldt a part of?
标准：["The Vaudevillains"]
答案：WWE
理由：逐题审阅最终答案与标准：WWE / ["The Vaudevillains"]；实体、数值、时间或所問字段不一致，维持错误。

### row 599：incorrect
How many times has the author of Writing with Intent been shortlisted for the Booker Prize ?
标准：["five times"]
答案：twice
理由：逐题审阅最终答案：twice；标准：["five times"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 604：incorrect
Of these two publication--Báiki and Sick--what type of publication is the one that was published most frequently?
标准：["satirical-humor magazine"]
答案：journal
理由：逐题审阅最终答案与标准：journal / ["satirical-humor magazine"]；实体、数值、时间或所問字段不一致，维持错误。

### row 606：uncertain
What is in both the Lithocarpus and Duranta species?
标准：["trees"]
答案：flowering plants
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 607：equivalent
Which writer also enjoyed boxing, Amy Tan or Norman Lindsay?
标准：["Norman Alfred William Lindsay"]
答案：Norman Lindsay
理由：Norman Lindsay与Norman Alfred William Lindsay同一作家，省略中间名。

### row 608：incorrect
Ralph Faudree served as the American equivalent to what United Kingdom and Australian position?
标准：["pro-vice-chancellor"]
答案：Prime Minister
理由：逐题审阅最终答案与标准：Prime Minister / ["pro-vice-chancellor"]。实体、数值、时间或所问字段不一致，维持错误。

### row 609：incorrect
What is the size of the archaeological site which is in the hamlet of the Guilderland in Albany County, New York?
标准：["2 acre"]
答案：1 acre
理由：逐题审阅最终答案与标准：1 acre / ["2 acre"]；实体、数值、时间或所問字段不一致，维持错误。

### row 611：equivalent
On which coast can the California Aqueduct and the Lake Washington Ship Canal be found?
标准：["west"]
答案：west coast
理由：west coast与west在海岸问题中相同方向，附加单位词。

### row 612：uncertain
What do Josef Veltjens and Hermann Goering have in common?
标准：["A veteran World War I fighter pilot ace"]
答案：German
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 614：incorrect
In addition to the individual born on August 21, who else wrote He's The Great Imposter?
标准：["Sharon Sheeley"]
答案：Brennan Manning
理由：逐题审阅最终答案与标准：Brennan Manning / ["Sharon Sheeley"]；实体、数值、时间或所問字段不一致，维持错误。

### row 615：equivalent
Who appeared in the Olympics first, Piet Norval or Emilio Sánchez?
标准：["Sanchez"]
答案：Emilio Sánchez
理由：Emilio Sánchez与Sanchez在指定两位网球运动员中同一人，附加名及重音符。

### row 617：equivalent
Which filmmaker, Stan Brakhage or Alfred L. Werker, was a non-narrative filmmaker?
标准：["James Stanley Brakhage"]
答案：Stan Brakhage
理由：Stan Brakhage与James Stanley Brakhage同一电影人的常用名和全名。

### row 618：incorrect
Blackamoor, Lancashire lies near the banks of what river?
标准：["Ribble"]
答案：River Conder
理由：逐题审阅最终答案与标准：River Conder / ["Ribble"]；实体、数值、时间或所問字段不一致，维持错误。

### row 619：incorrect
How many episodes did the season of The Simpsons which featured the voice of Lisa Kudrow contain?
标准：["It contains twenty-three episodes"]
答案：25
理由：逐题审阅最终答案：25；标准：["It contains twenty-three episodes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 620：equivalent
John Hatzistergos was a Member of a council that has how many members ?
标准：["42 members"]
答案：42
理由：42与42 members同一数量，省略题目已限定单位。

### row 621：incorrect
Ross Pople worked with this French dominant figure of the post-war classical music world.?
标准：["Pierre Louis Joseph Boulez"]
答案：André Popp
理由：逐题审阅最终答案与标准：André Popp / ["Pierre Louis Joseph Boulez"]；实体、数值、时间或所問字段不一致，维持错误。

### row 622：equivalent
John Stark Regional High School serves the community in which New Hampshire county?
标准：["Merrimack"]
答案：Merrimack County
理由：Merrimack County与Merrimack同一县，附加单位词。

### row 623：equivalent
Who has the highest scope of profession in Peter Yates or Jang Joon-hwan?
标准：["Peter James Yates"]
答案：Peter Yates
理由：Peter Yates与Peter James Yates同一导演，省略中间名。

### row 624：equivalent
Who wrote lyrics for both "Little Shop of Horrors" and the song "Be Our Guest?"?
标准：["Howard Elliott Ashman"]
答案：Howard Ashman
理由：Howard Ashman与Howard Elliott Ashman同一作词人，省略中间名。

### row 627：incorrect
The player who defeated Johnny Majors for the Heisman Trophy in 1956 was born in what year?
标准：["1935"]
答案：1930
理由：逐题审阅最终答案与标准：1930 / ["1935"]；实体、数值、时间或所問字段不一致，维持错误。

### row 631：equivalent
Which interviewee featured in The History of Sex also hosted the radio show "Sexually Speaking"?
标准：["Dr. Ruth Westheimer"]
答案：Ruth Westheimer
理由：Ruth Westheimer与Dr. Ruth Westheimer同一人，省略学衔。

### row 632：incorrect
This event which was part of the 1954 AAA National Championship Trail was held at a racing circuit located at the corner of what?
标准：["16th Street and Georgetown Road"]
答案：Route 14
理由：逐题审阅最终答案与标准：Route 14 / ["16th Street and Georgetown Road"]；实体、数值、时间或所問字段不一致，维持错误。

### row 634：equivalent
Which Hong Kong actor born on 19 August 1946 starred in The Sentimental Swordsman?
标准：["Tommy Tam Fu-Wing"]
答案：Ti Lung
理由：轨迹Ti Lung条目明确Tommy Tam Fu-Wing known by stage name Ti Lung，同一演员艺名。

### row 635：equivalent
Who is the sister of Princess Zein and the daughter of a British woman?
标准：["Princess Aisha bint Hussein"]
答案：Princess Aisha
理由：Princess Aisha与Princess Aisha bint Hussein在Princess Zein姐妹语境中同一人。

### row 636：equivalent
Which  American politician and lawyer contested in San Francisco mayoral election, 2003?
标准：["Matthew Edward"]
答案：Matt Gonzalez
理由：轨迹明确Matt Gonzalez本名Matthew Edward Gonzalez；标准Matthew Edward是同一人名截断。

### row 638：incorrect
Where was the community schools to which Franklin Community High School was part of headquartered ?
标准：["Franklin, Indiana"]
答案：Marion County
理由：逐题审阅最终答案与标准：Marion County / ["Franklin, Indiana"]；实体、数值、时间或所問字段不一致，维持错误。

### row 639：incorrect
Where was the artist behind "Shit" born and raised?
标准：["Atlanta, Georgia"]
答案：Soncino
理由：逐题审阅最终答案与标准：Soncino / ["Atlanta, Georgia"]；实体、数值、时间或所問字段不一致，维持错误。

### row 642：incorrect
Josephine de Reszke made her debut in what grand opera?
标准：["Hamlet"]
答案：Aida
理由：逐题审阅最终答案：Aida；标准：["Hamlet"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 644：incorrect
How many seasons has a popular tv show had, in which one of the episodes is called Moho House?
标准：["28"]
答案：thirty
理由：逐题审阅最终答案与标准：thirty / ["28"]；实体、数值、时间或所問字段不一致，维持错误。

### row 645：incorrect
where is the American professional basketball team which Jalen Jones played for based?
标准：["Louisiana."]
答案：Cleveland, Ohio
理由：逐题审阅最终答案：Cleveland, Ohio；标准：["Louisiana."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 646：incorrect
Jack Alfred Evans played with a football club team that is based in what city in Australia?
标准：["Melbourne"]
答案：Geelong
理由：逐题审阅最终答案：Geelong；标准：["Melbourne"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 647：incorrect
The Collective for Living Cinema of Lower Manhattan featured work from what filmmaker also known as Denis Kaufman?
标准：["Dziga Vertov"]
答案：Lizzie Borden
理由：逐题审阅最终答案与标准：Lizzie Borden / ["Dziga Vertov"]；实体、数值、时间或所問字段不一致，维持错误。

### row 648：equivalent
How many more singles titles did Kim Warwick win than Jorge Lozano?
标准：["three singles titles"]
答案：3
理由：3与three singles titles同一数量。

### row 650：equivalent
How many members were in the South Korean boy group whose first official sub-unit is Bastarz?
标准：["seven members"]
答案：seven
理由：seven与seven members同一团体人数。

### row 651：incorrect
Where was the second World Junior Ice Hockey Championship in which Miroslav Přerost coached the men's national junior ice hockey team hosted?
标准：["Ufa, Russia"]
答案：Czech Republic
理由：逐题审阅最终答案与标准：Czech Republic / ["Ufa, Russia"]；实体、数值、时间或所問字段不一致，维持错误。

### row 652：incorrect
When did British politician Damian Green state that said that e-Borders would be collecting information an all passengers on 100% of non-EEA flights to the UK?
标准：["April"]
答案：March 2012
理由：逐题审阅最终答案：March 2012；标准：["April"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 653：incorrect
Which animal races annually for a national title as part of a post-season NCAA Division I Football Bowl Subdivision college football game?\?
标准：["Dachshunds"]
答案：horse
理由：逐题审阅最终答案与标准：horse / ["Dachshunds"]；实体、数值、时间或所問字段不一致，维持错误。

### row 655：equivalent
Steve Denton and Albert Costa are both tennis players, which one began playing at the age if five?
标准：["Costa"]
答案：Albert Costa
理由：Albert Costa与Costa在两位网球选手比较语境下同一人。

### row 656：equivalent
College Humor is a 1933 American pre-Code musical comedy film that starred what American singer and actor who has a trademark warm bass-baritone voice?
标准：["Harry Lillis \"Bing\" Crosby Jr."]
答案：Bing Crosby
理由：Bing Crosby与Harry Lillis Bing Crosby Jr.同一演员歌手的艺名和全名。

### row 659：label_issue
What Danish sports club based in Copenhagen  did striker Søren Lindsted start his career at?
标准：["Søren Lindsted"]
答案：None
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 661：uncertain
What's the common ingredient to a Gimlet and Pink Gin?
标准：["Plymouth Gin"]
答案：gin
理由：gin省略Plymouth特定品牌，不能唯一指认标准。

### row 663：incorrect
Who is older, Anne Noe or Jean-Marie Pfaff?
标准：["Jean-Marie Pfaff"]
答案：Anne Noe
理由：逐题审阅最终答案：Anne Noe；标准：["Jean-Marie Pfaff"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 667：equivalent
Who is a poet, Rumi or Farouk El-Baz?
标准：["Rumi (30 September 1207 – 17 December 1273), was a 13th-century Persian Sunni Muslim poet"]
答案：Rumi
理由：Rumi是标准长句中被指认的诗人，省略不必需传记描述。

### row 668：incorrect
Who directed both Last Days and Point Break?
标准：["Kathryn Bigelow"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 669：incorrect
What type of diary did one of the founders of the John Bishop Memorial Hospital in Srinagar write?
标准：["a travel diary"]
答案：personal
理由：逐题审阅最终答案与标准：personal / ["a travel diary"]；实体、数值、时间或所問字段不一致，维持错误。

### row 670：equivalent
who is older, Maria Sharapova or Chanda Rubin?
标准：["Chanda Rubin (born February 18, 1976)"]
答案：Chanda Rubin
理由：Chanda Rubin与带出生日期的Chanda Rubin同一选项。

### row 672：uncertain
Which American former competitive swimmer was Mitzi Kremer team mate?
标准：["Dara Grace Torres"]
答案：Laura Walker
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 675：equivalent
Which Lithuanian-Canadian anthropologist, primatologist, conservationist, ethologist, and author was chosen by  Louis Leakey, along with Jane Goodall, Dian Fossey to study hominids in their natural environments?
标准：["Birutė Marija Filomena Galdikas"]
答案：Birutė Galdikas
理由：Birutė Galdikas与Birutė Marija Filomena Galdikas同一人，省略中间名。

### row 677：equivalent
In between Burton C. Bell and Billy Idol who is known professionally as Billy Idol?
标准：["William Michael Albert Broad"]
答案：Billy Idol
理由：Billy Idol与William Michael Albert Broad同一人的艺名与本名；题目要求在两人中选身份。

### row 679：incorrect
The genus containing lions also contains several poorly known what?
标准：["Old World fossil representatives"]
答案：subspecies
理由：逐题审阅最终答案：subspecies；标准：["Old World fossil representatives"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 681：equivalent
What role did Kim Dong-wook play in the 2012 South Korean historical film directed by Kim Dae-seung?
标准：["an obsessed and tormented king"]
答案：Prince Sung-won
理由：轨迹把同一演员在The Concubine中的角色称Prince Sung-won，并描述为obsessed and tormented king；角色名与标准角色描述一致。

### row 682：incorrect
What amount was the settlement that the character from the Son of al Quada got in 2017?
标准：["$10.5 million"]
答案：$75 million
理由：逐题审阅最终答案与标准：$75 million / ["$10.5 million"]；实体、数值、时间或所問字段不一致，维持错误。

### row 686：incorrect
Who was also an actor, Serri or John Fogerty?
标准：["Serri"]
答案：John Fogerty
理由：逐题审阅最终答案与标准：John Fogerty / ["Serri"]。实体、数值、时间或所问字段不一致，维持错误。

### row 688：equivalent
The competition Lev Oborin won in 1927 is held in what city?
标准：["Warsaw, Poland"]
答案：Warsaw
理由：题目只问city，Warsaw完整回答Warsaw, Poland中的城市。

### row 691：incorrect
Are both Frank Lloyd and Olivier Assayas American film directors?
标准：["no"]
答案：yes
理由：逐题审阅最终答案与标准：yes / ["no"]；实体、数值、时间或所問字段不一致，维持错误。

### row 697：incorrect
Which producer from the 2015 British documentary film about the life and death of British singer-songwriter Amy Winehouse also worked on the film Oasis: Supersonic as a film producer?
标准：["James Gay-Rees"]
答案：Asif Kapadia
理由：逐题审阅最终答案与标准：Asif Kapadia / ["James Gay-Rees"]；实体、数值、时间或所問字段不一致，维持错误。

### row 701：incorrect
The Chinese actress also known as Crystal Liu stars in Night Peacock with which three other actresses?
标准：["Liu Ye, Yu Shaoqun and Leon Lai"]
答案：Liu Yifei
理由：逐题审阅最终答案与标准：Liu Yifei / ["Liu Ye, Yu Shaoqun and Leon Lai"]；实体、数值、时间或所問字段不一致，维持错误。

### row 702：uncertain
What retailer did Albert Heijn start up that eventually merged with the Delhaize Group?
标准：["Koninklijke Ahold N.V."]
答案：Albert Heijn
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 703：incorrect
What is the name of the umcoming horror film adaptation starring Melanie Griffiths daughter?
标准：["Suspiria"]
答案：Piercing
理由：逐题审阅最终答案与标准：Piercing / ["Suspiria"]；实体、数值、时间或所問字段不一致，维持错误。

### row 704：equivalent
The 2013 Oregon Ducks football team was led by which former American football coach who is currently a college football analyst for Fox Sports?
标准：["Mark August Helfrich"]
答案：Mark Helfrich
理由：Mark Helfrich与Mark August Helfrich同一教练，省略中间名。

### row 706：incorrect
The German who is credited with inventing the V-2 rocket and Saturn V was also a supervisor of what NASA program?
标准：["Applications Technology Satellites"]
答案：Apollo program
理由：逐题审阅最终答案：Apollo program；标准：["Applications Technology Satellites"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 707：incorrect
Which organization has been led by the overseer of the Renewable Heat Incentive Scandal since 2003?
标准：["Northern Ireland Assembly for Fermanagh and South Tyrone"]
答案：Democratic Unionist Party
理由：逐题审阅最终答案：Democratic Unionist Party；标准：["Northern Ireland Assembly for Fermanagh and South Tyrone"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 708：label_issue
Is The Stuff of Legend and Babes in Toyland both entertainment?
标准：["by"]
答案：yes
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 710：equivalent
The Legendary A&M Sessions contain five songs by the singer whose work was conducted with what band?
标准：["Magic Band"]
答案：His Magic Band
理由：His Magic Band与Magic Band在Captain Beefheart语境中同一乐队。

### row 711：label_issue
which  Australian politician represented  Electoral district of Goulburn?
标准：["Jane Goward"]
答案：Pru Goward
理由：轨迹支持Pru Goward，金标准Jane Goward疑似姓名错误；非同名别名。

### row 713：uncertain
What kind of group does Josey Scott and Kurt Cobain have in common?
标准：["band"]
答案：rock
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 718：equivalent
Which guitarist that played on the LP Street Survivors and was a member of an American Southern Rock band from May 1976 until his death Oct 1977?
标准：["Steven Earl \"Steve\" Gaines"]
答案：Steve Gaines
理由：Steve Gaines与Steven Earl Steve Gaines同一吉他手的常用名和全名。

### row 720：uncertain
Which countries forces fought in The Battle of Hürtgen Forest which was covered in the shooter video game Darkest Hour: Europe '44-'45?
标准：["American and German"]
答案：United States
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 723：equivalent
What sport is featured in the film in which Kwon Yu-ri made her film debut ?
标准：["swimming"]
答案：competitive swimming
理由：competitive swimming与swimming在体育电影问题下同一游泳运动。

### row 724：equivalent
To where did the war criminal who is the fictional defendant in the film After the Truth flee in real life ?
标准：["South America"]
答案：Argentina
理由：轨迹明确躲藏在Argentina；Argentina是标准South America内的具体逃亡目的地。

### row 725：uncertain
When was the federal US law made that was responsible for shutting down Braniff Airways?
标准：["1978"]
答案：December 1978
理由：标准1978的法案实际签署于10月，答案附加December存在日期冲突，不仅凭年份包含加分。

### row 726：incorrect
Which tropical storm has been present in the Central Pacific Ocean but not in the western north Pacific Ocean?
标准：["Ana"]
答案：Invest 91C
理由：逐题审阅最终答案：Invest 91C；标准：["Ana"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 728：uncertain
Where was the singer born who performs Pon de Replay and was born Robyn Fenty?
标准：["Saint Michael, Barbados"]
答案：Barbados
理由：Barbados省略Saint Michael的具体出生地点。

### row 729：equivalent
Which star of Zork was also the voice of Pac-Man?
标准：["Martin Ingerman"]
答案：Marty Ingels
理由：轨迹明确Martin Ingerman known professionally as Marty Ingels，同一演员的本名与艺名。

### row 730：incorrect
What is the relationship of Yeshahework Yilma's mother to the man who was Ethiopia's emperor from 1930 to 1974?
标准：["niece"]
答案：aunt
理由：逐题审阅最终答案与标准：aunt / ["niece"]；实体、数值、时间或所問字段不一致，维持错误。

### row 731：uncertain
What offence were opening batsman Khalid Latif and 5 other cricketers suspended for, in February 2017?
标准：["spot-fixing"]
答案：violating the Pakistan Cricket Board's (PCB) anti-corruption code
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 732：equivalent
What is the main difference between the game Plateau and the game Colt Express?
标准：["Colt Express is a railway-themed"]
答案：railway-themed family board game
理由：railway-themed family board game明确给所问Colt Express的railway-themed主题差异。

### row 734：incorrect
Both WAGS Atlanta and WAGS are what?
标准：["American reality television series"]
答案：wives and girlfriends of high-profile sportspersons
理由：逐题审阅最终答案与标准：wives and girlfriends of high-profile sportspersons / ["American reality television series"]；实体、数值、时间或所問字段不一致，维持错误。

### row 735：equivalent
Vivian Pinn taught at which college founded in Massachusetts in 1852?
标准：["Tufts College"]
答案：Tufts University School of Medicine
理由：轨迹明确Pinn在Tufts University School of Medicine教学；同一Tufts机构的具体教学单位。

### row 737：equivalent
Which Bob Stoops coached team beat the 2016 Auburn Tigers football team?
标准：["2016 Oklahoma Sooners football team"]
答案：Oklahoma Sooners
理由：Oklahoma Sooners与2016 Oklahoma Sooners football team同一限定赛季球队，题目已给2016语境。

### row 739：uncertain
What airline holding company located in Solna Municipality, Sweden owns a technical aircraft maintenance company located in Arlanda, Sweden?
标准：["SAS Group"]
答案：Scandinavian Airlines
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 740：incorrect
Which tower is taller, 712 Fifth Avenue or Manhattan Life Insurance Building?
标准：["712 5th Avenue"]
答案：Manhattan Life Insurance Building
理由：逐题审阅最终答案与标准：Manhattan Life Insurance Building / ["712 5th Avenue"]；实体、数值、时间或所問字段不一致，维持错误。

### row 743：incorrect
What are the publishing years of this American and New York based film magazine published by Hachette Filipacchi Media U.S., where April Bernard worked as senior editor?
标准：["between 1987 and 2010"]
答案：1920
理由：逐题审阅最终答案与标准：1920 / ["between 1987 and 2010"]；实体、数值、时间或所問字段不一致，维持错误。

### row 745：uncertain
When was the track from which a sample was featured in "Take Me to the Clouds Above" released?
标准：["16 March 1987"]
答案：1987
理由：1987省略标准16 March日期，保留精度不足。

### row 747：incorrect
What was the capacity of the stadium that Colección Privada that was filmed on October 10, 2000?
标准：["15,500"]
答案：80,093
理由：逐题审阅最终答案：80,093；标准：["15,500"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 750：incorrect
Here's Little Richard is a debut album containing a song written by Little Richard, Enotris Johnson and who else?
标准：["Robert \"Bumps\" Blackwell"]
答案：Dorothy LaBostrie
理由：逐题审阅最终答案与标准：Dorothy LaBostrie / ["Robert \"Bumps\" Blackwell"]；实体、数值、时间或所問字段不一致，维持错误。

### row 751：equivalent
Which writer was from England, Henry Roth or Robert Erskine Childers?
标准：["Robert Erskine Childers DSC"]
答案：Robert Erskine Childers
理由：Robert Erskine Childers与附加DSC勋衔的标准同一人。

### row 754：equivalent
Which two occupations does Ronnie Dunn and Annie Lennox have in common?
标准：["singer, songwriter"]
答案：singer-songwriter
理由：singer-songwriter完整给出singer和songwriter两项职业。

### row 755：equivalent
What is the current position held by the Nathan Sharansky's co-author of the book The Case for Democracy?
标准：["Israeli Ambassador"]
答案：Israeli Ambassador to the United States
理由：Israeli Ambassador to the United States保留Israeli Ambassador职位并补充派驻国家。

### row 756：equivalent
Theme Park Inc is a video game that created what sequel in North America in 1999?
标准：["Sim Theme Park"]
答案：Theme Park World
理由：轨迹明确Theme Park World在North America称Sim Theme Park，为同一游戏别名。

### row 757：equivalent
August R. Lindt served as chairman of a UN program from 1956 to 1960 that won how many noble prizes ?
标准：["two Nobel Peace Prizes"]
答案：two
理由：two与two Nobel Peace Prizes在奖项次数问题下同一数量。

### row 758：equivalent
Between Joe Orton and Henry James, which author is the adjective "Ortonesque" used to refer to his work?
标准：["John Kingsley \"Joe\" Orton"]
答案：Joe Orton
理由：Joe Orton与John Kingsley Joe Orton同一作家的常用名和全名。

### row 760：incorrect
when was american stunt performer which Stunt Cycle attempted to cash in with born?
标准：["October 17, 1938"]
答案：October 12, 1958
理由：逐题审阅最终答案与标准：October 12, 1958 / ["October 17, 1938"]；实体、数值、时间或所問字段不一致，维持错误。

### row 761：equivalent
What kind of music do The Stone Roses and The Lemonheads play?
标准：["rock band"]
答案：rock
理由：题目问音乐类型，rock完整提取标准rock band中的音乐类型。

### row 762：uncertain
what caused the death of over 250 people in Accra, Ghana?
标准：["an explosion and a fire occurred at a petrol station"]
答案：explosion
理由：explosion未完整给出explosion and fire两个原因。

### row 764：equivalent
Are Dorothy Parker and Maxine Kumin the same nationality?
标准：["yes"]
答案：American
理由：该两人比较问题下回答American表明二者同为美国人，隐含肯定same nationality命题。

### row 765：equivalent
Edward C. Hugger and Alexander Acosta served at appointees for what job?
标准：["Secretary of Labor"]
答案：United States Secretary of Labor
理由：United States Secretary of Labor与Secretary of Labor同一职位，附加国家限定。

### row 766：incorrect
Which Roman Emperor was grandfather to the children of Mark Antony?
标准：["Caligula"]
答案：Augustus
理由：逐题审阅最终答案：Augustus；标准：["Caligula"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 768：incorrect
Keith Konrad Slettedahl appeared on which season of "How I Met Your Mother"?
标准：["first"]
答案：fourth
理由：逐题审阅最终答案与标准：fourth / ["first"]；实体、数值、时间或所問字段不一致，维持错误。

### row 769：equivalent
Suicide's 1977 released album features a song based on what brand's comic character?
标准：["Marvel"]
答案：Marvel Comics
理由：Marvel Comics与Marvel同一漫画公司，附加业务名。

### row 771：incorrect
What is the height of the tallest mountain from which the Glen River flows?
标准：["850 m"]
答案：3,655 feet
理由：逐题审阅最终答案与标准：3,655 feet / ["850 m"]；实体、数值、时间或所問字段不一致，维持错误。

### row 773：equivalent
When was the improvisational troupe, which trained Amy Sedaris, Paul Dinello, and Stephen Colber, founded?
标准：["1959"]
答案：December 16, 1959
理由：December 16, 1959为The Second City成立日，给出标准1959的相容细化日期。

### row 774：equivalent
In whose government did the original owner of Heythrop Park come to prominence?
标准：["William's"]
答案：William III
理由：William III完整给Heythrop Park原主人语境中的William君主身份。

### row 775：equivalent
The M1919 and the M1 was used by what military?
标准：["U.S."]
答案：U.S. military
理由：U.S. military与U.S.在军队归属问题中同一美国军队。

### row 776：equivalent
What kind of comedian was Michael Mclntyre's father?
标准：["Canadian comedian"]
答案：Canadian
理由：题目已限定comedian，Canadian完整回答标准Canadian comedian的国籍限定。

### row 777：incorrect
Cyrina Fiallo has guest starred on which Michael Jacobs-created sitcom?
标准：["Girl Meets World"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 779：equivalent
Zach Parise's father played in which league?
标准：["NHL"]
答案：National Hockey League
理由：National Hockey League与NHL同一联赛的全称和缩写。

### row 781：incorrect
Bobby Bowden coached which former Toronto Blue Jays minor league baseball player?
标准：["Chris Weinke"]
答案：Tim Leiper
理由：逐题审阅最终答案与标准：Tim Leiper / ["Chris Weinke"]；实体、数值、时间或所問字段不一致，维持错误。

### row 782：incorrect
Which of the university at which Jack M. Guttentag  is a professor emeritus of finance was established in 1881 through a donation?
标准：["Wharton School of the University"]
答案：McMaster University
理由：逐题审阅最终答案与标准：McMaster University / ["Wharton School of the University"]；实体、数值、时间或所問字段不一致，维持错误。

### row 785：uncertain
What criteria subjectively qualifies the Houston Astrodome to be called the Eighth Wonder of the World?
标准：["comparable to the seven Wonders of the World"]
答案：innovative design
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 786：incorrect
What other jobs did the man that co-produced Gyara Hazar Ladkian have?
标准：["film lyricist"]
答案：poet
理由：逐题审阅最终答案：poet；标准：["film lyricist"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 787：incorrect
What song included on the 59th edition of Now That's What I Call Music was written and recorded by an Australian recording artist?
标准：["\"Cheap Thrills\" by Sia"]
答案：Call My Name
理由：逐题审阅最终答案与标准：Call My Name / ["\"Cheap Thrills\" by Sia"]；实体、数值、时间或所問字段不一致，维持错误。

### row 789：incorrect
Jamie Harris is best known for his role as The Hook-Handed Man in a movie directed by who ?
标准：["Brad Silberling"]
答案：Karl Maka
理由：逐题审阅最终答案与标准：Karl Maka / ["Brad Silberling"]；实体、数值、时间或所問字段不一致，维持错误。

### row 790：uncertain
Igor Naming Agency named a resort located where?
标准：["Las Vegas Strip"]
答案：Paradise, Nevada
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 791：incorrect
Who is a guest in the final two episodes of season eighteen of South Park?
标准：["PewDiePie"]
答案：Randy Cunningham
理由：逐题审阅最终答案与标准：Randy Cunningham / ["PewDiePie"]；实体、数值、时间或所問字段不一致，维持错误。

### row 792：incorrect
What anchor store in the Stratford Square Mall has 728 department store locations in the continental United States?
标准：["Macy's"]
答案：Sears
理由：逐题审阅最终答案与标准：Sears / ["Macy's"]；实体、数值、时间或所問字段不一致，维持错误。

### row 794：equivalent
Which American actor portray Steve Urkel in "Family Matters"?
标准：["Jaleel Ahmad White"]
答案：Jaleel White
理由：Jaleel White与Jaleel Ahmad White同一演员，省略中间名。

### row 795：incorrect
How much Argentina currency was involved in Boudougate?
标准：["2.3 million pesos"]
答案：120 million new Argentine peso banknotes
理由：逐题审阅最终答案：120 million new Argentine peso banknotes；标准：["2.3 million pesos"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 797：incorrect
Which Royal Air Force is located in a town that had a population of 2,841 on 15 April 2012?
标准：["Mount Pleasant"]
答案：RAF Swanton Morley
理由：逐题审阅最终答案与标准：RAF Swanton Morley / ["Mount Pleasant"]；实体、数值、时间或所問字段不一致，维持错误。

### row 798：incorrect
What did Eric Radomski produce that premiered on Disney XD on May 26, 2013?
标准：["Avengers Assemble"]
答案：Dude, That's My Ghost!
理由：逐题审阅最终答案：Dude, That's My Ghost!；标准：["Avengers Assemble"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 799：incorrect
What Hindi thriller directed by Deepak SHivdasani features choreography by Phulwa Khamkar?
标准：["Julie 2"]
答案：Baadshaho
理由：逐题审阅最终答案与标准：Baadshaho / ["Julie 2"]；实体、数值、时间或所問字段不一致，维持错误。

### row 804：equivalent
Which is the Birthplace of Sir Isaac Newton and has a neighboring village called Belvor?
标准：["Woolsthorpe"]
答案：Woolsthorpe-by-Colsterworth
理由：Woolsthorpe-by-Colsterworth是所问牛顿出生地Woolsthorpe的完整地名。

### row 806：uncertain
The focus city for Israel's third largest airline is located where?
标准：["Tel Aviv"]
答案：Israel
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 809：incorrect
The non-fiction book "Finding Chandra" is about an affair between the victim and a congressman that holds a B.B.A from what school?
标准：["USC Marshall School of Business"]
答案：University of Oklahoma
理由：逐题审阅最终答案与标准：University of Oklahoma / ["USC Marshall School of Business"]；实体、数值、时间或所問字段不一致，维持错误。

### row 811：incorrect
The eastern coast of Ivan Zammit's birth city is located along what body of water?
标准：["Grand Harbour"]
答案：Mediterranean Sea
理由：逐题审阅最终答案：Mediterranean Sea；标准：["Grand Harbour"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 812：equivalent
I Like 'em Big and Stupid was a single whose B-side was played on the show of the record collector specializing in what type of music?
标准：["novelty songs"]
答案：novelty
理由：题目已限定music，novelty与novelty songs为相同音乐类别。

### row 813：uncertain
The Church of the Guanche People was founded in the city that is on the most populated island of what larger area?
标准：["Macaronesia"]
答案：Canary Islands
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 814：incorrect
What country is the Selun located in?
标准：["Switzerland"]
答案：Germany
理由：逐题审阅最终答案：Germany；标准：["Switzerland"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 815：incorrect
Who founded the company that sponsors the CFL game of the week?
标准：["Dave Thomas"]
答案：Gordon Craig
理由：逐题审阅最终答案与标准：Gordon Craig / ["Dave Thomas"]；实体、数值、时间或所問字段不一致，维持错误。

### row 817：label_issue
Who authorized this infantry that was organized in the northern states during the Civil War and was commanded by RObert GOuld Shaw?
标准：["Emancipation Proclamation"]
答案：United States War Department
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 818：incorrect
Which jazz singer has a 2003 album entitled The Boy Next Door?
标准：["Stacey Kent"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 819：incorrect
Stabat Mater was written by a composer of what nationality?
标准：["Polish"]
答案：Italian
理由：逐题审阅最终答案：Italian；标准：["Polish"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 826：incorrect
In which album was American rapper Kendrick Lamar's first number-one single on the US "Billboard" Hot 100 included?
标准：["\"1989\" (2014)"]
答案：Damn
理由：逐题审阅最终答案与标准：Damn / ["\"1989\" (2014)"]。实体、数值、时间或所问字段不一致，维持错误。

### row 827：incorrect
What is the seventh book of the Hebrew and Christina bible and also has Quran references to the river drinking experience?
标准：["Book of Judges"]
答案：Book of Samuel
理由：逐题审阅最终答案与标准：Book of Samuel / ["Book of Judges"]；实体、数值、时间或所問字段不一致，维持错误。

### row 828：incorrect
YouPorn was surpassed, in 2013, by competitor sites xHamster, Pornhub, LiveJasmin, and this website that is registered to the Polish company WGCZ Holding?
标准：["XVideos"]
答案：Pornhub
理由：逐题审阅最终答案与标准：Pornhub / ["XVideos"]；实体、数值、时间或所問字段不一致，维持错误。

### row 829：equivalent
Was Artie Ziff a good prom date for Marge?
标准：["Artie turns out to be a terrible date"]
答案：no
理由：no与标准terrible date直接否定good prom date为同义布尔回答。

### row 833：incorrect
Over how many centuries were the "dwelling place of the dead" built?
标准：["three centuries"]
答案：centuries
理由：逐题审阅最终答案与标准：centuries / ["three centuries"]；实体、数值、时间或所問字段不一致，维持错误。

### row 834：incorrect
Casino and Culto A La Vida are cocktails, one of which contains Havana Club 7 and what else?
标准：["It features Havana Club 7 Añejo Rum and Cranberry juice"]
答案：grenadine
理由：逐题审阅最终答案与标准：grenadine / ["It features Havana Club 7 Añejo Rum and Cranberry juice"]；实体、数值、时间或所問字段不一致，维持错误。

### row 838：incorrect
What film was written and directed by Joby Harold with music written by Samuel Sim?
标准：["Awake"]
答案：Master Harold...and the Boys
理由：逐题审阅最终答案与标准：Master Harold...and the Boys / ["Awake"]；实体、数值、时间或所問字段不一致，维持错误。

### row 840：incorrect
Live Acoustic America features a cover of a Beatles song that peaked at what number in the United Kingdom?
标准：["4"]
答案：number 1
理由：逐题审阅最终答案与标准：number 1 / ["4"]；实体、数值、时间或所問字段不一致，维持错误。

### row 843：equivalent
Sony/Philips Digital Interface Format can transmit over what Toshiba optical fiber connector system?
标准：["TOSLINK (from \"Toshiba Link\") is a standardized optical fiber connector system."]
答案：TOSLINK
理由：TOSLINK直接提取标准长描述中的连接器系统名称。

### row 845：uncertain
Where in Greek mythology was the father of Benthesikyme venerated as a chief deity?
标准：["Pylos and Thebes"]
答案：Greece
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 847：equivalent
What "God Gave Me You" artist wrote the song "Imagine That" for Diamond Rio?
标准：["Bryan Shelton White"]
答案：Bryan White
理由：Bryan White与Bryan Shelton White同一歌手，省略中间名。

### row 849：incorrect
What format does a 1170 kHz AM station that Jim Angel presented the news for have?
标准：["an oldies format"]
答案：Sports Talk
理由：逐题审阅最终答案与标准：Sports Talk / ["an oldies format"]；实体、数值、时间或所問字段不一致，维持错误。

### row 851：incorrect
Which musical group has released more albums, The Telescopes or Candlelight Red?
标准：["Candlelight Red"]
答案：The Telescopes
理由：逐题审阅最终答案：The Telescopes；标准：["Candlelight Red"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 852：incorrect
Who was born earlier, Robert Mulligan or James Foley?
标准：["Robert Patrick Mulligan"]
答案：James Foley
理由：逐题审阅最终答案：James Foley；标准：["Robert Patrick Mulligan"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 853：incorrect
What judge who was on the show "Dancing with the Stars" was born on the 31st of March, 1963?
标准：["Paul Joseph Mercurio"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 854：incorrect
Which Kevin Costner movie included an actor who also starred in "Little Big League"?
标准：["\"Field of Dreams\""]
答案：The Upside of Anger
理由：逐题审阅最终答案与标准：The Upside of Anger / ["\"Field of Dreams\""]；实体、数值、时间或所問字段不一致，维持错误。

### row 855：incorrect
José Baviera starred in the 1962 film by the filmmaker who worked in what countries?
标准：["Spain, Mexico and France"]
答案：Italy
理由：逐题审阅最终答案与标准：Italy / ["Spain, Mexico and France"]；实体、数值、时间或所問字段不一致，维持错误。

### row 856：incorrect
What is the Latin phrase that describes Pope Julius II's efforts to remove Pope Alexander VI's name from the records?
标准：["Damnatio memoriae"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 857：incorrect
Brendon Urie wrote new perspective after firing which bassist?
标准：["Brent Wilson was fired"]
答案：Jon Walker
理由：逐题审阅最终答案：Jon Walker；标准：["Brent Wilson was fired"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 859：incorrect
How high on the US "Billboard" Hot 100 chart did Dan Smith's song reach in 2013?
标准：["number 5"]
答案：four
理由：逐题审阅最终答案与标准：four / ["number 5"]；实体、数值、时间或所問字段不一致，维持错误。

### row 860：incorrect
Which of the city at the south of Shelly Beach, New South Wales is a local government area in the Hunter region of New South Wales, Australia?
标准：["City of Newcastle"]
答案：Shellharbour
理由：逐题审阅最终答案与标准：Shellharbour / ["City of Newcastle"]；实体、数值、时间或所問字段不一致，维持错误。

### row 861：incorrect
How many albums does the duo who sang "Yesterday Once More" have?
标准：["11 albums"]
答案：12
理由：逐题审阅最终答案与标准：12 / ["11 albums"]。实体、数值、时间或所问字段不一致，维持错误。

### row 862：equivalent
The Austrian border barriers at facilities like South Tyrol was designed to designed to manage what?
标准：["people arrived in the European Union"]
答案：the flow of refugees and migrants
理由：轨迹明确边境设施用于control flow of refugees and migrants，与标准到达EU的人流为同一管理对象。

### row 863：incorrect
What number album is the first W.A.S.P. album to feature Steven Edward Duren playing guitar?
标准：["third"]
答案：first
理由：逐题审阅最终答案与标准：first / ["third"]；实体、数值、时间或所問字段不一致，维持错误。

### row 865：equivalent
How many laps did Harry Prowell run during the 10,000 metres race at the 1967 Pan American Games?
标准：["25 laps"]
答案：25
理由：25与25 laps同一圈数。

### row 866：incorrect
What conference does Ralphie the Buffalo's football team play in?
标准：["Pac-12"]
答案：Mid-American Conference
理由：逐题审阅最终答案与标准：Mid-American Conference / ["Pac-12"]。实体、数值、时间或所问字段不一致，维持错误。

### row 867：equivalent
Who wrote more fictional works, Jim Thompson or Theodore H. White?
标准：["Thompson"]
答案：Jim Thompson
理由：Jim Thompson与Thompson在题目限定两位作家中同一人。

### row 868：uncertain
What ranks does Jerry Kyd wear while captaining the largest warship ever built for the Royal Navy?
标准：["Captain while retaining the substantive rank of Commodore"]
答案：captain
理由：captain缺少明确所问ranks的Commodore实衔。

### row 872：uncertain
Both Alexander Hall and Pierre Morel are involved in which profession?
标准：["film director"]
答案：film
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 873：label_issue
WHich college is located in the United States, Grand Valley State University or Carleton University?
标准：["Carleton University"]
答案：Grand Valley State University
理由：轨迹Grand Valley State University在Michigan、Carleton University在Canada；金标准与所问美国学校相反。

### row 875：uncertain
In what country does the director of Shirin in Love, live?
标准：["Iranian"]
答案：Iran
理由：Iranian为国籍形容词，题目问居住国；不把国籍推成居住地Iran。

### row 877：equivalent
When was the actor in the CW show developed by Greg Berlanti who also appears in "Gods and Generals" born?
标准：["1970"]
答案：June 26, 1970
理由：轨迹Matt Letscher明确born June 26, 1970；更细日期与标准1970无冲突。

### row 879：incorrect
Who was the producer of the 1994 American animated epic musical film which Mel Shaw animated?
标准：["Don Hahn"]
答案：Walt Disney Pictures
理由：逐题审阅最终答案与标准：Walt Disney Pictures / ["Don Hahn"]；实体、数值、时间或所問字段不一致，维持错误。

### row 880：incorrect
What year did the series on CBS, starring the actor who known for his role in "Rebel Without a Cause," air?
标准：["1952"]
答案：1974
理由：逐题审阅最终答案与标准：1974 / ["1952"]；实体、数值、时间或所問字段不一致，维持错误。

### row 881：incorrect
Did both Alan Crosland and Chris Columbus work as stage actor?
标准：["no"]
答案：yes
理由：逐题审阅最终答案与标准：yes / ["no"]；实体、数值、时间或所問字段不一致，维持错误。

### row 882：uncertain
How many minutes outside of Carson City is the Moonlite BunnyRanch on Moonlight Road?
标准：["a few minutes"]
答案：1
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 883：incorrect
What British made dance competition television series franchise did Claudia Albertario appear on?
标准：["\"Dancing on Ice\" around the world"]
答案：Strictly Come Dancing
理由：逐题审阅最终答案：Strictly Come Dancing；标准：["\"Dancing on Ice\" around the world"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 884：incorrect
Khushi Ek Roag is broadcast by a company based out of where?
标准：["Dubai"]
答案：Mumbai
理由：逐题审阅最终答案：Mumbai；标准：["Dubai"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 885：uncertain
Die Nacht was composed by German composer, Richard Strauss. What other well known operas did he compose?
标准：["Der Rosenkavalier"]
答案：Elektra
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 886：equivalent
Philip Despencer's brother was a favorite of which king who was deposed in January of 1327?
标准：["King Edward II"]
答案：Edward II
理由：Edward II与King Edward II同一君主，省略头衔。

### row 888：incorrect
Do Bloody Mary and Sidecar share any ingredients in common?
标准：["no"]
答案：lemon juice
理由：逐题审阅最终答案：lemon juice；标准：["no"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 890：incorrect
Which American-Canadian actor starred in the Disney Channel's "Good Luck Charlie, It's Christmas!"?
标准：["Eric Allan Kramer"]
答案：Jason Dolley
理由：逐题审阅最终答案：Jason Dolley；标准：["Eric Allan Kramer"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 892：incorrect
SuperMansion starred the actress who had a recurring role as whom on Workaholics?
标准：["Jillian Belk"]
答案：Leonor
理由：逐题审阅最终答案与标准：Leonor / ["Jillian Belk"]；实体、数值、时间或所問字段不一致，维持错误。

### row 893：incorrect
Phillip Pullman's book set in a parallel universe featuring a character named Lyra Belacqua was put into audio in what year?
标准：["2002"]
答案：2015
理由：逐题审阅最终答案与标准：2015 / ["2002"]；实体、数值、时间或所問字段不一致，维持错误。

### row 894：incorrect
Which American comedian, actor, writer, producer and voice actor from "Hot & Fluffy" voices a character in The Nut Job?
标准：["Gabriel Iglesias"]
答案：Will Arnett
理由：逐题审阅最终答案：Will Arnett；标准：["Gabriel Iglesias"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 895：incorrect
Which British engineering company is best known for its luxury motor cars in the era of British history that covers the brief reign of King Edward VII?
标准：["D. Napier & Son"]
答案：Daimler
理由：逐题审阅最终答案与标准：Daimler / ["D. Napier & Son"]；实体、数值、时间或所問字段不一致，维持错误。

### row 897：incorrect
When was the multinational group headquartered in the Netherlands adjacent to the Junction 27 Retail Park near Birstall, Batley, West Yorkshite, England, founded?
标准：["1943"]
答案：May, 1995
理由：逐题审阅最终答案与标准：May, 1995 / ["1943"]；实体、数值、时间或所問字段不一致，维持错误。

### row 898：incorrect
Which airport, Salt Lake City International Airport or Brainerd Lakes Regional Airport, serves as a commercial airline and is closest to it's respective downtown city?
标准：["Brainerd Lakes Regional Airport"]
答案：Salt Lake City International Airport
理由：逐题审阅最终答案：Salt Lake City International Airport；标准：["Brainerd Lakes Regional Airport"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 903：incorrect
Orlando Maturana had to compete with what other Colombian retired footballer for the national football team's striker position?
标准：["Adolfo José Valencia Mosquera"]
答案：Faustino Asprilla
理由：逐题审阅最终答案：Faustino Asprilla；标准：["Adolfo José Valencia Mosquera"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 905：incorrect
Are David Schwimmer and James Wan in the same industry?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所問字段不一致，维持错误。

### row 907：uncertain
When was the film containing the song "I'm still Here (Jim's Theme)" published?
标准：["November 27, 2002."]
答案：2002
理由：2002省略标准November 27发行日期，保留精度不足。

### row 908：equivalent
The Rome Protocols were signed by three Prime Ministers one of which was assassinated as part of what?
标准：["a failed coup attempt"]
答案：July Putsch
理由：轨迹明确刺杀发生在attempted coup d'état, the July Putsch；事件名与标准事件描述相同。

### row 909：incorrect
What is the company that currently recognizes the sprinting records set by Leni Junker and Florence Griffith-Joyner?
标准：["International Association of Athletics Federations"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 913：incorrect
Queen Elizabeth Grammar School, Wakefield is a type of secondary school that caters to children of what age cohort?
标准：["between 11 or 13 and 18"]
答案：7 to 11
理由：逐题审阅最终答案与标准：7 to 11 / ["between 11 or 13 and 18"]；实体、数值、时间或所問字段不一致，维持错误。

### row 914：uncertain
Arundel Castle was damaged during a war between which two groups?
标准：["Parliamentarians (\"Roundheads\") and Royalists (\"Cavaliers\")"]
答案：Parliamentarians
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 918：equivalent
TimeCamp enables what type of commercial documents from a seller to a buyer?
标准：["invoice"]
答案：invoices
理由：invoices与invoice仅单复数不同，商业单据类型一致。

### row 919：incorrect
How are Ceephax Acid Crew  and Squarepusher's music similar?
标准：["drum and bass electronic musician"]
答案：acid house
理由：逐题审阅最终答案：acid house；标准：["drum and bass electronic musician"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 920：equivalent
Brian Newman's wife performs for what genre of variety show?
标准：["American burlesque"]
答案：burlesque
理由：问题问表演genre，burlesque完整回答类别；American为标准的附加国别。

### row 922：incorrect
When was the  Argentine former footballer which  Dutch manager Ronald Koeman replaced in  2014–15 Southampton F.C. season born?
标准：["2 March 1972"]
答案：29 March 1972
理由：逐题审阅最终答案与标准：29 March 1972 / ["2 March 1972"]；实体、数值、时间或所問字段不一致，维持错误。

### row 923：uncertain
The university where Rolf Martin Theodor Dahlgren worked as a professor has how many employees?
标准：["9,000"]
答案：over 9,000
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 924：incorrect
Who wrote the 1996 American historical drama film in which William Preston appeared?
标准：["Arthur Miller"]
答案：Graham Yost
理由：逐题审阅最终答案与标准：Graham Yost / ["Arthur Miller"]。实体、数值、时间或所问字段不一致，维持错误。

### row 925：incorrect
The rapper whose debut album was titled "Thug Misses" has sold over how many records worldwide?
标准：["2 million"]
答案：over 1 million
理由：逐题审阅最终答案与标准：over 1 million / ["2 million"]；实体、数值、时间或所問字段不一致，维持错误。

### row 926：incorrect
What population ranking is the Oklahoma city located south of a wilderness area spanning over 5000 acres?
标准：["fifth-largest"]
答案：27th
理由：逐题审阅最终答案：27th；标准：["fifth-largest"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 928：incorrect
The 2011–12 Houston Rockets season began with the drafting of the player who now plays for what team?
标准：["Boston Celtics"]
答案：Charlotte Hornets
理由：逐题审阅最终答案与标准：Charlotte Hornets / ["Boston Celtics"]。实体、数值、时间或所问字段不一致，维持错误。

### row 929：equivalent
What type of movie are Wishing Stairs and Voice?
标准：["South Korean horror film"]
答案：horror
理由：问题问电影类型，horror完整回答类型；South Korean为标准的附加国别。

### row 933：incorrect
Wrinkles is a song that was recorded by what American country and Christian country band that was founded in 1982?
标准：["Diamond Rio"]
答案：Atlanta
理由：逐题审阅最终答案：Atlanta；标准：["Diamond Rio"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 934：label_issue
Who was born in August and was a professor?
标准：["Fred MacMurray"]
答案：Jack August
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 937：incorrect
What video game character did the voice actress in the animated film Alpha and Omega voice?
标准：["Kairi in the video game series \"Kingdom Hearts\"."]
答案：Tails
理由：逐题审阅最终答案与标准：Tails / ["Kairi in the video game series \"Kingdom Hearts\"."]；实体、数值、时间或所問字段不一致，维持错误。

### row 940：incorrect
Brahmarshi Vishwamitra is a 1991 film produced & directed by a man that served as Chief Minister of Andhra Pradesh for how many years?
标准：["seven"]
答案：three
理由：逐题审阅最终答案与标准：three / ["seven"]；实体、数值、时间或所問字段不一致，维持错误。

### row 941：incorrect
Which breed of dog came first, the Norrbottenspets or the Blue Lacy?
标准：["Norrbottenspets"]
答案：Blue Lacy
理由：逐题审阅最终答案：Blue Lacy；标准：["Norrbottenspets"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 942：uncertain
Were was the Mexican state after which there is Villa Unión, Sinaloa located?
标准：["tip of the Baja California"]
答案：Northwestern Mexico
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 943：incorrect
Penny Rae Bridges starred in a television sitcom with what other actor?
标准：["Ben Savage"]
答案：Fred Berry
理由：逐题审阅最终答案与标准：Fred Berry / ["Ben Savage"]；实体、数值、时间或所問字段不一致，维持错误。

### row 944：uncertain
What type of elevation does Aldgate railway station, Adelaide and Aldgate, South Australia have in common?
标准：["Hills"]
答案：elevated
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 945：label_issue
In what year did Farda Amiga win a race at the Saratoga Race course?
标准：["(foaled February 1, 1999)"]
答案：2001
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 946：incorrect
A celebrity magazine that has featured Snoop Dogg and footballers such as Riyad Mahrez and the creator's team-mate Juan Mata was launched by which former Manchester United player?
标准：["Ferdinand"]
答案：Brian McClair
理由：逐题审阅最终答案与标准：Brian McClair / ["Ferdinand"]；实体、数值、时间或所問字段不一致，维持错误。

### row 949：incorrect
Who is older, Hampton Del Ruth or Ted Kotcheff?
标准：["Hampton Del Ruth"]
答案：Ted Kotcheff
理由：逐题审阅最终答案与标准：Ted Kotcheff / ["Hampton Del Ruth"]；实体、数值、时间或所問字段不一致，维持错误。

### row 955：incorrect
What group of Elektra Records recording artists are known to be an indie pop band?
标准：["Saint Motel"]
答案：Neutral Milk Hotel
理由：逐题审阅最终答案：Neutral Milk Hotel；标准：["Saint Motel"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 957：uncertain
Carlos Alberto Hurtado played on loan from a mexican team which plays where?
标准：["Estadio Victoria"]
答案：Mexico
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 958：equivalent
What song was created by the group consisting of Jeffrey Jey, Maurizio Lobina and Gabry Ponte and released on 15 January 1999?
标准：["Blue"]
答案：Blue (Da Ba Dee)
理由：Blue (Da Ba Dee)与Blue同一Eiffel 65歌曲的完整名和短名。

### row 961：incorrect
Which of Aaron Goodwin client was born in May 31, 1984?
标准：["Nate Robinson"]
答案：Damian Lillard
理由：逐题审阅最终答案与标准：Damian Lillard / ["Nate Robinson"]；实体、数值、时间或所問字段不一致，维持错误。

### row 962：uncertain
Who were the live-in lovers of the founder of "Playboy" magazine in 1999 and 2000?
标准：["Bentley Twins"]
答案：Sandy Bentley
理由：Sandy Bentley仅给Bentley Twins之一，复数对象未答全。

### row 964：incorrect
Which American Space Western animated series did Celebrity Home Entertainment released?
标准：["BraveStarr"]
答案：Saber Rider and the Star Sheriffs
理由：逐题审阅最终答案与标准：Saber Rider and the Star Sheriffs / ["BraveStarr"]。实体、数值、时间或所问字段不一致，维持错误。

### row 965：incorrect
Taylor Momsen and Craig Mabbitt from Escape the Fate have what in common?
标准：["lead singer"]
答案：Escape the Fate
理由：逐题审阅最终答案与标准：Escape the Fate / ["lead singer"]；实体、数值、时间或所問字段不一致，维持错误。

### row 967：equivalent
Where are Catcha Lake and Hedley Mascot Mine located?
标准：["British Columbia, Canada"]
答案：British Columbia
理由：British Columbia与British Columbia, Canada同一省份，省略国家。

### row 968：incorrect
What trio was the songwriter of "What Are We Doin' Lonesome" from?
标准：["trio with his younger brothers Steve and Rudy"]
答案：JaR
理由：逐题审阅最终答案与标准：JaR / ["trio with his younger brothers Steve and Rudy"]；实体、数值、时间或所問字段不一致，维持错误。

### row 970：uncertain
Who wrote the jukebox musical depicting the recording session between the "King of Rock and Roll" and 3 other famous musicians?
标准：["Floyd Mutrux and Colin Escott"]
答案：Colin Escott
理由：Colin Escott只给两位作者之一，Floyd Mutrux遗漏。

### row 972：incorrect
What was the first comic book written by the writer who had a series developed into a 2010 film with Bruce Willis and Morgan Freeman?
标准：["Transmetropolitan"]
答案：The Authority
理由：逐题审阅最终答案与标准：The Authority / ["Transmetropolitan"]；实体、数值、时间或所問字段不一致，维持错误。

### row 973：incorrect
Who is the former pentecostal preacher who released the comedy album Leader of the Banned in 1990?
标准：["Sam Kinison"]
答案：Mike Warnke
理由：逐题审阅最终答案与标准：Mike Warnke / ["Sam Kinison"]。实体、数值、时间或所问字段不一致，维持错误。

### row 975：equivalent
Which record label released Van Morrison's "I've Been Working" on the album "His Band and the Street Choir"?
标准：["Warner Bros"]
答案：Warner Bros. Records
理由：Warner Bros. Records与Warner Bros在唱片厂牌问题下同一机构。

### row 976：incorrect
Why is Minister Pool important to Black Country and the West Midlands in England?
标准：["defence of the Cathedral"]
答案：Black Country
理由：逐题审阅最终答案与标准：Black Country / ["defence of the Cathedral"]；实体、数值、时间或所問字段不一致，维持错误。

### row 978：equivalent
Oklahoma State Cowboys are part of what NCAA Division?
标准：["NCAA Division I"]
答案：Division I
理由：题目限定NCAA，Division I与NCAA Division I为相同大学体育组别。

### row 979：incorrect
What musician is ranked 9th in the Top 100 Greatest Metal Guitarists and started a band in 1990 in Los Angeles, California?
标准：["Adam Thomas Jones"]
答案：Kirk Hammett
理由：逐题审阅最终答案：Kirk Hammett；标准：["Adam Thomas Jones"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 980：equivalent
What city is home to the private research university Jung Seul-ki swam for?
标准：["Seoul, South Korea"]
答案：Seoul
理由：题目只问city，Seoul完整回答Seoul, South Korea中的城市。

### row 984：incorrect
This British television series was adapted from one of the better-known novels of a 19th-century writer and was first published in what magazine?
标准：["Household Words"]
答案：Athenaeum
理由：逐题审阅最终答案与标准：Athenaeum / ["Household Words"]；实体、数值、时间或所問字段不一致，维持错误。

### row 986：incorrect
Kevin Watson currently manages which Southern League football team?
标准：["Bishop's Stortford"]
答案：Maldon &amp; Tiptree
理由：逐题审阅最终答案与标准：Maldon &amp; Tiptree / ["Bishop's Stortford"]；实体、数值、时间或所問字段不一致，维持错误。

### row 987：incorrect
Which one between Milium and Eucommia lives more widely spread across the world?
标准：["Milium"]
答案：Eucommia
理由：逐题审阅最终答案与标准：Eucommia / ["Milium"]；实体、数值、时间或所問字段不一致，维持错误。

### row 988：incorrect
Salisbury Woodland Gardens links a zoo with a park designed and built under the watchful eye of who?
标准：["Thomas Mawson"]
答案：Peter Perry
理由：逐题审阅最终答案与标准：Peter Perry / ["Thomas Mawson"]；实体、数值、时间或所問字段不一致，维持错误。

### row 989：incorrect
Who else besides "The Golden Jet" was born in Point Anne, Ontario?
标准：["Dennis Hull, as well as painter Manley MacDonald."]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 990：equivalent
Jessica Ashley has recorded her own songs and has also written songs for which singer known for her song "Leave (Get Out)"?
标准：["Joanna Noëlle Levesque"]
答案：JoJo
理由：JoJo与Joanna Noëlle Levesque同一歌手的艺名和本名。

### row 992：uncertain
What was the former name of the company which operates Hunterston Terminal?
标准：["Peel Holdings"]
答案：The Peel Group
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 995：incorrect
What is another name for the butterfly of the Hesperiidae family that is found in the third largest country in Africa?
标准：["the buff-tipped skipper"]
答案：African Grass Yellow
理由：逐题审阅最终答案与标准：African Grass Yellow / ["the buff-tipped skipper"]；实体、数值、时间或所問字段不一致，维持错误。

### row 997：incorrect
Petroglyphs on Ingaro isalnd indicate it has been innhabited since an era that lasted until what year?
标准：["500 BC"]
答案：500 AD
理由：逐题审阅最终答案与标准：500 AD / ["500 BC"]；实体、数值、时间或所問字段不一致，维持错误。

### row 998：incorrect
Where did Ian Harland study prior to studying at the oldest college at the University of Cambridge?
标准：["The Dragon School in Oxford"]
答案：Haileybury
理由：逐题审阅最终答案：Haileybury；标准：["The Dragon School in Oxford"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 999：incorrect
Which team featured in both the 2012 and 2011 Cops del Rey Finals ?
标准：["Barcelona"]
答案：Real Madrid
理由：逐题审阅最终答案与标准：Real Madrid / ["Barcelona"]；实体、数值、时间或所問字段不一致，维持错误。

### row 1001：incorrect
The Bodie & Benton Railway was a narrow gauge common carrier railroad in California, from the Mono Mills to a terminus in a ghost town located how many miles away from Lake Tahoe ?
标准：["75 mi"]
答案：32
理由：逐题审阅最终答案：32；标准：["75 mi"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1002：incorrect
What was the original name of the female singing group that recorded "The Happening"?
标准：["The Primettes"]
答案：The Supremes
理由：逐题审阅最终答案：The Supremes；标准：["The Primettes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1003：incorrect
For which team does Mads Bødker player that is controlled by Danmarks Ishockey Union?
标准：["Denmark men's national ice hockey"]
答案：SønderjyskE Ishockey
理由：逐题审阅最终答案：SønderjyskE Ishockey；标准：["Denmark men's national ice hockey"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1007：incorrect
What actor played the male lead in a teen comedy about a high school nerd directed by Steve Rash?
标准：["Patrick Dempsey"]
答案：Eric Christian Olsen
理由：逐题审阅最终答案与标准：Eric Christian Olsen / ["Patrick Dempsey"]；实体、数值、时间或所問字段不一致，维持错误。

### row 1008：equivalent
Richford is a town in Franklin County Vermont governed by what kind of body?
标准：["town meeting legislative body"]
答案：town meeting
理由：town meeting与town meeting legislative body同一治理机构，省略职能修饰。

### row 1011：uncertain
What three categories does income get levied under the Parliament of Australia's tax code?
标准：["\"personal earnings\" (such as salary and wages), \"business income\" and \"capital gains\""]
答案：personal earnings
理由：personal earnings只给明确所问三类收入之一。

### row 1013：label_issue
From 2015 to 2016, Jill Marie Jones starred in a Starz horror-comedy series set in the "Evil Dead" universe created by who?
标准：["Ivan Raimi"]
答案：Sam Raimi
理由：轨迹列Sam Raimi、Ivan Raimi、Tom Spezialy共同开发剧集；Sam与Ivan不是别名，合法替代作者单列。

### row 1015：incorrect
What Andy Williams' album did a song written by Charles Wesley appear on?
标准：["The Andy Williams Christmas Album"]
答案：None
理由：未交出合法最终答案，不从think或工具文段补出答案。

### row 1016：incorrect
Where does Yannick Ferreira Carrasco play home games?
标准：["Wanda Metropolitano"]
答案：Dalian Sports Center Stadium
理由：逐题审阅最终答案：Dalian Sports Center Stadium；标准：["Wanda Metropolitano"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1017：equivalent
What role in the TV show "Death in Paradise" was played by the man who performed with Alexander Armstrong in the podcast "Timeghost"?
标准：["Richard Poole"]
答案：DI Richard Poole
理由：DI Richard Poole与Richard Poole同一角色，附加警衔。

### row 1018：equivalent
John E. EchoHawk is a leading member in a social movement that wants to reverse what ?
标准：["the paternalistic policies enacted upon Native American tribes"]
答案：federal policy favoring control
理由：在原住民自主权运动语境中，federal policy favoring control指标准对部落实行的paternalistic policies；描述同一政策控制目标。

### row 1021：incorrect
Brinckerhoff, New Yorkhad a role in a CBS sitcom created by whom?
标准：["Justin Adler"]
答案：David Crane
理由：逐题审阅最终答案：David Crane；标准：["Justin Adler"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1022：incorrect
Are both Viken Babikian and Don Manoukian American ?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所問字段不一致，维持错误。
