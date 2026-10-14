# T1024语义复核：official_ppo_v02

标准：T1024-equivalence-v1

原始EM不变；只对明确等价的最终答案加分。标签错误、歧义、缺关键字段不计新增正确。

{
  "model": "official_ppo_v02",
  "policy": "T1024-equivalence-v1",
  "evaluation_complete": true,
  "review_complete": true,
  "n": 1024,
  "original_correct": 485,
  "equivalent_added": 141,
  "incorrect": 307,
  "uncertain": 77,
  "label_issue": 14,
  "pending": 0,
  "original_em": 0.4736328125,
  "semantic_correct_confirmed": 626,
  "semantic_accuracy": 0.611328125,
  "records_digest": "7b67158adb4e32efb0ce97582cbf8ac35e752785e45181d0335f8c7dcee6d1fe",
  "sources": {
    "nq": {
      "n": 335,
      "original_correct": 178,
      "semantic_correct": 209
    },
    "hotpotqa": {
      "n": 689,
      "original_correct": 307,
      "semantic_correct": 417
    }
  }
}

## EM错题逐项裁定

### row 0：incorrect
how many episodes are in chicago fire season 4?
标准：["23"]
答案：22
理由：逐题审阅最终答案与标准：22 / ["23"]；实体、数值、时间或所问字段不一致，维持错误。

### row 3：uncertain
wal-mart is a prime example of which type organization?
标准：["multinational retail corporation"]
答案：retail corporation
理由：retail corporation遗漏标准multinational限定，组织类别相近但未确认完整等价，不加分。

### row 5：incorrect
what is the highest base on the ph scale?
标准：["greater than 14"]
答案：14
理由：逐题审阅最终答案：14；标准：["greater than 14"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：the name of its present capital and patron saint, Saint Dominic
理由：最终答案明确指出名称来自patron saint Saint Dominic，与标准名称来源一致，补充首都名称语境。

### row 26：incorrect
who has majority in the house and senate?
标准：["Republican"]
答案：Republican Party
理由：逐题审阅最终答案：Republican Party；标准：["Republican"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 31：incorrect
list of strict nature reserve in the philippines?
标准：["Palawan", "Lake Malimanga", "Olango Island", "Calauit Safari Park", "Lake Buluan", "Calavite and FB Harrison"]
答案：Biosphere reserves of the Philippines
理由：逐题审阅最终答案与标准：Biosphere reserves of the Philippines / ["Palawan", "Lake Malimanga", "Olango Island", "Calauit Safari Park", "Lake Buluan", "Calavite and FB Harrison"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Rashida Jones
理由：逐题审阅最终答案与标准：Rashida Jones / ["Surprised Who"]；实体、数值、时间或所问字段不一致，维持错误。

### row 39：incorrect
who was the declaration of independence written for?
标准：["the Second Continental Congress"]
答案：the people
理由：逐题审阅最终答案与标准：the people / ["the Second Continental Congress"]；实体、数值、时间或所问字段不一致，维持错误。

### row 40：incorrect
what disney cartoon character's middle name is fauntleroy?
标准：["Donald Duck", "Donald Fauntleroy Duck"]
答案：Little Lord Fauntleroy
理由：逐题审阅最终答案与标准：Little Lord Fauntleroy / ["Donald Duck", "Donald Fauntleroy Duck"]；实体、数值、时间或所問字段不一致，维持错误。

### row 42：incorrect
communities of similar organisms found in a particular environment are called?
标准：["species", "habitat"]
答案：biomes
理由：逐题审阅最终答案与标准：biomes / ["species", "habitat"]；实体、数值、时间或所问字段不一致，维持错误。

### row 48：uncertain
who died in the first episode of stranger things?
标准：["Benny"]
答案：the owner
理由：the owner未说明哪位店主，角色描述不足以唯一确定标准Benny。

### row 49：incorrect
when did equus first appear in fossil record?
标准：["1820s", "~3.5 million years old", "about 3.5 mya"]
答案：early Eocene
理由：逐题审阅最终答案与标准：early Eocene / ["1820s", "~3.5 million years old", "about 3.5 mya"]；实体、数值、时间或所问字段不一致，维持错误。

### row 52：equivalent
where is wake forest located in north carolina?
标准：["78.51889°W", "in Franklin and Wake counties", "35.97333°N"]
答案：Franklin and Wake counties
理由：Franklin and Wake counties与标准in Franklin and Wake counties为同一地点，仅省略介词。

### row 55：incorrect
what episode does goku give up against cell?
标准：["165", "180"]
答案：28
理由：逐题审阅最终答案与标准：28 / ["165", "180"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 62：incorrect
when did the broncos win the super bowl?
标准：["1998", "2015", "1997"]
答案：1977
理由：逐题审阅最终答案与标准：1977 / ["1998", "2015", "1997"]。实体、数值、时间或所问字段不一致，维持错误。

### row 65：uncertain
what was the tower of london originally used for?
标准：["a royal residence", "as a royal residence"]
答案：fortress
理由：fortress与royal residence表达不同用途；伦敦塔兼具多种功能，不能据关联判成同义。

### row 68：equivalent
where are they playing the superbowl at this year?
标准：["Minneapolis, Minnesota"]
答案：U.S. Bank Stadium
理由：U.S. Bank Stadium位于标准Minneapolis, Minnesota，为所问比赛地点的具体球场，地点相容。

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
答案：10
理由：逐题审阅最终答案与标准：10 / ["18"]。实体、数值、时间或所问字段不一致，维持错误。

### row 84：equivalent
where is a simple gear train used in real life?
标准：["Automobile drivetrains"]
答案：automobile manual transmission
理由：automobile manual transmission为汽车传动系统的具体组成及齿轮传动应用，符合标准Automobile drivetrains所述汽车传动应用。

### row 87：incorrect
who plays charles on have and have nots?
标准：["Nick Sager", "Nick Sagar"]
答案：Peter Parros
理由：逐题审阅最终答案：Peter Parros；标准：["Nick Sager", "Nick Sagar"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 90：equivalent
which animal is the carrier of the h1n1 virus?
标准：["Pig", "pigs"]
答案：swine
理由：swine与pigs同义，所问病毒动物载体一致。

### row 93：incorrect
what is the spelling of lakh in english?
标准：["lakh"]
答案：L
理由：逐题审阅最终答案与标准：L / ["lakh"]；实体、数值、时间或所问字段不一致，维持错误。

### row 94：uncertain
where does the red river start and end in louisiana?
标准：["the Texas Panhandle"]
答案：Atchafalaya River
理由：答案给河流终点而标签给起点；问题问起止两处，未提供标准起点，不加分。

### row 95：equivalent
who invented the first home video security system?
标准：["her husband Albert Brown", "Marie Van Brittan Brown"]
答案：Marie Brown
理由：轨迹明确该安全系统发明者称Marie Brown；与Marie Van Brittan Brown同一人。

### row 96：incorrect
when did michigan last win a national championship?
标准：["1989"]
答案：1997
理由：逐题审阅最终答案与标准：1997 / ["1989"]；实体、数值、时间或所问字段不一致，维持错误。

### row 99：incorrect
who did the dominican republic gain its independence from?
标准：["Haiti"]
答案：Spain
理由：逐题审阅最终答案：Spain；标准：["Haiti"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 101：incorrect
when was you'll never walk alone first released?
标准：["1945"]
答案：1963
理由：逐题审阅最终答案：1963；标准：["1945"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 103：incorrect
active absorption of water from the soil by the root is mainly affected by?
标准：["SURFACE AREA OF ROOTS", "ATP"]
答案：mechanism of water absorption
理由：逐题审阅最终答案与标准：mechanism of water absorption / ["SURFACE AREA OF ROOTS", "ATP"]；实体、数值、时间或所问字段不一致，维持错误。

### row 105：equivalent
who took part in the american civil war?
标准：["nationalists of the Union"]
答案：the Union
理由：the Union在南北战争参战方问题中对应标准nationalists of the Union所指联邦一方。

### row 107：equivalent
who became king of erebor after thorin dies?
标准：["Dáin", "his cousin Dáin"]
答案：Dáin Ironfoot
理由：Dáin Ironfoot与Dáin为同一角色的完整名和短名。

### row 112：incorrect
what is the rank of india in economic growth?
标准：["12 / 225", "12"]
答案：sixth-largest
理由：逐题审阅最终答案：sixth-largest；标准：["12 / 225", "12"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 114：incorrect
ajay devgan preity zinta and madhuri dixit movie?
标准：["Yeh Raaste Hain Pyaar Ke"]
答案：Total Dhamaal
理由：逐题审阅最终答案与标准：Total Dhamaal / ["Yeh Raaste Hain Pyaar Ke"]。实体、数值、时间或所问字段不一致，维持错误。

### row 118：incorrect
who did the chiefs play in the playoffs?
标准：["the Tennessee Titans"]
答案：Houston Texans
理由：逐题审阅最终答案：Houston Texans；标准：["the Tennessee Titans"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 119：uncertain
how much is a 72 oz steak at the big texan?
标准：["$72"]
答案：free
理由：free仅在限时吃完挑战等条件下成立，不能等同未限定条件的标价72美元。

### row 120：incorrect
where will the first round of march madness be played?
标准：["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]
答案：University of Dayton Arena
理由：逐题审阅最终答案与标准：University of Dayton Arena / ["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]；实体、数值、时间或所问字段不一致，维持错误。

### row 121：uncertain
where can you find convergent boundaries on earth?
标准：["Mariana Trench"]
答案：at the edges of tectonic plates
理由：板块边缘过宽，未给出标准Mariana Trench这一具体位置。

### row 123：uncertain
what is the central idea of the poem the rime of ancient mariner?
标准：["a violation of nature"]
答案：sin and redemption
理由：sin and redemption与标准violation of nature主题有关，但未表达自然被侵犯这一关键内容，暂不加分。

### row 124：equivalent
what is katie running from in safe haven?
标准：["her abusive husband"]
答案：her abusive and alcoholic husband
理由：her abusive and alcoholic husband明确保留标准her abusive husband，附加相容描述。

### row 125：incorrect
who plays the mouse in alice in wonderland?
标准：["Barbara Windsor"]
答案：Crispin Glover
理由：逐题审阅最终答案与标准：Crispin Glover / ["Barbara Windsor"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Edinburgh, Scotland
理由：Edinburgh, Scotland与in Edinburgh, Scotland仅介词不同。

### row 142：incorrect
what is the job of the whip in congress?
标准：["to ensure party discipline"]
答案：keep track of all legislation
理由：逐题审阅最终答案与标准：keep track of all legislation / ["to ensure party discipline"]；实体、数值、时间或所问字段不一致，维持错误。

### row 146：incorrect
who carried the usa flag in opening ceremony?
标准：["Erin Hamlin"]
答案：Dawn Staley
理由：逐题审阅最终答案：Dawn Staley；标准：["Erin Hamlin"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 152：equivalent
what kind of book is where's waldo?
标准：["puzzle"]
答案：puzzle book
理由：puzzle book与puzzle在书籍类型问题中同义，附加类别单位。

### row 153：incorrect
who sang oh annie i not your daddy?
标准：["Kid Creole and the Coconuts", "Kid Creole & The Coconuts"]
答案：Hank Ballard & the Midnighters
理由：逐题审阅最终答案：Hank Ballard & the Midnighters；标准：["Kid Creole and the Coconuts", "Kid Creole & The Coconuts"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 155：incorrect
ben 10 ultimate alien episode 2 season 1?
标准：["Duped"]
答案：The Ultimate Enemy
理由：逐题审阅最终答案与标准：The Ultimate Enemy / ["Duped"]；实体、数值、时间或所问字段不一致，维持错误。

### row 157：incorrect
who played the music producer in pitch perfect 2?
标准：["Keegan-Michael Key"]
答案：Max Martin
理由：逐题审阅最终答案与标准：Max Martin / ["Keegan-Michael Key"]；实体、数值、时间或所问字段不一致，维持错误。

### row 158：incorrect
for complaints of sudden chest pain patients should take a?
标准：["Aspirin"]
答案：medication
理由：逐题审阅最终答案：medication；标准：["Aspirin"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 159：incorrect
who sang last night on saturday night live?
标准：["Childish Gambino"]
答案：The Weeknd
理由：逐题审阅最终答案：The Weeknd；标准：["Childish Gambino"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 163：uncertain
when did the nba add the three point line?
标准：["1979–80", "1979–80 season", "the 1979–80 season"]
答案：1979
理由：1979未完整给出1979–80赛季区间，按共同日期精度标准保留争议，不加分。

### row 164：incorrect
who wins the final fight in real steel?
标准：["Zeus"]
答案：Atom
理由：逐题审阅最终答案：Atom；标准：["Zeus"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 165：equivalent
who abolished the monarchy and declared france a republic?
标准：["Convention", "France's Legislative Assembly"]
答案：National Convention
理由：National Convention是标准Convention的完整机构名。

### row 166：uncertain
where does water come from in new york city?
标准：["The Catskill Aqueduct", "The Delaware Aqueduct", "The New Croton Aqueduct"]
答案：Catskill Mountains watershed
理由：Catskill Mountains watershed为水源区，标准为输水设施名称，相关但非同一对象。

### row 167：incorrect
who played ice queen in chronicles of narnia?
标准：["Tilda Swinton", "Laura Brent"]
答案：Anna Popplewell
理由：逐题审阅最终答案与标准：Anna Popplewell / ["Tilda Swinton", "Laura Brent"]；实体、数值、时间或所问字段不一致，维持错误。

### row 168：uncertain
who is the writer of a walk to remember?
标准：["American writer Nicholas Sparks", "Nicholas Sparks"]
答案：Karen Janszen
理由：Karen Janszen为电影编剧，标签为小说作者Nicholas Sparks；媒介版本有歧义，人物不同，不按别名加分。

### row 172：equivalent
where was 2017 beauty and the beast filmed?
标准：["Surrey, United Kingdom"]
答案：Shepperton Studios
理由：轨迹明确拍摄在Shepperton Studios in Surrey, England；回答具体拍摄场地，与标准地点相容且更具体。

### row 176：incorrect
when did indoor toilets become common in america?
标准：["After World War I"]
答案：1890
理由：逐题审阅最终答案：1890；标准：["After World War I"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 178：incorrect
who has won the most united states championships?
标准：["Lex Luger", "Ric Flair"]
答案：Pete Sampras
理由：逐题审阅最终答案：Pete Sampras；标准：["Lex Luger", "Ric Flair"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Anthony McPartlin
理由：Anthony McPartlin未答完整的Ant & Dec搭档。

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

### row 195：equivalent
where do the secretory cells of endocrine glands secrete their products?
标准：["epithelial surface", "bloodstream", "directly into the bloodstream"]
答案：directly into the blood stream
理由：directly into the blood stream与directly into the bloodstream为同一分泌位置，bloodstream拼写空格差异。

### row 197：incorrect
who is the head a in pretty little liars?
标准：["CeCe Drake"]
答案：Alison DiLaurentis
理由：逐题审阅最终答案与标准：Alison DiLaurentis / ["CeCe Drake"]；实体、数值、时间或所问字段不一致，维持错误。

### row 199：uncertain
what are the 5 prohibitions of yom kippur?
标准：["No marital relations", "No wearing of leather shoes", "No eating and drinking", "No bathing or washing"]
答案：refraining from food and drink
理由：题目明确要求五项禁令，最终只给禁食禁饮，缺少其余字段，不加分。

### row 200：incorrect
what was the first light beer in the us?
标准：["Miller Lite"]
答案：Bud Light
理由：逐题审阅最终答案与标准：Bud Light / ["Miller Lite"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 208：incorrect
a player that can shoot pass or dribble is considered to be?
标准：["Triple threat"]
答案：basketball player
理由：逐题审阅最终答案与标准：basketball player / ["Triple threat"]；实体、数值、时间或所问字段不一致，维持错误。

### row 211：incorrect
what level is a city and guilds qualification?
标准：["entry level to level 7"]
答案：level 2 or 3
理由：逐题审阅最终答案：level 2 or 3；标准：["entry level to level 7"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 215：incorrect
where was held the first session of muslim league?
标准：["Dhaka, Bangladesh", "Lucknow"]
答案：All India Muhammadan Educational Conference
理由：逐题审阅最终答案与标准：All India Muhammadan Educational Conference / ["Dhaka, Bangladesh", "Lucknow"]；实体、数值、时间或所问字段不一致，维持错误。

### row 217：incorrect
who sings what the world needs now in boss baby?
标准：["Missi Hale", "Steve Mazzaro", "Hans Zimmer"]
答案：Jackie DeShannon
理由：逐题审阅最终答案：Jackie DeShannon；标准：["Missi Hale", "Steve Mazzaro", "Hans Zimmer"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 223：incorrect
when was the cleveland browns last winning game?
标准：["2016"]
答案：2017
理由：逐题审阅最终答案与标准：2017 / ["2016"]。实体、数值、时间或所问字段不一致，维持错误。

### row 224：incorrect
who is in charge of new issues not mentioned in the constitution?
标准：["Congress"]
答案：the judiciary
理由：逐题审阅最终答案与标准：the judiciary / ["Congress"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：December 10, 2006
理由：逐题审阅最终答案与标准：December 10, 2006 / ["September 9, 2012"]；实体、数值、时间或所问字段不一致，维持错误。

### row 236：equivalent
the secret of crickley hall how many episodes?
标准：["3"]
答案：three
理由：three与3是相同数量。

### row 238：equivalent
where was the first nhl hockey game played?
标准：["Ottawa", "Montreal"]
答案：Montreal, Quebec, Canada
理由：Montreal, Quebec, Canada保留标准Montreal实体，并补充地理说明。

### row 239：incorrect
which president of the united states was a boy scout?
标准：["Gerald Ford", "President Gerald Ford"]
答案：Theodore Roosevelt
理由：逐题审阅最终答案：Theodore Roosevelt；标准：["Gerald Ford", "President Gerald Ford"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 241：incorrect
what is the most common blood type in sweden?
标准：["A+", "AB+"]
答案：O+
理由：逐题审阅最终答案与标准：O+ / ["A+", "AB+"]；实体、数值、时间或所问字段不一致，维持错误。

### row 242：uncertain
when did the first battle of ypres end?
标准：["22 November 1914"]
答案：November 1914
理由：November 1914省略标准22日，保留精度不足。

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
答案：Abaya
理由：逐题审阅最终答案：Abaya；标准：["hijab"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 254：equivalent
theme of the song roar by katy perry?
标准：["self-empowerment", "standing up for oneself"]
答案：standing up for oneself and self-empowerment
理由：最终答案把标准允许的self-empowerment与standing up for oneself组合表述。

### row 256：equivalent
what was the emperor name in star wars?
标准：["Darth Sidious", "Sheev Palpatine"]
答案：Palpatine
理由：Palpatine与Sheev Palpatine在Star Wars皇帝语境下为同一角色。

### row 259：uncertain
where is the oldest civilization known to man?
标准：["Mesopotamia"]
答案：Sumer
理由：Sumer为Mesopotamia中的文明地区，范围相关但非同一地理名称。

### row 261：incorrect
name three large lakes other than the great lakes in the united states?
标准：["Iliamna Lake", "Great Salt Lake", "Lake of the Woods"]
答案：Lake Tahoe
理由：逐题审阅最终答案：Lake Tahoe；标准：["Iliamna Lake", "Great Salt Lake", "Lake of the Woods"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 263：equivalent
where was the u.s.s maine when it exploded in 1898?
标准：["Havana Harbor"]
答案：Havana harbor, Cuba
理由：Havana harbor, Cuba与Havana Harbor同一港口，附加国家名。

### row 270：incorrect
who sings so come and dance with me jai ho?
标准：["Mahalaxmi Iyer", "Vijay Prakash", "Tanvi Shah", "Sukhvinder Singh"]
答案：The Pussycat Dolls
理由：逐题审阅最终答案：The Pussycat Dolls；标准：["Mahalaxmi Iyer", "Vijay Prakash", "Tanvi Shah", "Sukhvinder Singh"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 273：incorrect
where does half life 2 episode 2 take place?
标准：["outside City 17"]
答案：war-torn City 17
理由：逐题审阅最终答案与标准：war-torn City 17 / ["outside City 17"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 278：incorrect
tools made from high-speed tool steel are generally used for what type of machining operations?
标准：["milling"]
答案：cutting tools
理由：逐题审阅最终答案：cutting tools；标准：["milling"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 279：uncertain
when does season 3 of the riveras start?
标准：["March 11, 2018"]
答案：2018
理由：2018省略标准March 11日期，保留精度不足。

### row 282：incorrect
who lived in jamestown before the arrival of the english?
标准：["uninhabited"]
答案：Paspahegh people
理由：逐题审阅最终答案与标准：Paspahegh people / ["uninhabited"]；实体、数值、时间或所问字段不一致，维持错误。

### row 283：incorrect
nearest metro station to gandhi nagar in delhi?
标准：["Shastri Park metro station"]
答案：Adarsh Nagar
理由：逐题审阅最终答案与标准：Adarsh Nagar / ["Shastri Park metro station"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 288：incorrect
when was the last time the jets won a playoff game?
标准：["2010"]
答案：2018
理由：逐题审阅最终答案与标准：2018 / ["2010"]。实体、数值、时间或所问字段不一致，维持错误。

### row 291：equivalent
who got the first nobel prize in physics?
标准：["Wilhelm Conrad Röntgen"]
答案：Wilhelm Röntgen
理由：Wilhelm Röntgen与Wilhelm Conrad Röntgen是同一人，省略中间名。

### row 292：uncertain
when did lynyrd skynyrd's plane crash happen?
标准：["October 20, 1977"]
答案：1977
理由：1977省略标准October 20日期，保留精度不足。

### row 298：uncertain
which central american nations border the pacific ocean and the caribbean sea?
标准：["Nicaragua", "Costa Rica"]
答案：Panama
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 299：equivalent
where did the name huey helicopter come from?
标准：["originally designated HU-1"]
答案：HU-1
理由：HU-1直接给出标准originally designated HU-1中所问Huey名称来源。

### row 302：incorrect
nodding your head no is an example of?
标准：["a gesture"]
答案：disagreement
理由：逐题审阅最终答案与标准：disagreement / ["a gesture"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 305：equivalent
who shot first in the shot heard around the world?
标准：["Americans acting under orders"]
答案：Americans
理由：Americans与标准Americans acting under orders指同一开枪方；问题问哪方，省略命令状态未改变所答群体。

### row 306：label_issue
where did the ashes from ash wednesday originate?
标准：["Pope Gregory I the Great"]
答案：burning palm branches
理由：问题问灰烬来源，标签给Pope Gregory I人名，答案给燃烧棕榈枝材料；标签字段疑误单列，不擅自替换。

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

### row 313：incorrect
where will the next summer and winter olympics be held?
标准：["Beijing", "Tokyo"]
答案：Los Angeles, California, United States
理由：逐题审阅最终答案与标准：Los Angeles, California, United States / ["Beijing", "Tokyo"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：president judge
理由：逐题审阅最终答案与标准：president judge / ["District Judge"]；实体、数值、时间或所问字段不一致，维持错误。

### row 319：incorrect
legislation regarding data protection and security in uk?
标准：["The Data Protection Act 1998", "Data Protection Act 1998"]
答案：Data Protection Act 2018
理由：逐题审阅最终答案：Data Protection Act 2018；标准：["The Data Protection Act 1998", "Data Protection Act 1998"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 320：incorrect
when did the first immigrants come to hawaii?
标准：["Around 1200"]
答案：1789
理由：逐题审阅最终答案与标准：1789 / ["Around 1200"]；实体、数值、时间或所问字段不一致，维持错误。

### row 323：incorrect
what is the definition of the word hosanna?
标准：["save, rescue, savior", "rescue", "savior", "save"]
答案：a liturgical word
理由：逐题审阅最终答案与标准：a liturgical word / ["save, rescue, savior", "rescue", "savior", "save"]；实体、数值、时间或所问字段不一致，维持错误。

### row 326：incorrect
what is the salary of the ceo of microsoft?
标准：["$84.3 million", "$84.3 million (2018)"]
答案：$18 million
理由：逐题审阅最终答案：$18 million；标准：["$84.3 million", "$84.3 million (2018)"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 327：incorrect
when did gimme gimme gimme start?
标准：["8 January 1999", "1999"]
答案：1979
理由：逐题审阅最终答案与标准：1979 / ["8 January 1999", "1999"]；实体、数值、时间或所问字段不一致，维持错误。

### row 328：incorrect
how long has tom brady been the patriots quarterback?
标准：["2001", "16 seasons"]
答案：18 seasons
理由：逐题审阅最终答案：18 seasons；标准：["2001", "16 seasons"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 329：incorrect
architectural elements forming rib vaults eg wells cathedral?
标准：["an armature of piped masonry", "barrel vaults", "two to three barrel vaults"]
答案：Wells Cathedral
理由：逐题审阅最终答案与标准：Wells Cathedral / ["an armature of piped masonry", "barrel vaults", "two to three barrel vaults"]；实体、数值、时间或所问字段不一致，维持错误。

### row 331：incorrect
when was the last easter fell on april 1?
标准：["2018"]
答案：1943
理由：逐题审阅最终答案与标准：1943 / ["2018"]；实体、数值、时间或所问字段不一致，维持错误。

### row 332：incorrect
south african tree with thorns on the trunk?
标准：["silk floss tree"]
答案：Buffalo thorn
理由：逐题审阅最终答案与标准：Buffalo thorn / ["silk floss tree"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Chaves
理由：逐题审阅最终答案：Chaves；标准：["Rooster"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 344：incorrect
Who wrote the book that inspired the name of the CD/DVD "Here at the End of All Things"?
标准：["J. R. R. Tolkien"]
答案：Stephen King
理由：逐题审阅最终答案与标准：Stephen King / ["J. R. R. Tolkien"]；实体、数值、时间或所問字段不一致，维持错误。

### row 346：equivalent
What was the birth name of the ex-slave abolitionist featured in the art installation The Dinner Party?
标准：["Isabella (Belle) Baumfree"]
答案：Isabella Baumfree
理由：Isabella Baumfree与Isabella (Belle) Baumfree同一出生名，括号昵称可省略。

### row 347：equivalent
William Novac co-wrote the memoir of what American retired professional basketball player who is current president of basketball operations for the Los Angeles Lakers?
标准：["Earvin \"Magic\" Johnson Jr."]
答案：Magic Johnson
理由：Magic Johnson与Earvin Magic Johnson Jr.同一篮球运动员的常用名和全名。

### row 348：label_issue
How old was William DuVall when Black Gives Way to Blue was certified gold by the RIAA?
标准：["William Bradley DuVall (born September 6, 1967)"]
答案：43
理由：题目问年龄，标签却给姓名与出生日期，无法直接作为年龄等价判据；标签疑误不加分。

### row 351：uncertain
The current coach of the Los Angeles Clippers was signed as a free agent to the San Antonio Spurs during what season?
标准：["1994–95 NBA season"]
答案：1994
理由：1994未完整给出1994–95 NBA season所问赛季，保留精度争议，不加分。

### row 352：incorrect
Where does the train that runs from NYC and Miami station at in Florida?
标准：["Jacksonville station"]
答案：Miami
理由：逐题审阅最终答案：Miami；标准：["Jacksonville station"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 353：incorrect
Ali Eren Balıkel started a restaurant which hosted a number of famous figures including an English actor who won three consecutive what?
标准：["BAFTA Awards for Best Actress"]
答案：Academy Award
理由：逐题审阅最终答案与标准：Academy Award / ["BAFTA Awards for Best Actress"]；实体、数值、时间或所问字段不一致，维持错误。

### row 355：incorrect
Who was the secretary to the Winter Queen?
标准：["Sir Francis Nethersole"]
答案：Ebba Ryning
理由：逐题审阅最终答案与标准：Ebba Ryning / ["Sir Francis Nethersole"]。实体、数值、时间或所问字段不一致，维持错误。

### row 361：incorrect
Who is the Chief Executive Officer of the corporation that owns Space Dev?
标准：["Fatih Ozmen"]
答案：David W. Thompson
理由：逐题审阅最终答案与标准：David W. Thompson / ["Fatih Ozmen"]；实体、数值、时间或所问字段不一致，维持错误。

### row 362：incorrect
James Stuart became a specialist of a rhythmic pattern charecterised by what?
标准：["characterised by a moderately fast to very fast tempo"]
答案：a regular recurring motion
理由：逐题审阅最终答案与标准：a regular recurring motion / ["characterised by a moderately fast to very fast tempo"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Maurice Labro
理由：逐题审阅最终答案与标准：Maurice Labro / ["Orson Welles"]；实体、数值、时间或所问字段不一致，维持错误。

### row 366：incorrect
Jacques Sernas, actor in Fugitive in Trieste, was of what nationality?
标准：["Lithuanian-born French"]
答案：Lithuanian
理由：逐题审阅最终答案与标准：Lithuanian / ["Lithuanian-born French"]；实体、数值、时间或所問字段不一致，维持错误。

### row 368：uncertain
What was the name of a land where Maria Anna of Spain's husband was king?
标准：["Hungary"]
答案：Holy Roman Empire
理由：Holy Roman Empire与Hungary为不同地域及君主头衔对应地，不能按同一地点加分。

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
答案：sportscaster
理由：逐题审阅最终答案与标准：sportscaster / ["American"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 383：incorrect
Baadshah is an Indian action comedy film that was inspired by what Hong Kong action movie starring Jackie Chan and Richard Norton?
标准：["Mr. Nice Guy"]
答案：Nick of Time
理由：逐题审阅最终答案与标准：Nick of Time / ["Mr. Nice Guy"]；实体、数值、时间或所问字段不一致，维持错误。

### row 385：label_issue
Were Maurice Tourneur and Greg Mottola both American film directors?
标准：["French film director"]
答案：no
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 386：incorrect
What is the birthday of the Earl of Merioneth?
标准：["10 June 1921"]
答案：2006
理由：逐题审阅最终答案与标准：2006 / ["10 June 1921"]；实体、数值、时间或所问字段不一致，维持错误。

### row 388：incorrect
From 2003 to 2008 Tom Holland was responsible for what  ?
标准：["for crafting and voting on legislation"]
答案：Spider-Man
理由：逐题审阅最终答案：Spider-Man；标准：["for crafting and voting on legislation"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 391：incorrect
What profession did Alan Crosland and Kurt Voss both hold?
标准：["film director"]
答案：politician
理由：逐题审阅最终答案与标准：politician / ["film director"]；实体、数值、时间或所问字段不一致，维持错误。

### row 392：incorrect
Which town was home to a forward for the Western New York Flash?
标准：["Oyster Bay"]
答案：Elma
理由：逐题审阅最终答案：Elma；标准：["Oyster Bay"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 393：incorrect
Which team based in South Wales participated in a final game of 1980 Welsh Cup Final?
标准：["Newport County"]
答案：Bangor City
理由：逐题审阅最终答案与标准：Bangor City / ["Newport County"]。实体、数值、时间或所问字段不一致，维持错误。

### row 394：incorrect
What man, born in 1963, was instrumental in bringing the Boston Red Sox to the stadium City of Palms Park in Fort Myers, Florida?
标准：["Mike Greenwell"]
答案：Peter Gammons
理由：逐题审阅最终答案与标准：Peter Gammons / ["Mike Greenwell"]；实体、数值、时间或所问字段不一致，维持错误。

### row 395：incorrect
Which musician's band contains more letters in it's name, Micky Dolenz or Jesse James Dupree?
标准：["George Michael Dolenz"]
答案：Monkees
理由：题目问哪位音乐家，答案Monkees为乐队名，未给标签所指音乐家，不加分。

### row 396：incorrect
Tui Flower and Julia child were both known for what?
标准：["Cooking"]
答案：bringing French cuisine to the American public
理由：逐题审阅最终答案与标准：bringing French cuisine to the American public / ["Cooking"]；实体、数值、时间或所问字段不一致，维持错误。

### row 397：incorrect
What are some foods that may have been served at the Hawaiin Cottage?
标准：["poi, Kalua pig, poke, lomi salmon, opihi, haupia"]
答案：luau
理由：逐题审阅最终答案：luau；标准：["poi, Kalua pig, poke, lomi salmon, opihi, haupia"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 398：incorrect
Does Linzhou, Henan have a larger population than Xingcheng?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 401：incorrect
What surrounding river in a Canadian province was Erin Wall born near?
标准：["Bow River"]
答案：Highwood River
理由：逐题审阅最终答案与标准：Highwood River / ["Bow River"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 406：label_issue
Which director, Chris O'Dea or Lucky McKee,  is a Master of Fine Arts graduate of the UCLA School of Theater, Film and Television?
标准：["Edward Lucky McKee"]
答案：Chris O'Dea
理由：轨迹支持Chris O'Dea为UCLA MFA毕业生，与金标准Lucky McKee冲突；标签疑误单列。

### row 407：incorrect
Who designed the hotel that held the IFBB professional bodybuilding competition in September 1991?
标准：["architect Michael Graves"]
答案：Charles D. Wetmore
理由：逐题审阅最终答案与标准：Charles D. Wetmore / ["architect Michael Graves"]；实体、数值、时间或所问字段不一致，维持错误。

### row 410：uncertain
What athletic team has its football and basketball games broadcast on KFST and has a mascot who is named Bevo?
标准：["Texas Longhorns"]
答案：University of Texas at Austin
理由：University of Texas at Austin为大学，标准Texas Longhorns为校运动队，相关机构不直接互换。

### row 412：equivalent
Which characters are akin to goblins and were added to a Tilted Mill Entertainment video game in 2009?
标准：["Orc characters"]
答案：Orc
理由：Orc与Orc characters在游戏角色问题中同一角色种类，省略characters类别词。

### row 414：incorrect
what species of plants are Chamelaucium and Vanilla derived from?
标准：["flowers"]
答案：orchid
理由：逐题审阅最终答案与标准：orchid / ["flowers"]；实体、数值、时间或所问字段不一致，维持错误。

### row 417：uncertain
Illmatic, the debut studio album by Nas which featured the song "N.Y. State of Mind", was released on what date by which record label?
标准：["April 19, 1994, by Columbia Records"]
答案：April 19, 1994
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 419：incorrect
What is the name of one the ex-security officials that means The Institute?
标准：["Mossad"]
答案：Oldřich Černý
理由：逐题审阅最终答案与标准：Oldřich Černý / ["Mossad"]；实体、数值、时间或所問字段不一致，维持错误。

### row 420：incorrect
How many albums have been released by the same band that released the "Trance" EP?
标准：["4 albums"]
答案：2
理由：逐题审阅最终答案与标准：2 / ["4 albums"]；实体、数值、时间或所问字段不一致，维持错误。

### row 421：uncertain
After partially sinking in 1994, Celestyal Crystal was rebuilt for the purpose of what Bermudian company?
标准：["Norwegian Cruise Line Holdings Ltd."]
答案：Norwegian Cruise Line
理由：Norwegian Cruise Line为经营品牌/实体，标签Holdings Ltd.为控股公司；上下级关系不自动视为同一法律实体。

### row 426：equivalent
Was Kanako Momota or Mark Hollis born first?
标准：["Mark David Hollis"]
答案：Mark Hollis
理由：Mark Hollis与Mark David Hollis同一人，省略中间名。

### row 428：incorrect
The team that would become the Little Giants was located in the county seat of which Ohio county?
标准：["Mahoning County"]
答案：Scioto County
理由：逐题审阅最终答案：Scioto County；标准：["Mahoning County"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 430：equivalent
The 1948 Commonwealth Prime Ministers' Conference was hosted by the Prime Minister from what British party?
标准：["Labour"]
答案：Labour Party
理由：Labour Party与Labour同一政党。

### row 435：incorrect
Who is the original writer of the 1977 horror film?
标准：["Wes Craven"]
答案：John Carpenter
理由：逐题审阅最终答案与标准：John Carpenter / ["Wes Craven"]；实体、数值、时间或所问字段不一致，维持错误。

### row 436：equivalent
What season of the Indian reality TV series "Big Boss" did the model Lopamundra Raut compete in?
标准：["the tenth season"]
答案：10
理由：10与the tenth season同一季数。

### row 437：uncertain
Criss Angel generated $150 million in tourist revenue for his live performance show in what city?
标准：["Paradise, Nevada"]
答案：Las Vegas
理由：Las Vegas与Paradise, Nevada存在都会区及行政城界差异，保留地理精度争议。

### row 438：uncertain
What career titles do Ed Wood and Fernand Rivers share?
标准：["actor, writer, producer, and director"]
答案：director
理由：只给director，题目要求共有职业头衔且标签包含actor、writer、producer、director，字段不完整。

### row 439：uncertain
What is the pioneer who has a park dedicated to him near Lexington, North Carolina famous for?
标准：["Wilderness Road"]
答案：exploration and settlement of what is now Kentucky
理由：exploration and settlement of Kentucky为人物事业描述，未直接给标准Wilderness Road事迹。

### row 440：equivalent
The Gate is a song from the album scheduled for release in what month?
标准：["November 2017"]
答案：November
理由：题目只问month，November完整回答标准November 2017中的月份。

### row 441：incorrect
Who developed the jet fighters operated by the 41st Tactical Squadron of the Polish Air Force?
标准：["the Mikoyan design bureau"]
答案：General Dynamics
理由：逐题审阅最终答案：General Dynamics；标准：["the Mikoyan design bureau"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 442：equivalent
The Porsche 968 was the last in a line of front-engined sports cars following the 944 and which earlier model?
标准：["924"]
答案：Porsche 924
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 444：incorrect
The subject of the biography "Name Dropper" was born in what year?
标准：["1961"]
答案：1923
理由：逐题审阅最终答案与标准：1923 / ["1961"]；实体、数值、时间或所问字段不一致，维持错误。

### row 448：incorrect
Which plant genus is part of a family with a longer name, Morning glory or Rothmannia?
标准：["Morning glory"]
答案：Rothmannia
理由：逐题审阅最终答案与标准：Rothmannia / ["Morning glory"]。实体、数值、时间或所问字段不一致，维持错误。

### row 449：incorrect
What band did both Delores Holmes and an inductee to the Rock and Roll Hall of Fame sing in?
标准：["E Street Band"]
答案：Bruce Springsteen
理由：逐题审阅最终答案与标准：Bruce Springsteen / ["E Street Band"]；实体、数值、时间或所问字段不一致，维持错误。

### row 452：incorrect
What is the name of a Sri Lankan political party associated with the aim of developing a national identity based on shared characteristics and preserving the nation's culture?
标准：["The Sri Lanka Freedom Party"]
答案：Jathika Hela Urumaya
理由：逐题审阅最终答案与标准：Jathika Hela Urumaya / ["The Sri Lanka Freedom Party"]；实体、数值、时间或所问字段不一致，维持错误。

### row 453：equivalent
How many albums had been recorded by Talking Heads by November, 1980?
标准：["four"]
答案：4
理由：4与four相同数量。

### row 454：incorrect
In what year did the American Record company established in 1958 release a record co-produced by Adam Faith?
标准：["January 1974"]
答案：1958
理由：逐题审阅最终答案：1958；标准：["January 1974"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 456：incorrect
What is Diego Tonetto's Italian passport called?
标准：["Italian nationality law"]
答案：Passaporto
理由：逐题审阅最终答案与标准：Passaporto / ["Italian nationality law"]。实体、数值、时间或所问字段不一致，维持错误。

### row 457：incorrect
What year was Playford B Power Station permanently closed in by its Australian operator?
标准：["2015"]
答案：2016
理由：逐题审阅最终答案：2016；标准：["2015"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 458：incorrect
Who did the player nicknamed "The Human Highlight Film" play for after he left the Atlanta Hawks?
标准：["Boston Celtics"]
答案：Los Angeles Clippers
理由：逐题审阅最终答案：Los Angeles Clippers；标准：["Boston Celtics"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 459：incorrect
Wheelock Whitney is just one member of the Whitney Family. Where did this American family originate from?
标准：["London, England"]
答案：New England
理由：逐题审阅最终答案与标准：New England / ["London, England"]；实体、数值、时间或所问字段不一致，维持错误。

### row 460：incorrect
What city did the musician whose debut album shares its title with the 1959 Alfred Hitchcock hail from?
标准：["Chicago, IL"]
答案：Gary, Indiana
理由：逐题审阅最终答案与标准：Gary, Indiana / ["Chicago, IL"]；实体、数值、时间或所问字段不一致，维持错误。

### row 461：incorrect
Which star in the Maltese Bippy died in 1987?
标准：["Dan Rowan"]
答案：Charles Thake
理由：逐题审阅最终答案与标准：Charles Thake / ["Dan Rowan"]；实体、数值、时间或所問字段不一致，维持错误。

### row 463：incorrect
APB and Sleeper are both from britain?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 469：incorrect
Who was the brother of the wife of the Democratic Party nomination for Vice President in 1972?
标准：["President John F. Kennedy"]
答案：Theodore Adams "Ted" Mondale
理由：逐题审阅最终答案与标准：Theodore Adams "Ted" Mondale / ["President John F. Kennedy"]；实体、数值、时间或所问字段不一致，维持错误。

### row 470：incorrect
What is the name of  rocker, who was awarded "Rock Goddess of the Year" in the Annual Loudwide Music Awards, who sang with high pitched screams in her band's albums?
标准：["Maria Brink"]
答案：Kat Bjelland
理由：逐题审阅最终答案与标准：Kat Bjelland / ["Maria Brink"]；实体、数值、时间或所问字段不一致，维持错误。

### row 474：equivalent
Who was born first Al-Karaji or Masatoshi Gündüz Ikeda?
标准：["Abū Bakr ibn Muḥammad ibn al Ḥusayn al-Karajī"]
答案：Al-Karaji
理由：Al-Karaji与标准长阿拉伯人名指同一数学家。

### row 476：incorrect
How long is the bridge in the Öresund Region that connect Copenhagen, Denmark and Malmo, Sweden?
标准：["8 km"]
答案：7.8 miles
理由：逐题审阅最终答案：7.8 miles；标准：["8 km"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 477：uncertain
What were the nations after 1722 that composed a culture that was extensively studied by William N. Fenton?
标准：["Mohawk, Onondaga, Oneida, Cayuga, Seneca, and Tuscarora"]
答案：Iroquois
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 479：incorrect
In what year was the football club for which Reuven Niemeijer plays founded?
标准：["1903"]
答案：1900
理由：逐题审阅最终答案：1900；标准：["1903"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 481：equivalent
Where is the company that owns thanKing Horse pub restaurant chain based ?
标准：["Bury St Edmunds,"]
答案：Bury St Edmunds, Suffolk, England
理由：Bury St Edmunds, Suffolk, England保留标准城市并补充地理说明。

### row 482：incorrect
Where is the University Joe Odom played football for located?
标准：["West Lafayette, Indiana"]
答案：Houston Oilers
理由：逐题审阅最终答案与标准：Houston Oilers / ["West Lafayette, Indiana"]；实体、数值、时间或所问字段不一致，维持错误。

### row 489：uncertain
Where did the tribe Mato-tope chief over reside?
标准：["North Dakota"]
答案：upper Missouri River
理由：upper Missouri River覆盖区域宽于North Dakota，不能由较宽地理范围自动确认同州。

### row 490：uncertain
What Swedish songwriter worked with Taylor Swift?
标准：["Shellback"]
答案：Max Martin
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 491：equivalent
Which author has won more Pulitzer Prizes, Thomas Friedman or Henri Bergson?
标准：["Thomas Loren Friedman"]
答案：Thomas Friedman
理由：Thomas Friedman与Thomas Loren Friedman同一人，省略中间名。

### row 493：equivalent
Whose given first name is longer, Theo Angelopoulos and Budd Boetticher (nicknames)?
标准：["Theodoros \"Theo\" Angelopoulos"]
答案：Theo
理由：Theo在题中Theo Angelopoulos与Budd Boetticher的二选一语境中明确指Theodoros Theo Angelopoulos，省略姓氏。

### row 494：incorrect
What year did a Russian soprano opera singer born in October 1926 leave Russia with her cellist husband and daughter?
标准：["1974"]
答案：1923
理由：逐题审阅最终答案与标准：1923 / ["1974"]；实体、数值、时间或所问字段不一致，维持错误。

### row 497：incorrect
What month did the an online adult website whose last print magazine was published in the summer of 2007 recognize Nikita Gross?
标准：["January"]
答案：SexIs
理由：逐题审阅最终答案与标准：SexIs / ["January"]；实体、数值、时间或所问字段不一致，维持错误。

### row 498：incorrect
Which airport is busier, Palm Springs International Airport or Trenton–Mercer Airport?
标准：["Trenton–Mercer Airport"]
答案：Palm Springs International Airport
理由：逐题审阅最终答案：Palm Springs International Airport；标准：["Trenton–Mercer Airport"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 501：uncertain
Where is the university located in which the current editor-in-chief of Review of Policy Reseach is from?
标准：["Toronto"]
答案：Ryerson University
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 504：incorrect
Where is the headquarters for the service broadcaster the show Tenko is on?
标准：["Broadcasting House in London"]
答案：2-4-8, Daiba, Minato, Tokyo
理由：逐题审阅最终答案与标准：2-4-8, Daiba, Minato, Tokyo / ["Broadcasting House in London"]；实体、数值、时间或所问字段不一致，维持错误。

### row 505：incorrect
Francisco Mela performed with which American Jazz bassist and singer born in 1984 ?
标准：["Esperanza Spalding"]
答案：John Scofield
理由：逐题审阅最终答案与标准：John Scofield / ["Esperanza Spalding"]；实体、数值、时间或所问字段不一致，维持错误。

### row 508：incorrect
What album did John Lennon release before the one that contained the song "How?"?
标准：["John Lennon/Plastic Ono Band"]
答案：Imagine
理由：逐题审阅最终答案与标准：Imagine / ["John Lennon/Plastic Ono Band"]；实体、数值、时间或所问字段不一致，维持错误。

### row 509：incorrect
Where is the closest relative to the whale located?
标准：["sub-Saharan Africa"]
答案：hippopotamuses
理由：逐题审阅最终答案：hippopotamuses；标准：["sub-Saharan Africa"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 510：incorrect
What English campaigner for the suffragette movement did Angela Down portray?
标准：["Sylvia Pankhurst"]
答案：Emily Davison
理由：逐题审阅最终答案与标准：Emily Davison / ["Sylvia Pankhurst"]；实体、数值、时间或所问字段不一致，维持错误。

### row 511：uncertain
Christopher Oscar Pena was recognized by an entertainment-industry brand aimed at what?
标准：["people working in film and the performing arts"]
答案：members of awards voting groups
理由：奖项投票群体与标准电影及表演艺术从业者受众范围不同，不自动确认等价。

### row 517：equivalent
What is the English translation of the tier four league that TSV Schilksee was promoted to in 2014, following a league championship in the Schleswig-Holstein-Liga?
标准：["Regional League North"]
答案：Regionalliga Nord
理由：Regionalliga Nord与Regional League North指同一联赛名称，德文原名与英文直译语义一致。

### row 518：incorrect
Umi-a-Liloa inherited authority of a kind which is a belief in what?
标准：["belief in many deities and spirits"]
答案：religious
理由：religious仅表达宗教属性，未说明标准belief in many deities and spirits中的多神与灵体信仰内容。

### row 521：equivalent
What sport do The Basham Brothers and Doug Basham have in common?
标准：["wrestling"]
答案：professional wrestling
理由：professional wrestling与wrestling在职业摔跤人物语境中同一运动。

### row 526：equivalent
Q:The 7.92×57mm Mauser rifle cartridge was used by which country's military in the 20th century?
标准：["German service cartridge"]
答案：Germany
理由：问题问国家，Germany提取标准German service cartridge中的国家身份。

### row 529：incorrect
Which company used a voice actor who also voiced He-Man?
标准：["9Lives"]
答案：Filmation
理由：逐题审阅最终答案：Filmation；标准：["9Lives"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：1962
理由：逐题审阅最终答案与标准：1962 / ["December 23, 1977"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 541：incorrect
What two singers who worked together on the song I Would Like to See You Again also performed as part of a country music group which was active between 1985 and 1995?
标准：["Johnny Cash, Waylon Jennings"]
答案：Waylon Jennings
理由：逐题审阅最终答案：Waylon Jennings；标准：["Johnny Cash, Waylon Jennings"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 542：incorrect
The M104 155mm Projectile was specifically designed to carry about 11.7 pounds of what prototypical substance?
标准：["mustard gas"]
答案：high explosive
理由：逐题审阅最终答案与标准：high explosive / ["mustard gas"]；实体、数值、时间或所问字段不一致，维持错误。

### row 544：incorrect
In what part of England is John Folwes' country house located?
标准：["West Dorset, South West England."]
答案：Berkshire
理由：逐题审阅最终答案：Berkshire；标准：["West Dorset, South West England."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 545：equivalent
What is the global rank by population of the city that Daewoong Pharmaceutical Co., Ltd is based in?
标准：["world's 16th largest city"]
答案：16
理由：16在城市全球人口排名问题中表示第16名，与world's 16th largest city一致。

### row 546：equivalent
what year was the cover artist of Multiverse: Exploring Poul Anderson's Worlds born ?
标准：["September 13, 1960"]
答案：1960
理由：题目只问year，1960完整提取标准September 13, 1960中的年份。

### row 547：incorrect
The producer of "Live By NIght" began his film career playing what role in "Critters 3"?
标准：["Josh"]
答案：an interstellar bounty hunter
理由：逐题审阅最终答案与标准：an interstellar bounty hunter / ["Josh"]；实体、数值、时间或所问字段不一致，维持错误。

### row 548：incorrect
An actress in Strange Fruit was better known for a role in CBS sitcom.  Which sitcom is this actress better known for than her role in Strange Fruit?
标准：["The Jeffersons"]
答案：Cheers
理由：逐题审阅最终答案与标准：Cheers / ["The Jeffersons"]；实体、数值、时间或所问字段不一致，维持错误。

### row 549：incorrect
Who was born first Doug Liman or Saul Metzstein?
标准：["Douglas Eric \"Doug\" Liman"]
答案：Saul Metzstein
理由：逐题审阅最终答案：Saul Metzstein；标准：["Douglas Eric \"Doug\" Liman"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 550：incorrect
What year was George Harrison's top UK charted song voted the nations 11th favorite 1980s number?
标准：["2015"]
答案：1997
理由：逐题审阅最终答案与标准：1997 / ["2015"]；实体、数值、时间或所问字段不一致，维持错误。

### row 553：incorrect
The Environment Act 1995 passed under the tutelage of a politician associated with what political party?
标准：["British Conservative Party"]
答案：Labour
理由：逐题审阅最终答案与标准：Labour / ["British Conservative Party"]；实体、数值、时间或所问字段不一致，维持错误。

### row 556：uncertain
the work of The Last Poets and Gil Scott Heron inspired music that fits under what larger sub-genre?
标准：["underground hip hop"]
答案：Political hip hop
理由：Political hip hop与underground hip hop可能交叠，但属于不同风格分类，不能按同义加分。

### row 557：incorrect
Which date occurred first the end of Riley Hawk's amateur career or end of production of Skateboard Magazine ?
标准：["October 15, 2013"]
答案：end of production of Skateboard Magazine
理由：逐题审阅最终答案与标准：end of production of Skateboard Magazine / ["October 15, 2013"]；实体、数值、时间或所問字段不一致，维持错误。

### row 558：incorrect
What team was formed in 1996 that starred players like Robert Parish?
标准：["50 Greatest Players in National Basketball Association History"]
答案：Boston Celtics
理由：逐题审阅最终答案与标准：Boston Celtics / ["50 Greatest Players in National Basketball Association History"]；实体、数值、时间或所问字段不一致，维持错误。

### row 560：uncertain
What is the name of the largest publicly owned company in Minnesota that is situated in Minnesota's most populous county?
标准：["United Healthcare"]
答案：UnitedHealth Group
理由：UnitedHealth Group与United Healthcare为母公司与业务品牌关系；轨迹支持前者但不与后者直接等价。

### row 561：incorrect
What Hong Kong actor born in 1980 will star in "Heart and Greed"?
标准：["Bosco Wong Chung-chak"]
答案：Joseph Lee
理由：逐题审阅最终答案与标准：Joseph Lee / ["Bosco Wong Chung-chak"]；实体、数值、时间或所问字段不一致，维持错误。

### row 566：equivalent
Which film was was made first The Young Black Stallion or Wild Hearts Can't Be Broken?
标准：["Wild Hearts Can’t Be Broken"]
答案：Wild Hearts Can't Be Broken
理由：Wild Hearts Can't Be Broken与Wild Hearts Can’t Be Broken仅撇号编码不同。

### row 567：incorrect
Are Billy and Barak both breeds of scenthound? (Barak is also known as a Bosnian Coarse-haired Hound)?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 568：equivalent
At least how many countries does the company that bought Oil Can Henry's operate in?
标准：["100 countries"]
答案：more than 100
理由：题目问至少多少国家；more than 100包含标准的100个国家下界，未减少覆盖数。

### row 570：incorrect
What railroad in which Challengers were most common was completed in 1915?
标准：["Clinchfield Railroad"]
答案：Union Pacific Railroad
理由：逐题审阅最终答案与标准：Union Pacific Railroad / ["Clinchfield Railroad"]；实体、数值、时间或所问字段不一致，维持错误。

### row 571：incorrect
What component was included on the iPad4 that is now a registered trademark in Jamaica?
标准：["Retina Display"]
答案：Lightning
理由：逐题审阅最终答案与标准：Lightning / ["Retina Display"]；实体、数值、时间或所问字段不一致，维持错误。

### row 572：incorrect
Rejuvelac is kind of grain water invented and promoted by a "holistic health" practitioner born in which year ?
标准：["1909"]
答案：1916
理由：逐题审阅最终答案与标准：1916 / ["1909"]；实体、数值、时间或所问字段不一致，维持错误。

### row 573：uncertain
What is the nationality of the author of Fifty Shades Freed?
标准：["English"]
答案：British
理由：British比English范围更宽，严格等价主分数暂不增加。

### row 574：uncertain
The Church of St Peter in Pertenhall, Bedfordshire, England was added to this register on 13 July 1964.?
标准：["Statutory List of Buildings of Special Architectural or Historic Interest"]
答案：Grade I listed
理由：Grade I listed为列级状态，标签为法定建筑名录名称；关联但未完整回答名录，不加分。

### row 575：equivalent
How many years in prison did the Norfolk farmer defended by Anthony Scrivener serve?
标准：["three"]
答案：three years
理由：three years与three在服刑年数问题下同一数量，附加单位。

### row 577：incorrect
What is Rachelle Amy Beinart's role in the film that follows a group of rebels on a mission?
标准：["stunt performances"]
答案：French foreign aid doctor
理由：逐题审阅最终答案与标准：French foreign aid doctor / ["stunt performances"]；实体、数值、时间或所问字段不一致，维持错误。

### row 578：incorrect
The water-based dark ride in Walt Disney is connected to a song known for what?
标准：["most performed song of all time"]
答案：Can You Feel the Love Tonight
理由：逐题审阅最终答案与标准：Can You Feel the Love Tonight / ["most performed song of all time"]；实体、数值、时间或所问字段不一致，维持错误。

### row 579：incorrect
What is this fictional scientifically and technologically advanced militaristic alien race, from which Sequoia descends, is called?
标准：["the Ruul"]
答案：Cotati
理由：逐题审阅最终答案与标准：Cotati / ["the Ruul"]；实体、数值、时间或所问字段不一致，维持错误。

### row 581：incorrect
Who did the Star and Dagger bass player marry?
标准：["Sean Yseult."]
答案：Yvette Bissonnet
理由：逐题审阅最终答案与标准：Yvette Bissonnet / ["Sean Yseult."]；实体、数值、时间或所问字段不一致，维持错误。

### row 582：incorrect
Which American pro basketball player who won gold at the 2008 Summer Olympics was signed by the Utah Jazz during the 2005-05 offseason?
标准：["Carlos Austin Boozer Jr."]
答案：Andrei Kirilenko
理由：逐题审阅最终答案与标准：Andrei Kirilenko / ["Carlos Austin Boozer Jr."]；实体、数值、时间或所问字段不一致，维持错误。

### row 586：equivalent
Where is the location of Liberty Square park in Disneyland California?
标准：["Anaheim"]
答案：Anaheim, California
理由：Anaheim, California与Anaheim同一城市。

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
答案：1965
理由：逐题审阅最终答案：1965；标准：["1962"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 604：uncertain
Of these two publication--Báiki and Sick--what type of publication is the one that was published most frequently?
标准：["satirical-humor magazine"]
答案：magazine
理由：magazine省略satirical-humor的关键细分类型。

### row 605：equivalent
Shadi Attieh is often referred to as the Lebanese version of a footballer who plays for what Major League Soccer team?
标准：["Los Angeles Galaxy"]
答案：LA Galaxy
理由：LA Galaxy与Los Angeles Galaxy为同一球队名称缩写。

### row 606：incorrect
What is in both the Lithocarpus and Duranta species?
标准：["trees"]
答案：flowers
理由：逐题审阅最终答案：flowers；标准：["trees"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：approximately
理由：逐题审阅最终答案：approximately；标准：["2 acre"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 611：equivalent
On which coast can the California Aqueduct and the Lake Washington Ship Canal be found?
标准：["west"]
答案：Pacific Coast
理由：题目限定两条美国水道，Pacific Coast与west均指美国西海岸。

### row 612：incorrect
What do Josef Veltjens and Hermann Goering have in common?
标准：["A veteran World War I fighter pilot ace"]
答案：personal emissary
理由：逐题审阅最终答案与标准：personal emissary / ["A veteran World War I fighter pilot ace"]；实体、数值、时间或所问字段不一致，维持错误。

### row 614：incorrect
In addition to the individual born on August 21, who else wrote He's The Great Imposter?
标准：["Sharon Sheeley"]
答案：Robert Crichton
理由：逐题审阅最终答案：Robert Crichton；标准：["Sharon Sheeley"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：22
理由：逐题审阅最终答案与标准：22 / ["It contains twenty-three episodes"]。实体、数值、时间或所问字段不一致，维持错误。

### row 620：equivalent
John Hatzistergos was a Member of a council that has how many members ?
标准：["42 members"]
答案：42
理由：42与42 members同一数量，省略题目已限定单位。

### row 621：equivalent
Ross Pople worked with this French dominant figure of the post-war classical music world.?
标准：["Pierre Louis Joseph Boulez"]
答案：Pierre Boulez
理由：Pierre Boulez与Pierre Louis Joseph Boulez同一人，省略中间名。

### row 622：incorrect
John Stark Regional High School serves the community in which New Hampshire county?
标准：["Merrimack"]
答案：Hillsborough County
理由：逐题审阅最终答案：Hillsborough County；标准：["Merrimack"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 623：incorrect
Who has the highest scope of profession in Peter Yates or Jang Joon-hwan?
标准：["Peter James Yates"]
答案：Jang Joon-hwan
理由：逐题审阅最终答案与标准：Jang Joon-hwan / ["Peter James Yates"]。实体、数值、时间或所问字段不一致，维持错误。

### row 624：equivalent
Who wrote lyrics for both "Little Shop of Horrors" and the song "Be Our Guest?"?
标准：["Howard Elliott Ashman"]
答案：Howard Ashman
理由：Howard Ashman与Howard Elliott Ashman同一作词人，省略中间名。

### row 625：uncertain
What was the given name of the singer who is most closely associated with The Dakotas ?
标准：["William Howard Ashton,"]
答案：Billy J.
理由：Billy J.为艺名片段，题目问given name且标签William Howard Ashton，未提供所问本名。

### row 631：equivalent
Which interviewee featured in The History of Sex also hosted the radio show "Sexually Speaking"?
标准：["Dr. Ruth Westheimer"]
答案：Ruth Westheimer
理由：Ruth Westheimer与Dr. Ruth Westheimer同一人，省略学衔。

### row 632：incorrect
This event which was part of the 1954 AAA National Championship Trail was held at a racing circuit located at the corner of what?
标准：["16th Street and Georgetown Road"]
答案：the TT Grandstand
理由：逐题审阅最终答案与标准：the TT Grandstand / ["16th Street and Georgetown Road"]；实体、数值、时间或所问字段不一致，维持错误。

### row 634：equivalent
Which Hong Kong actor born on 19 August 1946 starred in The Sentimental Swordsman?
标准：["Tommy Tam Fu-Wing"]
答案：Ti Lung
理由：轨迹Ti Lung条目明确Tommy Tam Fu-Wing known by stage name Ti Lung，同一演员艺名。

### row 636：uncertain
Which  American politician and lawyer contested in San Francisco mayoral election, 2003?
标准：["Matthew Edward"]
答案：Gavin Newsom
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 643：equivalent
What is one element of House dance where the dancer ripples his or her torso back and forth?
标准：["the jack"]
答案：Jacking
理由：Jacking与the jack指House dance中同一躯干摇动元素，词形不同。

### row 644：equivalent
How many seasons has a popular tv show had, in which one of the episodes is called Moho House?
标准：["28"]
答案：twenty-eighth
理由：twenty-eighth在所问剧季数量语境下指28季，与28一致。

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

### row 648：equivalent
How many more singles titles did Kim Warwick win than Jorge Lozano?
标准：["three singles titles"]
答案：three
理由：three与three singles titles同一数量，单位由问题给出。

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
答案：Holbæk Boldklub
理由：题目问sports club，金标准Søren Lindsted为人物；模型俱乐部也未独立证实。

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

### row 669：incorrect
What type of diary did one of the founders of the John Bishop Memorial Hospital in Srinagar write?
标准：["a travel diary"]
答案：journal
理由：逐题审阅最终答案：journal；标准：["a travel diary"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 670：equivalent
who is older, Maria Sharapova or Chanda Rubin?
标准：["Chanda Rubin (born February 18, 1976)"]
答案：Chanda Rubin
理由：Chanda Rubin与带出生日期的Chanda Rubin同一选项。

### row 672：equivalent
Which American former competitive swimmer was Mitzi Kremer team mate?
标准：["Dara Grace Torres"]
答案：Dara Torres
理由：Dara Torres与Dara Grace Torres同一游泳运动员，省略中间名。

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

### row 679：uncertain
The genus containing lions also contains several poorly known what?
标准：["Old World fossil representatives"]
答案：species
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 681：equivalent
What role did Kim Dong-wook play in the 2012 South Korean historical film directed by Kim Dae-seung?
标准：["an obsessed and tormented king"]
答案：Prince Sung-won
理由：轨迹把同一演员在The Concubine中的角色称Prince Sung-won，并描述为obsessed and tormented king；角色名与标准角色描述一致。

### row 682：incorrect
What amount was the settlement that the character from the Son of al Quada got in 2017?
标准：["$10.5 million"]
答案：$750,000
理由：逐题审阅最终答案与标准：$750,000 / ["$10.5 million"]；实体、数值、时间或所问字段不一致，维持错误。

### row 686：incorrect
Who was also an actor, Serri or John Fogerty?
标准：["Serri"]
答案：John Fogerty
理由：逐题审阅最终答案与标准：John Fogerty / ["Serri"]。实体、数值、时间或所问字段不一致，维持错误。

### row 687：equivalent
literary magazine Okyeame was inspired by this first prime Minister of Ghana whom led Ghana to independence from what country?
标准：["Britain"]
答案：the United Kingdom
理由：the United Kingdom与Britain在加纳独立来源国问题中指同一国家。

### row 688：equivalent
The competition Lev Oborin won in 1927 is held in what city?
标准：["Warsaw, Poland"]
答案：Warsaw
理由：题目只问city，Warsaw完整回答Warsaw, Poland中的城市。

### row 701：incorrect
The Chinese actress also known as Crystal Liu stars in Night Peacock with which three other actresses?
标准：["Liu Ye, Yu Shaoqun and Leon Lai"]
答案：Liu Ye
理由：逐题审阅最终答案：Liu Ye；标准：["Liu Ye, Yu Shaoqun and Leon Lai"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 702：uncertain
What retailer did Albert Heijn start up that eventually merged with the Delhaize Group?
标准：["Koninklijke Ahold N.V."]
答案：Albert Heijn
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 703：incorrect
What is the name of the umcoming horror film adaptation starring Melanie Griffiths daughter?
标准：["Suspiria"]
答案：The Blackcoat's Daughter
理由：逐题审阅最终答案：The Blackcoat's Daughter；标准：["Suspiria"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 713：equivalent
What kind of group does Josey Scott and Kurt Cobain have in common?
标准：["band"]
答案：rock band
理由：rock band完整回答标准band，并给出不冲突的类别限定。

### row 717：incorrect
Thea Ruth White is best known for her voice over work as Muriel Bagge on  an American animated horror comedy television series created for who?
标准：["Cartoon Network"]
答案：John R. Dilworth
理由：逐题审阅最终答案与标准：John R. Dilworth / ["Cartoon Network"]；实体、数值、时间或所问字段不一致，维持错误。

### row 718：equivalent
Which guitarist that played on the LP Street Survivors and was a member of an American Southern Rock band from May 1976 until his death Oct 1977?
标准：["Steven Earl \"Steve\" Gaines"]
答案：Steve Gaines
理由：Steve Gaines与Steven Earl Steve Gaines同一吉他手的常用名和全名。

### row 720：incorrect
Which countries forces fought in The Battle of Hürtgen Forest which was covered in the shooter video game Darkest Hour: Europe '44-'45?
标准：["American and German"]
答案：American
理由：逐题审阅最终答案：American；标准：["American and German"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 724：equivalent
To where did the war criminal who is the fictional defendant in the film After the Truth flee in real life ?
标准：["South America"]
答案：Argentina
理由：轨迹明确躲藏在Argentina；Argentina是标准South America内的具体逃亡目的地。

### row 726：incorrect
Which tropical storm has been present in the Central Pacific Ocean but not in the western north Pacific Ocean?
标准：["Ana"]
答案：Hurricane
理由：逐题审阅最终答案与标准：Hurricane / ["Ana"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 731：uncertain
What offence were opening batsman Khalid Latif and 5 other cricketers suspended for, in February 2017?
标准：["spot-fixing"]
答案：violating the anti-corruption code
理由：violating the anti-corruption code为宽泛违规类别，未给具体spot-fixing行为，不加分。

### row 732：equivalent
What is the main difference between the game Plateau and the game Colt Express?
标准：["Colt Express is a railway-themed"]
答案：railway-themed
理由：railway-themed直接给出题中Colt Express相对Plateau的铁路主题差别，与标准核心相同。

### row 734：equivalent
Both WAGS Atlanta and WAGS are what?
标准：["American reality television series"]
答案：reality television series
理由：题目问节目类型，reality television series完整回答类别；标准American为附加国别。

### row 735：incorrect
Vivian Pinn taught at which college founded in Massachusetts in 1852?
标准：["Tufts College"]
答案：Massachusetts Agricultural College
理由：逐题审阅最终答案与标准：Massachusetts Agricultural College / ["Tufts College"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 743：uncertain
What are the publishing years of this American and New York based film magazine published by Hachette Filipacchi Media U.S., where April Bernard worked as senior editor?
标准：["between 1987 and 2010"]
答案：1987
理由：1987省略出版结束年2010，完整时间段未答全。

### row 745：uncertain
When was the track from which a sample was featured in "Take Me to the Clouds Above" released?
标准：["16 March 1987"]
答案：1987
理由：1987省略标准16 March日期，保留精度不足。

### row 747：incorrect
What was the capacity of the stadium that Colección Privada that was filmed on October 10, 2000?
标准：["15,500"]
答案：43,713
理由：逐题审阅最终答案与标准：43,713 / ["15,500"]；实体、数值、时间或所问字段不一致，维持错误。

### row 749：uncertain
What language, also known as the Amazigh, is part of Siwa Oasis?
标准：["Berber"]
答案：Siwi
理由：Siwi为Berber语言分支，尚未确认问题要求总类还是具体语言。

### row 750：incorrect
Here's Little Richard is a debut album containing a song written by Little Richard, Enotris Johnson and who else?
标准：["Robert \"Bumps\" Blackwell"]
答案：Enotris Johnson
理由：逐题审阅最终答案与标准：Enotris Johnson / ["Robert \"Bumps\" Blackwell"]；实体、数值、时间或所问字段不一致，维持错误。

### row 751：equivalent
Which writer was from England, Henry Roth or Robert Erskine Childers?
标准：["Robert Erskine Childers DSC"]
答案：Robert Erskine Childers
理由：Robert Erskine Childers与附加DSC勋衔的标准同一人。

### row 754：uncertain
Which two occupations does Ronnie Dunn and Annie Lennox have in common?
标准：["singer, songwriter"]
答案：singer
理由：只给singer，缺少明确要求的另一职业songwriter。

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

### row 757：incorrect
August R. Lindt served as chairman of a UN program from 1956 to 1960 that won how many noble prizes ?
标准：["two Nobel Peace Prizes"]
答案：one
理由：逐题审阅最终答案与标准：one / ["two Nobel Peace Prizes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 758：equivalent
Between Joe Orton and Henry James, which author is the adjective "Ortonesque" used to refer to his work?
标准：["John Kingsley \"Joe\" Orton"]
答案：Joe Orton
理由：Joe Orton与John Kingsley Joe Orton同一作家的常用名和全名。

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
答案：fourth season
理由：逐题审阅最终答案与标准：fourth season / ["first"]；实体、数值、时间或所问字段不一致，维持错误。

### row 769：incorrect
Suicide's 1977 released album features a song based on what brand's comic character?
标准：["Marvel"]
答案：Garfield
理由：逐题审阅最终答案与标准：Garfield / ["Marvel"]；实体、数值、时间或所问字段不一致，维持错误。

### row 771：incorrect
What is the height of the tallest mountain from which the Glen River flows?
标准：["850 m"]
答案：Navajo Mountain
理由：逐题审阅最终答案与标准：Navajo Mountain / ["850 m"]；实体、数值、时间或所问字段不一致，维持错误。

### row 773：incorrect
When was the improvisational troupe, which trained Amy Sedaris, Paul Dinello, and Stephen Colber, founded?
标准：["1959"]
答案：1955
理由：逐题审阅最终答案与标准：1955 / ["1959"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Everybody Hates Chris
理由：逐题审阅最终答案：Everybody Hates Chris；标准：["Girl Meets World"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 779：equivalent
Zach Parise's father played in which league?
标准：["NHL"]
答案：National Hockey League
理由：National Hockey League与NHL同一联赛的全称和缩写。

### row 780：incorrect
What stadium does the team who has Kent Baer as the defensive coordinator play its home games?
标准：["Sam Boyd Stadium"]
答案：Folsom Field
理由：逐题审阅最终答案与标准：Folsom Field / ["Sam Boyd Stadium"]；实体、数值、时间或所问字段不一致，维持错误。

### row 782：uncertain
Which of the university at which Jack M. Guttentag  is a professor emeritus of finance was established in 1881 through a donation?
标准：["Wharton School of the University"]
答案：University of Pennsylvania
理由：University of Pennsylvania为母校，题目1881 donation限定的是Wharton School具体学院。

### row 785：incorrect
What criteria subjectively qualifies the Houston Astrodome to be called the Eighth Wonder of the World?
标准：["comparable to the seven Wonders of the World"]
答案：nickname
理由：逐题审阅最终答案与标准：nickname / ["comparable to the seven Wonders of the World"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 788：equivalent
What is the rule that makes a major difference between the National League and the American League that allows another player to bat for the pitcher?
标准：["the designated hitter rule"]
答案：designated hitter
理由：题目已限定rule，designated hitter省略rule仍指同一指定打击规则。

### row 789：incorrect
Jamie Harris is best known for his role as The Hook-Handed Man in a movie directed by who ?
标准：["Brad Silberling"]
答案：Elia Kazan
理由：逐题审阅最终答案与标准：Elia Kazan / ["Brad Silberling"]；实体、数值、时间或所问字段不一致，维持错误。

### row 791：incorrect
Who is a guest in the final two episodes of season eighteen of South Park?
标准：["PewDiePie"]
答案：Trey Parker
理由：逐题审阅最终答案与标准：Trey Parker / ["PewDiePie"]；实体、数值、时间或所问字段不一致，维持错误。

### row 792：incorrect
What anchor store in the Stratford Square Mall has 728 department store locations in the continental United States?
标准：["Macy's"]
答案：Kohl's
理由：逐题审阅最终答案：Kohl's；标准：["Macy's"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 793：uncertain
What type of media does Jeff Rona and Veeram have in common?
标准：["film"]
答案：soundtrack
理由：soundtrack为配乐媒介，film为电影媒介，相关但不能直接视为相同媒体类型。

### row 794：equivalent
Which American actor portray Steve Urkel in "Family Matters"?
标准：["Jaleel Ahmad White"]
答案：Jaleel White
理由：Jaleel White与Jaleel Ahmad White同一演员，省略中间名。

### row 795：incorrect
How much Argentina currency was involved in Boudougate?
标准：["2.3 million pesos"]
答案：120 million
理由：逐题审阅最终答案与标准：120 million / ["2.3 million pesos"]；实体、数值、时间或所问字段不一致，维持错误。

### row 797：incorrect
Which Royal Air Force is located in a town that had a population of 2,841 on 15 April 2012?
标准：["Mount Pleasant"]
答案：RAF Lyneham
理由：逐题审阅最终答案：RAF Lyneham；标准：["Mount Pleasant"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 798：incorrect
What did Eric Radomski produce that premiered on Disney XD on May 26, 2013?
标准：["Avengers Assemble"]
答案：Bunks
理由：逐题审阅最终答案与标准：Bunks / ["Avengers Assemble"]；实体、数值、时间或所问字段不一致，维持错误。

### row 799：incorrect
What Hindi thriller directed by Deepak SHivdasani features choreography by Phulwa Khamkar?
标准：["Julie 2"]
答案：Happy New Year
理由：逐题审阅最终答案：Happy New Year；标准：["Julie 2"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 803：incorrect
Was American Scientist or Dwell published first?
标准：["American Scientist"]
答案：Scientific American
理由：逐题审阅最终答案与标准：Scientific American / ["American Scientist"]；实体、数值、时间或所问字段不一致，维持错误。

### row 804：equivalent
Which is the Birthplace of Sir Isaac Newton and has a neighboring village called Belvor?
标准：["Woolsthorpe"]
答案：Woolsthorpe-by-Colsterworth
理由：Woolsthorpe-by-Colsterworth是所问牛顿出生地Woolsthorpe的完整地名。

### row 809：incorrect
The non-fiction book "Finding Chandra" is about an affair between the victim and a congressman that holds a B.B.A from what school?
标准：["USC Marshall School of Business"]
答案：California State University, Stanislaus
理由：逐题审阅最终答案：California State University, Stanislaus；标准：["USC Marshall School of Business"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 810：incorrect
Psychopsis and Aubrieta are both genuses of which type of plants?
标准：["flowering plants"]
答案：orchids
理由：逐题审阅最终答案与标准：orchids / ["flowering plants"]；实体、数值、时间或所问字段不一致，维持错误。

### row 811：incorrect
The eastern coast of Ivan Zammit's birth city is located along what body of water?
标准：["Grand Harbour"]
答案：Mediterranean Sea
理由：逐题审阅最终答案：Mediterranean Sea；标准：["Grand Harbour"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 812：incorrect
I Like 'em Big and Stupid was a single whose B-side was played on the show of the record collector specializing in what type of music?
标准：["novelty songs"]
答案：music
理由：逐题审阅最终答案与标准：music / ["novelty songs"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：John Forzani
理由：逐题审阅最终答案：John Forzani；标准：["Dave Thomas"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 817：label_issue
Who authorized this infantry that was organized in the northern states during the Civil War and was commanded by RObert GOuld Shaw?
标准：["Emancipation Proclamation"]
答案：President Lincoln
理由：问题问授权者，标签给Emancipation Proclamation文件，答案给President Lincoln人物；标签字段类型疑误，不直接加分。

### row 818：incorrect
Which jazz singer has a 2003 album entitled The Boy Next Door?
标准：["Stacey Kent"]
答案：Lil' Mo
理由：逐题审阅最终答案与标准：Lil' Mo / ["Stacey Kent"]。实体、数值、时间或所问字段不一致，维持错误。

### row 819：incorrect
Stabat Mater was written by a composer of what nationality?
标准：["Polish"]
答案：Italian
理由：逐题审阅最终答案：Italian；标准：["Polish"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 821：incorrect
Which was formed first, Noori or Test Icicles?
标准：["Noori"]
答案：Test Icicles
理由：逐题审阅最终答案与标准：Test Icicles / ["Noori"]；实体、数值、时间或所问字段不一致，维持错误。

### row 826：incorrect
In which album was American rapper Kendrick Lamar's first number-one single on the US "Billboard" Hot 100 included?
标准：["\"1989\" (2014)"]
答案：Damn
理由：逐题审阅最终答案与标准：Damn / ["\"1989\" (2014)"]。实体、数值、时间或所问字段不一致，维持错误。

### row 828：incorrect
YouPorn was surpassed, in 2013, by competitor sites xHamster, Pornhub, LiveJasmin, and this website that is registered to the Polish company WGCZ Holding?
标准：["XVideos"]
答案：xHamster
理由：逐题审阅最终答案与标准：xHamster / ["XVideos"]；实体、数值、时间或所问字段不一致，维持错误。

### row 829：equivalent
Was Artie Ziff a good prom date for Marge?
标准：["Artie turns out to be a terrible date"]
答案：no
理由：no与标准terrible date直接否定good prom date为同义布尔回答。

### row 833：uncertain
Over how many centuries were the "dwelling place of the dead" built?
标准：["three centuries"]
答案：several centuries
理由：several centuries未提供标准three centuries的确定数量，精度不足。

### row 834：incorrect
Casino and Culto A La Vida are cocktails, one of which contains Havana Club 7 and what else?
标准：["It features Havana Club 7 Añejo Rum and Cranberry juice"]
答案：sugar
理由：逐题审阅最终答案与标准：sugar / ["It features Havana Club 7 Añejo Rum and Cranberry juice"]；实体、数值、时间或所问字段不一致，维持错误。

### row 838：incorrect
What film was written and directed by Joby Harold with music written by Samuel Sim?
标准：["Awake"]
答案：Home Fires
理由：逐题审阅最终答案：Home Fires；标准：["Awake"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 843：equivalent
Sony/Philips Digital Interface Format can transmit over what Toshiba optical fiber connector system?
标准：["TOSLINK (from \"Toshiba Link\") is a standardized optical fiber connector system."]
答案：TOSLINK
理由：TOSLINK直接提取标准长描述中的连接器系统名称。

### row 845：incorrect
Where in Greek mythology was the father of Benthesikyme venerated as a chief deity?
标准：["Pylos and Thebes"]
答案：sea god
理由：逐题审阅最终答案与标准：sea god / ["Pylos and Thebes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 847：equivalent
What "God Gave Me You" artist wrote the song "Imagine That" for Diamond Rio?
标准：["Bryan Shelton White"]
答案：Bryan White
理由：Bryan White与Bryan Shelton White同一歌手，省略中间名。

### row 849：incorrect
What format does a 1170 kHz AM station that Jim Angel presented the news for have?
标准：["an oldies format"]
答案：AM
理由：逐题审阅最终答案与标准：AM / ["an oldies format"]；实体、数值、时间或所问字段不一致，维持错误。

### row 852：incorrect
Who was born earlier, Robert Mulligan or James Foley?
标准：["Robert Patrick Mulligan"]
答案：James Foley
理由：逐题审阅最终答案：James Foley；标准：["Robert Patrick Mulligan"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 853：incorrect
What judge who was on the show "Dancing with the Stars" was born on the 31st of March, 1963?
标准：["Paul Joseph Mercurio"]
答案：Tom Bergeron
理由：逐题审阅最终答案与标准：Tom Bergeron / ["Paul Joseph Mercurio"]；实体、数值、时间或所问字段不一致，维持错误。

### row 854：incorrect
Which Kevin Costner movie included an actor who also starred in "Little Big League"?
标准：["\"Field of Dreams\""]
答案：The Upside of Anger
理由：逐题审阅最终答案与标准：The Upside of Anger / ["\"Field of Dreams\""]；实体、数值、时间或所問字段不一致，维持错误。

### row 855：incorrect
José Baviera starred in the 1962 film by the filmmaker who worked in what countries?
标准：["Spain, Mexico and France"]
答案：Argentina
理由：逐题审阅最终答案与标准：Argentina / ["Spain, Mexico and France"]；实体、数值、时间或所问字段不一致，维持错误。

### row 856：incorrect
What is the Latin phrase that describes Pope Julius II's efforts to remove Pope Alexander VI's name from the records?
标准：["Damnatio memoriae"]
答案：subvertare conatus est
理由：逐题审阅最终答案与标准：subvertare conatus est / ["Damnatio memoriae"]；实体、数值、时间或所问字段不一致，维持错误。

### row 857：incorrect
Brendon Urie wrote new perspective after firing which bassist?
标准：["Brent Wilson was fired"]
答案：Jon Walker
理由：逐题审阅最终答案：Jon Walker；标准：["Brent Wilson was fired"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 859：equivalent
How high on the US "Billboard" Hot 100 chart did Dan Smith's song reach in 2013?
标准：["number 5"]
答案：number five
理由：number five与number 5同一排名，英文数词和数字不同。

### row 860：incorrect
Which of the city at the south of Shelly Beach, New South Wales is a local government area in the Hunter region of New South Wales, Australia?
标准：["City of Newcastle"]
答案：Cessnock
理由：逐题审阅最终答案与标准：Cessnock / ["City of Newcastle"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：debut
理由：逐题审阅最终答案：debut；标准：["third"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 865：equivalent
How many laps did Harry Prowell run during the 10,000 metres race at the 1967 Pan American Games?
标准：["25 laps"]
答案：25
理由：25与25 laps同一圈数。

### row 866：equivalent
What conference does Ralphie the Buffalo's football team play in?
标准：["Pac-12"]
答案：Pac-12 Conference
理由：Pac-12 Conference与Pac-12同一体育联盟。

### row 867：incorrect
Who wrote more fictional works, Jim Thompson or Theodore H. White?
标准：["Thompson"]
答案：Theodore H. White
理由：逐题审阅最终答案与标准：Theodore H. White / ["Thompson"]；实体、数值、时间或所问字段不一致，维持错误。

### row 868：uncertain
What ranks does Jerry Kyd wear while captaining the largest warship ever built for the Royal Navy?
标准：["Captain while retaining the substantive rank of Commodore"]
答案：captain
理由：captain缺少明确所问ranks的Commodore实衔。

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

### row 878：incorrect
What New York representative and politician was defeated by Alan Hevesi in 2002?
标准：["John Faso"]
答案：John F. Ryan
理由：逐题审阅最终答案与标准：John F. Ryan / ["John Faso"]；实体、数值、时间或所问字段不一致，维持错误。

### row 880：incorrect
What year did the series on CBS, starring the actor who known for his role in "Rebel Without a Cause," air?
标准：["1952"]
答案：1951
理由：逐题审阅最终答案与标准：1951 / ["1952"]；实体、数值、时间或所问字段不一致，维持错误。

### row 882：incorrect
How many minutes outside of Carson City is the Moonlite BunnyRanch on Moonlight Road?
标准：["a few minutes"]
答案：about a mile
理由：about a mile为距离，题目要求分钟，未提供所问时间单位，不加分。

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
答案：Cooch
理由：逐题审阅最终答案与标准：Cooch / ["Jillian Belk"]；实体、数值、时间或所问字段不一致，维持错误。

### row 893：incorrect
Phillip Pullman's book set in a parallel universe featuring a character named Lyra Belacqua was put into audio in what year?
标准：["2002"]
答案：1995
理由：逐题审阅最终答案与标准：1995 / ["2002"]；实体、数值、时间或所问字段不一致，维持错误。

### row 894：incorrect
Which American comedian, actor, writer, producer and voice actor from "Hot & Fluffy" voices a character in The Nut Job?
标准：["Gabriel Iglesias"]
答案：Brendan Fraser
理由：逐题审阅最终答案与标准：Brendan Fraser / ["Gabriel Iglesias"]；实体、数值、时间或所问字段不一致，维持错误。

### row 895：incorrect
Which British engineering company is best known for its luxury motor cars in the era of British history that covers the brief reign of King Edward VII?
标准：["D. Napier & Son"]
答案：Rolls-Royce
理由：逐题审阅最终答案与标准：Rolls-Royce / ["D. Napier & Son"]；实体、数值、时间或所问字段不一致，维持错误。

### row 897：incorrect
When was the multinational group headquartered in the Netherlands adjacent to the Junction 27 Retail Park near Birstall, Batley, West Yorkshite, England, founded?
标准：["1943"]
答案：1907
理由：逐题审阅最终答案与标准：1907 / ["1943"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 904：equivalent
How many degrees and minutes south of the equator are the bone fragments of the extinct Ascension night heron found?
标准：["7°56'"]
答案：7°56' south
理由：7°56' south与题目已明确south of equator的标准7°56'一致。

### row 906：equivalent
The Battle of Nanchang was fought between the Chinese Nationals and what ground-based armed force of Japan?
标准：["Imperial Japanese Army"]
答案：Japan Imperial Japanese Army
理由：Japan Imperial Japanese Army明确给出标准Imperial Japanese Army，附加国家修饰。

### row 907：uncertain
When was the film containing the song "I'm still Here (Jim's Theme)" published?
标准：["November 27, 2002."]
答案：2002
理由：2002省略标准November 27发行日期，保留精度不足。

### row 908：incorrect
The Rome Protocols were signed by three Prime Ministers one of which was assassinated as part of what?
标准：["a failed coup attempt"]
答案：World War II
理由：逐题审阅最终答案与标准：World War II / ["a failed coup attempt"]；实体、数值、时间或所问字段不一致，维持错误。

### row 913：equivalent
Queen Elizabeth Grammar School, Wakefield is a type of secondary school that caters to children of what age cohort?
标准：["between 11 or 13 and 18"]
答案：11 to 18
理由：11 to 18给出标准between 11 or 13 and 18允许的11岁入学至18岁年龄范围。

### row 914：equivalent
Arundel Castle was damaged during a war between which two groups?
标准：["Parliamentarians (\"Roundheads\") and Royalists (\"Cavaliers\")"]
答案：the supporters of Charles I and the supporters of the English Parliament
理由：Charles I支持者与英国议会支持者分别对应Royalists与Parliamentarians，两个参战方完整同义表达。

### row 916：incorrect
Do the University of Florida and University of Texas System combine to have both a 2000 acre campus and over 216,000 students?
标准：["yes"]
答案：no
理由：逐题审阅最终答案与标准：no / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 923：uncertain
The university where Rolf Martin Theodor Dahlgren worked as a professor has how many employees?
标准：["9,000"]
答案：over 9,000
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 925：incorrect
The rapper whose debut album was titled "Thug Misses" has sold over how many records worldwide?
标准：["2 million"]
答案：over 1 million
理由：逐题审阅最终答案与标准：over 1 million / ["2 million"]；实体、数值、时间或所問字段不一致，维持错误。

### row 926：incorrect
What population ranking is the Oklahoma city located south of a wilderness area spanning over 5000 acres?
标准：["fifth-largest"]
答案：4
理由：逐题审阅最终答案与标准：4 / ["fifth-largest"]；实体、数值、时间或所问字段不一致，维持错误。

### row 928：incorrect
The 2011–12 Houston Rockets season began with the drafting of the player who now plays for what team?
标准：["Boston Celtics"]
答案：Dallas Mavericks
理由：逐题审阅最终答案与标准：Dallas Mavericks / ["Boston Celtics"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Avery August
理由：标签Fred MacMurray是演员且题目含was a professor，存在实体及身份歧义；答案Avery August不能与标签同一实体，疑误单列不加分。

### row 937：equivalent
What video game character did the voice actress in the animated film Alpha and Omega voice?
标准：["Kairi in the video game series \"Kingdom Hearts\"."]
答案：Kairi
理由：Kairi直接提取标准中的角色名，题目未要求游戏系列名。

### row 940：incorrect
Brahmarshi Vishwamitra is a 1991 film produced & directed by a man that served as Chief Minister of Andhra Pradesh for how many years?
标准：["seven"]
答案：three
理由：逐题审阅最终答案与标准：three / ["seven"]；实体、数值、时间或所問字段不一致，维持错误。

### row 942：incorrect
Were was the Mexican state after which there is Villa Unión, Sinaloa located?
标准：["tip of the Baja California"]
答案：Sinaloa
理由：逐题审阅最终答案与标准：Sinaloa / ["tip of the Baja California"]；实体、数值、时间或所问字段不一致，维持错误。

### row 943：incorrect
Penny Rae Bridges starred in a television sitcom with what other actor?
标准：["Ben Savage"]
答案：Ronny Cox
理由：逐题审阅最终答案与标准：Ronny Cox / ["Ben Savage"]；实体、数值、时间或所问字段不一致，维持错误。

### row 944：incorrect
What type of elevation does Aldgate railway station, Adelaide and Aldgate, South Australia have in common?
标准：["Hills"]
答案：suburban
理由：逐题审阅最终答案与标准：suburban / ["Hills"]；实体、数值、时间或所问字段不一致，维持错误。

### row 945：label_issue
In what year did Farda Amiga win a race at the Saratoga Race course?
标准：["(foaled February 1, 1999)"]
答案：1999
理由：题目问获胜年份，标签却给出生日期1999；答案1999与出生年份吻合不能证明获胜年份正确，标签疑误不加分。

### row 946：incorrect
A celebrity magazine that has featured Snoop Dogg and footballers such as Riyad Mahrez and the creator's team-mate Juan Mata was launched by which former Manchester United player?
标准：["Ferdinand"]
答案：Jamie Redknapp
理由：逐题审阅最终答案与标准：Jamie Redknapp / ["Ferdinand"]；实体、数值、时间或所问字段不一致，维持错误。

### row 949：incorrect
Who is older, Hampton Del Ruth or Ted Kotcheff?
标准：["Hampton Del Ruth"]
答案：Ted Kotcheff
理由：逐题审阅最终答案与标准：Ted Kotcheff / ["Hampton Del Ruth"]；实体、数值、时间或所問字段不一致，维持错误。

### row 955：incorrect
What group of Elektra Records recording artists are known to be an indie pop band?
标准：["Saint Motel"]
答案：Little Boots
理由：逐题审阅最终答案与标准：Little Boots / ["Saint Motel"]；实体、数值、时间或所问字段不一致，维持错误。

### row 957：incorrect
Carlos Alberto Hurtado played on loan from a mexican team which plays where?
标准：["Estadio Victoria"]
答案：Estadio Víctor Manuel Reyna
理由：逐题审阅最终答案与标准：Estadio Víctor Manuel Reyna / ["Estadio Victoria"]；实体、数值、时间或所问字段不一致，维持错误。

### row 958：equivalent
What song was created by the group consisting of Jeffrey Jey, Maurizio Lobina and Gabry Ponte and released on 15 January 1999?
标准：["Blue"]
答案：Blue (Da Ba Dee)
理由：Blue (Da Ba Dee)与Blue同一Eiffel 65歌曲的完整名和短名。

### row 961：incorrect
Which of Aaron Goodwin client was born in May 31, 1984?
标准：["Nate Robinson"]
答案：Candace Parker
理由：逐题审阅最终答案：Candace Parker；标准：["Nate Robinson"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 962：uncertain
Who were the live-in lovers of the founder of "Playboy" magazine in 1999 and 2000?
标准：["Bentley Twins"]
答案：Sandy Bentley
理由：Sandy Bentley仅给Bentley Twins之一，复数对象未答全。

### row 965：equivalent
Taylor Momsen and Craig Mabbitt from Escape the Fate have what in common?
标准：["lead singer"]
答案：lead vocalist
理由：lead vocalist与lead singer同义。

### row 968：incorrect
What trio was the songwriter of "What Are We Doin' Lonesome" from?
标准：["trio with his younger brothers Steve and Rudy"]
答案：Randy Goodrum
理由：逐题审阅最终答案与标准：Randy Goodrum / ["trio with his younger brothers Steve and Rudy"]；实体、数值、时间或所问字段不一致，维持错误。

### row 970：uncertain
Who wrote the jukebox musical depicting the recording session between the "King of Rock and Roll" and 3 other famous musicians?
标准：["Floyd Mutrux and Colin Escott"]
答案：Colin Escott
理由：Colin Escott只给两位作者之一，Floyd Mutrux遗漏。

### row 972：uncertain
What was the first comic book written by the writer who had a series developed into a 2010 film with Bruce Willis and Morgan Freeman?
标准：["Transmetropolitan"]
答案：Lazarus Churchyard
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 974：incorrect
Which film was released first, The Watercolor or Pokémon: Arceus and the Jewel of Life?
标准：["Pokémon: Arceus and the Jewel of Life"]
答案：The Watercolor
理由：逐题审阅最终答案：The Watercolor；标准：["Pokémon: Arceus and the Jewel of Life"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 975：equivalent
Which record label released Van Morrison's "I've Been Working" on the album "His Band and the Street Choir"?
标准：["Warner Bros"]
答案：Warner Bros. Records
理由：Warner Bros. Records与Warner Bros在唱片厂牌问题下同一机构。

### row 976：incorrect
Why is Minister Pool important to Black Country and the West Midlands in England?
标准：["defence of the Cathedral"]
答案：important to Black Country and the West Midlands
理由：逐题审阅最终答案与标准：important to Black Country and the West Midlands / ["defence of the Cathedral"]；实体、数值、时间或所问字段不一致，维持错误。

### row 978：equivalent
Oklahoma State Cowboys are part of what NCAA Division?
标准：["NCAA Division I"]
答案：Division I
理由：题目限定NCAA，Division I与NCAA Division I为相同大学体育组别。

### row 979：incorrect
What musician is ranked 9th in the Top 100 Greatest Metal Guitarists and started a band in 1990 in Los Angeles, California?
标准：["Adam Thomas Jones"]
答案：James Hetfield
理由：逐题审阅最终答案与标准：James Hetfield / ["Adam Thomas Jones"]；实体、数值、时间或所问字段不一致，维持错误。

### row 980：equivalent
What city is home to the private research university Jung Seul-ki swam for?
标准：["Seoul, South Korea"]
答案：Seoul
理由：题目只问city，Seoul完整回答Seoul, South Korea中的城市。

### row 983：incorrect
Name the movie that was cowritten by Paul Rudd and the director of the 2011 British science fiction horror comedy film written and directed by Joe Cornish and starring John Boyega, Nick Frost, Jodie Whittaker and Luke Treadaway.?
标准：["Ant-Man"]
答案：Attack the Block
理由：逐题审阅最终答案与标准：Attack the Block / ["Ant-Man"]；实体、数值、时间或所问字段不一致，维持错误。

### row 984：incorrect
This British television series was adapted from one of the better-known novels of a 19th-century writer and was first published in what magazine?
标准：["Household Words"]
答案：The Athenaeum
理由：逐题审阅最终答案与标准：The Athenaeum / ["Household Words"]；实体、数值、时间或所问字段不一致，维持错误。

### row 986：incorrect
Kevin Watson currently manages which Southern League football team?
标准：["Bishop's Stortford"]
答案：Maldon & Tiptree
理由：逐题审阅最终答案：Maldon & Tiptree；标准：["Bishop's Stortford"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 987：incorrect
Which one between Milium and Eucommia lives more widely spread across the world?
标准：["Milium"]
答案：Eucommia
理由：逐题审阅最终答案与标准：Eucommia / ["Milium"]；实体、数值、时间或所問字段不一致，维持错误。

### row 988：incorrect
Salisbury Woodland Gardens links a zoo with a park designed and built under the watchful eye of who?
标准：["Thomas Mawson"]
答案：Blackpool Corporation
理由：逐题审阅最终答案与标准：Blackpool Corporation / ["Thomas Mawson"]；实体、数值、时间或所问字段不一致，维持错误。

### row 989：incorrect
Who else besides "The Golden Jet" was born in Point Anne, Ontario?
标准：["Dennis Hull, as well as painter Manley MacDonald."]
答案：Bobby Hull
理由：逐题审阅最终答案与标准：Bobby Hull / ["Dennis Hull, as well as painter Manley MacDonald."]；实体、数值、时间或所问字段不一致，维持错误。

### row 990：equivalent
Jessica Ashley has recorded her own songs and has also written songs for which singer known for her song "Leave (Get Out)"?
标准：["Joanna Noëlle Levesque"]
答案：JoJo
理由：JoJo与Joanna Noëlle Levesque同一歌手的艺名和本名。

### row 992：uncertain
What was the former name of the company which operates Hunterston Terminal?
标准：["Peel Holdings"]
答案：Peel Group
理由：Peel Group与标签Peel Holdings涉及现名和旧名，题目明确问former name，不能省略时间角色而按同机构加分。

### row 995：incorrect
What is another name for the butterfly of the Hesperiidae family that is found in the third largest country in Africa?
标准：["the buff-tipped skipper"]
答案：Skipper
理由：Skipper为更宽类别，缺少buff-tipped限定，不是同一具体蝶种别名。

### row 996：equivalent
The Runge-Kutta methods were developed by M.W. Kutta and a German mathematician, physicist, and Spectroscopist that was born in what year?
标准：["1856"]
答案：30 August 1856
理由：30 August 1856明确给出所问出生年份1856并附加相容月日。

### row 998：equivalent
Where did Ian Harland study prior to studying at the oldest college at the University of Cambridge?
标准：["The Dragon School in Oxford"]
答案：The Dragon School
理由：The Dragon School与The Dragon School in Oxford同一学校，省略题中语境下非必要地点。

### row 999：incorrect
Which team featured in both the 2012 and 2011 Cops del Rey Finals ?
标准：["Barcelona"]
答案：Athletic Bilbao
理由：逐题审阅最终答案与标准：Athletic Bilbao / ["Barcelona"]。实体、数值、时间或所问字段不一致，维持错误。

### row 1001：incorrect
The Bodie & Benton Railway was a narrow gauge common carrier railroad in California, from the Mono Mills to a terminus in a ghost town located how many miles away from Lake Tahoe ?
标准：["75 mi"]
答案：32 miles
理由：逐题审阅最终答案与标准：32 miles / ["75 mi"]。实体、数值、时间或所问字段不一致，维持错误。

### row 1002：incorrect
What was the original name of the female singing group that recorded "The Happening"?
标准：["The Primettes"]
答案：The Supremes
理由：逐题审阅最终答案：The Supremes；标准：["The Primettes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1003：incorrect
For which team does Mads Bødker player that is controlled by Danmarks Ishockey Union?
标准：["Denmark men's national ice hockey"]
答案：Ottawa Senators
理由：逐题审阅最终答案与标准：Ottawa Senators / ["Denmark men's national ice hockey"]；实体、数值、时间或所问字段不一致，维持错误。

### row 1007：incorrect
What actor played the male lead in a teen comedy about a high school nerd directed by Steve Rash?
标准：["Patrick Dempsey"]
答案：Adrien Brody
理由：逐题审阅最终答案与标准：Adrien Brody / ["Patrick Dempsey"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 1014：equivalent
Josh Trank and Mike Valerio both work in what industry?
标准：["entertainment"]
答案：film
理由：两人从事film，回答同一entertainment产业中的电影行业；所问共同行业已明确。

### row 1015：equivalent
What Andy Williams' album did a song written by Charles Wesley appear on?
标准：["The Andy Williams Christmas Album"]
答案：The Christmas Album
理由：问题已明确Andy Williams，The Christmas Album在该语境中指The Andy Williams Christmas Album，省略题中艺术家姓名。

### row 1017：equivalent
What role in the TV show "Death in Paradise" was played by the man who performed with Alexander Armstrong in the podcast "Timeghost"?
标准：["Richard Poole"]
答案：DI Richard Poole
理由：DI Richard Poole与Richard Poole同一角色，附加警衔。

### row 1018：uncertain
John E. EchoHawk is a leading member in a social movement that wants to reverse what ?
标准：["the paternalistic policies enacted upon Native American tribes"]
答案：termination of federal tribe recognition
理由：termination of federal tribe recognition为具体政策，标准为对部落的paternalistic policies总体，范围与内容未完全确认等价，不加分。

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
