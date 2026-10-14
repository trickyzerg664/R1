# T1024语义复核：checkpoint60

标准：T1024-equivalence-v1

原始EM不变；只对明确等价的最终答案加分。标签错误、歧义、缺关键字段不计新增正确。

{
  "model": "checkpoint60",
  "policy": "T1024-equivalence-v1",
  "evaluation_complete": true,
  "review_complete": true,
  "n": 1024,
  "original_correct": 475,
  "equivalent_added": 149,
  "incorrect": 305,
  "uncertain": 80,
  "label_issue": 15,
  "pending": 0,
  "original_em": 0.4638671875,
  "semantic_correct_confirmed": 624,
  "semantic_accuracy": 0.609375,
  "records_digest": "8b2030a90ea21be54dbd39d7271c7e8965525df7648bf56d051296811d3dcc14",
  "sources": {
    "nq": {
      "n": 335,
      "original_correct": 171,
      "semantic_correct": 209
    },
    "hotpotqa": {
      "n": 689,
      "original_correct": 304,
      "semantic_correct": 415
    }
  }
}

## EM错题逐项裁定

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
答案：more than 115,000
理由：逐题审阅最终答案与标准：more than 115,000 / ["79,540 (2015)", "79,540"]；实体、数值、时间或所问字段不一致，维持错误。

### row 12：uncertain
where does the spinal cord become cauda equina?
标准：["L1 or L2", "the conus medullaris"]
答案：lumbar enlargement
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 15：uncertain
how did the dominican republic get its name?
标准：["patron saint, Saint Dominic"]
答案：Santo Domingo
理由：Santo Domingo为历史名称/首都及圣名相关来源，未明确回答patron saint Saint Dominic，保留命名路径歧义。

### row 21：incorrect
when was the last time an american won the new york marathon?
标准：["2009", "2017"]
答案：2018
理由：逐题审阅最终答案与标准：2018 / ["2009", "2017"]；实体、数值、时间或所问字段不一致，维持错误。

### row 25：uncertain
who starred in the movie the day the earth stood still?
标准：["Jennifer Connelly", "Jaden Smith", "Kyle Chandler", "Keanu Reeves", "Jon Hamm", "Kathy Bates", "John Cleese"]
答案：Michael Rennie
理由：电影1951版与2008版主演不同，题目未标年份；不作为与标准2008版演员等价。

### row 26：incorrect
who has majority in the house and senate?
标准：["Republican"]
答案：Republican Party
理由：逐题审阅最终答案：Republican Party；标准：["Republican"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 36：equivalent
when does middle-earth shadow of mordor come out?
标准：["September 2014"]
答案：September 30, 2014
理由：September 30, 2014属于标准September 2014；给出更精确且无冲突的发行日期。

### row 37：incorrect
who does bryce dallas howard play in the grinch?
标准：["Surprised Who"]
答案：Cindy Lou Who
理由：逐题审阅最终答案：Cindy Lou Who；标准：["Surprised Who"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 39：incorrect
who was the declaration of independence written for?
标准：["the Second Continental Congress"]
答案：the independence of the United States
理由：逐题审阅最终答案与标准：the independence of the United States / ["the Second Continental Congress"]；实体、数值、时间或所问字段不一致，维持错误。

### row 40：incorrect
what disney cartoon character's middle name is fauntleroy?
标准：["Donald Duck", "Donald Fauntleroy Duck"]
答案：Cedric Errol
理由：逐题审阅最终答案：Cedric Errol；标准：["Donald Duck", "Donald Fauntleroy Duck"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 42：incorrect
communities of similar organisms found in a particular environment are called?
标准：["species", "habitat"]
答案：community
理由：逐题审阅最终答案：community；标准：["species", "habitat"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 48：uncertain
who died in the first episode of stranger things?
标准：["Benny"]
答案：the owner
理由：the owner未说明哪位店主，角色描述不足以唯一确定标准Benny。

### row 49：incorrect
when did equus first appear in fossil record?
标准：["1820s", "~3.5 million years old", "about 3.5 mya"]
答案：54 million years ago
理由：逐题审阅最终答案：54 million years ago；标准：["1820s", "~3.5 million years old", "about 3.5 mya"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 52：uncertain
where is wake forest located in north carolina?
标准：["78.51889°W", "in Franklin and Wake counties", "35.97333°N"]
答案：Winston-Salem, North Carolina
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 55：incorrect
what episode does goku give up against cell?
标准：["165", "180"]
答案：34
理由：逐题审阅最终答案：34；标准：["165", "180"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 62：uncertain
when did the broncos win the super bowl?
标准：["1998", "2015", "1997"]
答案：Super Bowl XXXII
理由：Super Bowl XXXII标赛事届次，标准给年份；没有显式给出问题所问时间。

### row 65：incorrect
what was the tower of london originally used for?
标准：["a royal residence", "as a royal residence"]
答案：a timber fortification
理由：逐题审阅最终答案与标准：a timber fortification / ["a royal residence", "as a royal residence"]；实体、数值、时间或所问字段不一致，维持错误。

### row 68：equivalent
where are they playing the superbowl at this year?
标准：["Minneapolis, Minnesota"]
答案：U.S. Bank Stadium in Minneapolis, Minnesota
理由：U.S. Bank Stadium in Minneapolis, Minnesota给出标准Minneapolis, Minnesota相容的具体比赛球场。

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
答案：Nikki Reed
理由：逐题审阅最终答案与标准：Nikki Reed / ["Caroline Forbes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 76：incorrect
how much is the united states in debt to china?
标准：["$1.06 trillion", "1,200.5"]
答案：$1.16 trillion
理由：逐题审阅最终答案与标准：$1.16 trillion / ["$1.06 trillion", "1,200.5"]；实体、数值、时间或所问字段不一致，维持错误。

### row 77：equivalent
where in the bible is the book of revelation?
标准：["last book", "in the New Testament"]
答案：New Testament
理由：New Testament与in the New Testament相同，只省略介词。

### row 78：equivalent
what happened to western rome after it fell?
标准：["divided into several successor polities"]
答案：several successor polities
理由：题目问西罗马灭亡后结果，several successor polities表达标准分裂为多个继承政体的结果。

### row 79：incorrect
who are the nbc olympic ice skating commentators?
标准：["Jonny Moseley", "Tanith White", "Chris Vosters", "Luke Van Valin", "Charlie White", "Johnny Weir", "Tara Lipinski", "Andrea Joyce", "Terry Gannon"]
答案：Tom Hammond
理由：逐题审阅最终答案：Tom Hammond；标准：["Jonny Moseley", "Tanith White", "Chris Vosters", "Luke Van Valin", "Charlie White", "Johnny Weir", "Tara Lipinski", "Andrea Joyce", "Terry Gannon"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 80：incorrect
who dies in the lost city of z?
标准：["Manley"]
答案：Raleigh Rimell
理由：逐题审阅最终答案与标准：Raleigh Rimell / ["Manley"]；实体、数值、时间或所问字段不一致，维持错误。

### row 83：incorrect
how many episodes of season 5 of curse of oak island?
标准：["18"]
答案：10
理由：逐题审阅最终答案与标准：10 / ["18"]。实体、数值、时间或所问字段不一致，维持错误。

### row 84：uncertain
where is a simple gear train used in real life?
标准：["Automobile drivetrains"]
答案：mechanical watch or clock
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

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

### row 92：equivalent
when does season 18 of law and order svu start?
标准：["September 21, 2016"]
答案：Wednesday, September 21, 2016
理由：Wednesday, September 21, 2016为同一标准日期，附加正确星期。

### row 94：incorrect
where does the red river start and end in louisiana?
标准：["the Texas Panhandle"]
答案：southeastern end of the lake
理由：逐题审阅最终答案与标准：southeastern end of the lake / ["the Texas Panhandle"]；实体、数值、时间或所问字段不一致，维持错误。

### row 95：equivalent
who invented the first home video security system?
标准：["her husband Albert Brown", "Marie Van Brittan Brown"]
答案：Marie Brown
理由：轨迹明确该安全系统发明者称Marie Brown；与Marie Van Brittan Brown同一人。

### row 97：incorrect
in the dynastic cycle what is the right to rule called?
标准：["the Mandate of Heaven", "Mandate of Heaven"]
答案：Order of succession
理由：逐题审阅最终答案与标准：Order of succession / ["the Mandate of Heaven", "Mandate of Heaven"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 113：equivalent
what kind of beer is st pauli girl?
标准：["Special Dark", "Lager", "Non-Alcoholic Malt Beverage"]
答案：St. Pauli Girl Lager
理由：St. Pauli Girl Lager明确给标准允许的Lager类型，附加题中品牌。

### row 120：incorrect
where will the first round of march madness be played?
标准：["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]
答案：Alamodome in San Antonio, Texas
理由：逐题审阅最终答案与标准：Alamodome in San Antonio, Texas / ["Wichita State University", "Boise State University", "Duquesne University", "Big 12 Conference"]；实体、数值、时间或所问字段不一致，维持错误。

### row 121：incorrect
where can you find convergent boundaries on earth?
标准：["Mariana Trench"]
答案：Earth
理由：逐题审阅最终答案与标准：Earth / ["Mariana Trench"]；实体、数值、时间或所問字段不一致，维持错误。

### row 123：uncertain
what is the central idea of the poem the rime of ancient mariner?
标准：["a violation of nature"]
答案：A salvation story
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 124：equivalent
what is katie running from in safe haven?
标准：["her abusive husband"]
答案：abusive and alcoholic husband
理由：abusive and alcoholic husband保留标准的abusive husband指代，并附加不冲突描述。

### row 125：incorrect
who plays the mouse in alice in wonderland?
标准：["Barbara Windsor"]
答案：Sterling Holloway
理由：逐题审阅最终答案与标准：Sterling Holloway / ["Barbara Windsor"]；实体、数值、时间或所问字段不一致，维持错误。

### row 126：equivalent
who is the girl who played in the grinch?
标准：["Taylor Michel Momsen"]
答案：Taylor Momsen
理由：Taylor Momsen与Taylor Michel Momsen为同一演员，省略中间名。

### row 130：uncertain
what song did the titanic band play when it sank?
标准：["\"Autumn\""]
答案：Nearer, My God, to Thee
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 132：incorrect
when was the bridge over the hoover dam built?
标准：["2010"]
答案：2005
理由：逐题审阅最终答案与标准：2005 / ["2010"]；实体、数值、时间或所问字段不一致，维持错误。

### row 138：incorrect
when did the celebrities enter the big brother house?
标准：["February 7, 2018", "2017"]
答案：Sunday, July 3
理由：逐题审阅最终答案与标准：Sunday, July 3 / ["February 7, 2018", "2017"]；实体、数值、时间或所问字段不一致，维持错误。

### row 139：incorrect
who said some are born great in twelfth night?
标准：["Malvolio", "letter that Maria wrote"]
答案：William Shakespeare
理由：逐题审阅最终答案与标准：William Shakespeare / ["Malvolio", "letter that Maria wrote"]。实体、数值、时间或所问字段不一致，维持错误。

### row 140：equivalent
where does the edinburgh fringe festival take place?
标准：["in Edinburgh, Scotland"]
答案：Edinburgh, Scotland
理由：Edinburgh, Scotland与in Edinburgh, Scotland仅介词不同。

### row 142：equivalent
what is the job of the whip in congress?
标准：["to ensure party discipline"]
答案：ensure party discipline in a legislature
理由：ensure party discipline in a legislature与to ensure party discipline为同一职能。

### row 146：incorrect
who carried the usa flag in opening ceremony?
标准：["Erin Hamlin"]
答案：Dawn Staley
理由：逐题审阅最终答案：Dawn Staley；标准：["Erin Hamlin"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 147：equivalent
when was a series of unfortunate events published?
标准：["September 1999"]
答案：September 30, 1999
理由：轨迹明确The Bad Beginning released September 30, 1999，该更细日期与标准September 1999无冲突。

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
答案：Our Lady Peace
理由：逐题审阅最终答案与标准：Our Lady Peace / ["Kid Creole and the Coconuts", "Kid Creole & The Coconuts"]；实体、数值、时间或所问字段不一致，维持错误。

### row 155：incorrect
ben 10 ultimate alien episode 2 season 1?
标准：["Duped"]
答案：Ultimate Slime
理由：逐题审阅最终答案与标准：Ultimate Slime / ["Duped"]；实体、数值、时间或所问字段不一致，维持错误。

### row 157：incorrect
who played the music producer in pitch perfect 2?
标准：["Keegan-Michael Key"]
答案：Deke Sharon
理由：逐题审阅最终答案与标准：Deke Sharon / ["Keegan-Michael Key"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Royal Air Force (RAF)
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 162：equivalent
who has the talismans in sailor moon s?
标准：["Haruka and Michiru", "Haruka", "Michiru", "Sailor Pluto"]
答案：Haruka Tenoh
理由：Haruka Tenoh为标准Haruka同一角色完整名；标准已把Haruka作为可接受单项答案。

### row 163：uncertain
when did the nba add the three point line?
标准：["1979–80", "1979–80 season", "the 1979–80 season"]
答案：June 1979
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 164：incorrect
who wins the final fight in real steel?
标准：["Zeus"]
答案：Atom
理由：逐题审阅最终答案：Atom；标准：["Zeus"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 165：equivalent
who abolished the monarchy and declared france a republic?
标准：["Convention", "France's Legislative Assembly"]
答案：National Convention of France
理由：National Convention of France与Convention同一国民公会，附加全称与国家。

### row 166：uncertain
where does water come from in new york city?
标准：["The Catskill Aqueduct", "The Delaware Aqueduct", "The New Croton Aqueduct"]
答案：Catskill Mountains watershed
理由：Catskill Mountains watershed为水源区，标准为输水设施名称，相关但非同一对象。

### row 167：incorrect
who played ice queen in chronicles of narnia?
标准：["Tilda Swinton", "Laura Brent"]
答案：Claire Bloom
理由：逐题审阅最终答案与标准：Claire Bloom / ["Tilda Swinton", "Laura Brent"]；实体、数值、时间或所问字段不一致，维持错误。

### row 172：equivalent
where was 2017 beauty and the beast filmed?
标准：["Surrey, United Kingdom"]
答案：Shepperton Studios in Surrey, England
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 175：uncertain
who negotiated an agreement with japan concerning the future of korea?
标准：["the Korean Empire", "Empire of Japan", "Taft", "Korean Empire"]
答案：Japanese government
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

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

### row 187：incorrect
how many quarterbacks have a receiving touchdown in the superbowl?
标准：["1"]
答案：four
理由：逐题审阅最终答案与标准：four / ["1"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：blood stream
理由：blood stream与bloodstream为同义拼写。

### row 197：incorrect
who is the head a in pretty little liars?
标准：["CeCe Drake"]
答案：A
理由：逐题审阅最终答案与标准：A / ["CeCe Drake"]；实体、数值、时间或所问字段不一致，维持错误。

### row 199：uncertain
what are the 5 prohibitions of yom kippur?
标准：["No marital relations", "No wearing of leather shoes", "No eating and drinking", "No bathing or washing"]
答案：Total abstention from food and drink
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

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
答案：Vector
理由：逐题审阅最终答案与标准：Vector / ["displacement"]；实体、数值、时间或所问字段不一致，维持错误。

### row 205：equivalent
what is the first line of an http request to the server?
标准：["A request line", "the status line"]
答案：request/status line
理由：request/status line合并列出标准允许的request line和status line；不引入第三种答案。

### row 208：incorrect
a player that can shoot pass or dribble is considered to be?
标准：["Triple threat"]
答案：swingman
理由：逐题审阅最终答案：swingman；标准：["Triple threat"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 214：incorrect
what is the job of justice of the peace?
标准：["dispense summary justice"]
答案：judicial officer
理由：逐题审阅最终答案：judicial officer；标准：["dispense summary justice"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 221：incorrect
who is the best director in bollywood 2017?
标准：["Nitesh Tiwari"]
答案：N/A
理由：逐题审阅最终答案与标准：N/A / ["Nitesh Tiwari"]。实体、数值、时间或所问字段不一致，维持错误。

### row 223：incorrect
when was the cleveland browns last winning game?
标准：["2016"]
答案：2012
理由：逐题审阅最终答案与标准：2012 / ["2016"]；实体、数值、时间或所问字段不一致，维持错误。

### row 224：incorrect
who is in charge of new issues not mentioned in the constitution?
标准：["Congress"]
答案：judiciary
理由：逐题审阅最终答案与标准：judiciary / ["Congress"]；实体、数值、时间或所問字段不一致，维持错误。

### row 227：uncertain
when was the peak to peak gondola built?
标准：["in 2007 and 2008"]
答案：May 21, 2007
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 228：uncertain
what is an example of an americanized mexican food created by tex-mex cuisine?
标准：["fajitas", "nachos", "hard tacos", "chili con carne"]
答案：chimichangas
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 229：equivalent
what us president is the only president to become an eagle scout?
标准：["Ford"]
答案：Gerald Ford
理由：Gerald Ford与Ford指同一总统。

### row 234：equivalent
why the hole in the ozone layer over antarctica?
标准：["bromine", "chlorine", "methyl bromide", "CFCs", "halons"]
答案：chlorofluorocarbons or CFCs
理由：chlorofluorocarbons or CFCs为相同物质全称及缩写。

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

### row 237：uncertain
where does the brazos river start and stop?
标准：["Gulf of Mexico", "Llano Estacado"]
答案：head of Blackwater Draw, Curry County, New Mexico
理由：Blackwater Draw为上游相关地理点，未答标准起止点组合或同名位置。

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
答案：O
理由：逐题审阅最终答案：O；标准：["A+", "AB+"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 242：uncertain
when did the first battle of ypres end?
标准：["22 November 1914"]
答案：November 1914
理由：November 1914省略标准22日，保留精度不足。

### row 243：equivalent
what is the term of an official in the house of representatives?
标准：["two-year", "Speaker of the House", "Two years", "Representatives"]
答案：two-year term
理由：two-year term与two-year/Two years为同一两年任期。

### row 244：incorrect
when did the tradition of self government began in america?
标准：["1783"]
答案：1776
理由：逐题审阅最终答案与标准：1776 / ["1783"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 250：uncertain
who is currently serving as president of the senate?
标准：["Orrin Hatch", "Patrick Leahy"]
答案：Christine Kangaloo
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 251：equivalent
when did michael jordan return to the nba?
标准：["2001", "1995", "March 1995", "in March 1995"]
答案：September 25, 2001
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 253：incorrect
what was the ancient chinese umbrella used for?
标准：["a defense against rain"]
答案：parasols
理由：逐题审阅最终答案与标准：parasols / ["a defense against rain"]；实体、数值、时间或所问字段不一致，维持错误。

### row 254：equivalent
theme of the song roar by katy perry?
标准：["self-empowerment", "standing up for oneself"]
答案：standing up for oneself and self-empowerment
理由：最终答案把标准允许的self-empowerment与standing up for oneself组合表述。

### row 255：incorrect
when did teenage mutant ninja turtles come out?
标准：["1984"]
答案：August 8, 2014
理由：逐题审阅最终答案与标准：August 8, 2014 / ["1984"]。实体、数值、时间或所问字段不一致，维持错误。

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
答案：Havana Harbor, Cuba
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 265：incorrect
what year is the deer hunter set in?
标准：["late 1967", "1967"]
答案：1978
理由：逐题审阅最终答案与标准：1978 / ["late 1967", "1967"]。实体、数值、时间或所问字段不一致，维持错误。

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

### row 274：incorrect
who sings the song it ain't me?
标准：["Selena Gomez", "American singer Selena Gomez"]
答案：Norwegian DJ Kygo
理由：逐题审阅最终答案与标准：Norwegian DJ Kygo / ["Selena Gomez", "American singer Selena Gomez"]；实体、数值、时间或所问字段不一致，维持错误。

### row 276：uncertain
what is the first step in the evolution of the eye?
标准：["photoreceptor proteins that sense light", "eyespots"]
答案：Simple light detection
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 277：uncertain
when did john hart play the lone ranger?
标准：["from 1952 until 1953"]
答案：1952
理由：1952未完整回答1952 until 1953的时间段。

### row 278：uncertain
tools made from high-speed tool steel are generally used for what type of machining operations?
标准：["milling"]
答案：cutting tool material
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 279：incorrect
when does season 3 of the riveras start?
标准：["March 11, 2018"]
答案：November 6, 2017
理由：逐题审阅最终答案与标准：November 6, 2017 / ["March 11, 2018"]；实体、数值、时间或所问字段不一致，维持错误。

### row 282：incorrect
who lived in jamestown before the arrival of the english?
标准：["uninhabited"]
答案：Paspahegh people
理由：逐题审阅最终答案与标准：Paspahegh people / ["uninhabited"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 298：incorrect
which central american nations border the pacific ocean and the caribbean sea?
标准：["Nicaragua", "Costa Rica"]
答案：Belize
理由：逐题审阅最终答案与标准：Belize / ["Nicaragua", "Costa Rica"]；实体、数值、时间或所问字段不一致，维持错误。

### row 299：equivalent
where did the name huey helicopter come from?
标准：["originally designated HU-1"]
答案：HU-1
理由：HU-1直接给出标准originally designated HU-1中所问Huey名称来源。

### row 303：incorrect
when did the democratic party change its name?
标准：["the 1830s"]
答案：1844
理由：逐题审阅最终答案：1844；标准：["the 1830s"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 304：incorrect
who used morse code in world war 2?
标准：["naval bases", "warships"]
答案：United States
理由：逐题审阅最终答案：United States；标准：["naval bases", "warships"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 305：uncertain
who shot first in the shot heard around the world?
标准：["Americans acting under orders"]
答案：Ensign Robert Munroe
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 306：incorrect
where did the ashes from ash wednesday originate?
标准：["Pope Gregory I the Great"]
答案：the Gregorian Sacramentary of the late 8th century
理由：逐题审阅最终答案与标准：the Gregorian Sacramentary of the late 8th century / ["Pope Gregory I the Great"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 318：equivalent
who presides over the highest criminal court in a district?
标准：["District Judge"]
答案：District and Sessions judge
理由：District and Sessions judge与District Judge为所问地区最高刑事法院的地区/审判法官职位。

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
答案：a liturgical word in Judaism and Christianity
理由：逐题审阅最终答案与标准：a liturgical word in Judaism and Christianity / ["save, rescue, savior", "rescue", "savior", "save"]；实体、数值、时间或所问字段不一致，维持错误。

### row 326：incorrect
what is the salary of the ceo of microsoft?
标准：["$84.3 million", "$84.3 million (2018)"]
答案：$100 million
理由：逐题审阅最终答案与标准：$100 million / ["$84.3 million", "$84.3 million (2018)"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Buffalo thorn
理由：逐题审阅最终答案与标准：Buffalo thorn / ["silk floss tree"]；实体、数值、时间或所问字段不一致，维持错误。

### row 335：incorrect
Are Leopold Lummerstorfer and Valeria Sarmiento both authors?
标准：["no"]
答案：Yes
理由：逐题审阅最终答案：Yes；标准：["no"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Beth Quist
理由：逐题审阅最终答案与标准：Beth Quist / ["Karen O"]；实体、数值、时间或所问字段不一致，维持错误。

### row 343：incorrect
What is the colloquial name of the professional football team in which striker Frederico Chaves Guedos played?
标准：["Rooster"]
答案：Chaves
理由：逐题审阅最终答案：Chaves；标准：["Rooster"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 344：incorrect
Who wrote the book that inspired the name of the CD/DVD "Here at the End of All Things"?
标准：["J. R. R. Tolkien"]
答案：John Updike
理由：逐题审阅最终答案与标准：John Updike / ["J. R. R. Tolkien"]；实体、数值、时间或所问字段不一致，维持错误。

### row 345：incorrect
What park is just south of the location where the New York Jets played prior to moving to Shea Stadium?
标准：["Central Park"]
答案：Flushing Meadows–Corona Park
理由：逐题审阅最终答案：Flushing Meadows–Corona Park；标准：["Central Park"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：38
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 352：incorrect
Where does the train that runs from NYC and Miami station at in Florida?
标准：["Jacksonville station"]
答案：Miami station
理由：逐题审阅最终答案与标准：Miami station / ["Jacksonville station"]；实体、数值、时间或所问字段不一致，维持错误。

### row 353：incorrect
Ali Eren Balıkel started a restaurant which hosted a number of famous figures including an English actor who won three consecutive what?
标准：["BAFTA Awards for Best Actress"]
答案：Academy Award
理由：逐题审阅最终答案与标准：Academy Award / ["BAFTA Awards for Best Actress"]；实体、数值、时间或所问字段不一致，维持错误。

### row 355：incorrect
Who was the secretary to the Winter Queen?
标准：["Sir Francis Nethersole"]
答案：Agido
理由：逐题审阅最终答案与标准：Agido / ["Sir Francis Nethersole"]；实体、数值、时间或所问字段不一致，维持错误。

### row 356：equivalent
Tritonia and Phyteuma are both names for a what of plants?
标准：["genus"]
答案：genus of flowering plants
理由：genus of flowering plants保留标准genus分类，并补充相容植物限定。

### row 362：incorrect
James Stuart became a specialist of a rhythmic pattern charecterised by what?
标准：["characterised by a moderately fast to very fast tempo"]
答案：steady rock
理由：逐题审阅最终答案与标准：steady rock / ["characterised by a moderately fast to very fast tempo"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Ray Danton
理由：逐题审阅最终答案与标准：Ray Danton / ["Orson Welles"]。实体、数值、时间或所问字段不一致，维持错误。

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

### row 368：incorrect
What was the name of a land where Maria Anna of Spain's husband was king?
标准：["Hungary"]
答案：Spain
理由：逐题审阅最终答案：Spain；标准：["Hungary"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 369：incorrect
What year was the essay which Henry Louis Gates and Cornel West criticized in their book, "The Future of the Race" first published?
标准：["1903"]
答案：1994
理由：逐题审阅最终答案：1994；标准：["1903"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 370：uncertain
The languages Hussein Ali Mahfouz studied are spoken by how many people?
标准：["more than 330 million people"]
答案：330 million
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 371：incorrect
What is common between Matt Vasgersian and Michael Casey?
标准：["American"]
答案：beach volleyball player
理由：逐题审阅最终答案：beach volleyball player；标准：["American"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：The Grandmaster
理由：逐题审阅最终答案与标准：The Grandmaster / ["\"Hacksaw Ridge\""]；实体、数值、时间或所问字段不一致，维持错误。

### row 383：incorrect
Baadshah is an Indian action comedy film that was inspired by what Hong Kong action movie starring Jackie Chan and Richard Norton?
标准：["Mr. Nice Guy"]
答案：The Magic Crystal
理由：逐题审阅最终答案与标准：The Magic Crystal / ["Mr. Nice Guy"]；实体、数值、时间或所问字段不一致，维持错误。

### row 385：label_issue
Were Maurice Tourneur and Greg Mottola both American film directors?
标准：["French film director"]
答案：No
理由：布尔题标准写French film director，轨迹支持No；标签类型错误单列。

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

### row 392：incorrect
Which town was home to a forward for the Western New York Flash?
标准：["Oyster Bay"]
答案：Elma, New York
理由：逐题审阅最终答案与标准：Elma, New York / ["Oyster Bay"]；实体、数值、时间或所问字段不一致，维持错误。

### row 393：incorrect
Which team based in South Wales participated in a final game of 1980 Welsh Cup Final?
标准：["Newport County"]
答案：Cardiff City
理由：逐题审阅最终答案：Cardiff City；标准：["Newport County"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 394：incorrect
What man, born in 1963, was instrumental in bringing the Boston Red Sox to the stadium City of Palms Park in Fort Myers, Florida?
标准：["Mike Greenwell"]
答案：John Harrington
理由：逐题审阅最终答案与标准：John Harrington / ["Mike Greenwell"]。实体、数值、时间或所问字段不一致，维持错误。

### row 395：label_issue
Which musician's band contains more letters in it's name, Micky Dolenz or Jesse James Dupree?
标准：["George Michael Dolenz"]
答案：Jackyl
理由：题目问哪位音乐人，模型Jackyl给乐队名；标准也是人物名，保留问答实体类型问题。

### row 396：uncertain
Tui Flower and Julia child were both known for what?
标准：["Cooking"]
答案：food writer
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 397：equivalent
What are some foods that may have been served at the Hawaiin Cottage?
标准：["poi, Kalua pig, poke, lomi salmon, opihi, haupia"]
答案：Kalua pig
理由：题目要求举食品例子，Kalua pig为标准列举的一项合法食品；未明确要求答完全部六项。

### row 400：incorrect
Which band, Letters to Cleo or Screaming Trees, had more members?
标准：["Letters to Cleo"]
答案：Screaming Trees
理由：逐题审阅最终答案：Screaming Trees；标准：["Letters to Cleo"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Skidmore, Owings & Merrill
理由：逐题审阅最终答案：Skidmore, Owings & Merrill；标准：["architect Michael Graves"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Orchidaceae
理由：逐题审阅最终答案与标准：Orchidaceae / ["flowers"]；实体、数值、时间或所问字段不一致，维持错误。

### row 417：uncertain
Illmatic, the debut studio album by Nas which featured the song "N.Y. State of Mind", was released on what date by which record label?
标准：["April 19, 1994, by Columbia Records"]
答案：April 19, 1994
理由：逐题核对后存在精度不足、字段遗漏、范围/上下级关系或合法替代答案争议；相关不等于明确等价，暂不加分。

### row 419：incorrect
What is the name of one the ex-security officials that means The Institute?
标准：["Mossad"]
答案：Prague Security Studies Institute
理由：逐题审阅最终答案：Prague Security Studies Institute；标准：["Mossad"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 420：incorrect
How many albums have been released by the same band that released the "Trance" EP?
标准：["4 albums"]
答案：two
理由：逐题审阅最终答案：two；标准：["4 albums"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 421：incorrect
After partially sinking in 1994, Celestyal Crystal was rebuilt for the purpose of what Bermudian company?
标准：["Norwegian Cruise Line Holdings Ltd."]
答案：Celestyal Cruises
理由：逐题审阅最终答案：Celestyal Cruises；标准：["Norwegian Cruise Line Holdings Ltd."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 424：equivalent
Kasper Peter Schmeichel is the son of a professional footballer who was voted what in 1992 and 1993?
标准：["IFFHS World's Best Goalkeeper"]
答案：The World's Best Goalkeeper
理由：The World's Best Goalkeeper在题目所给1992/1993奖项语境中指同一IFFHS最佳守门员奖。

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

### row 429：equivalent
Thor Equities owns properties in Soho, which became known for what type of rental properties?
标准：["artists' lofts"]
答案：artists' lofts and art galleries
理由：明确含artists' lofts，并补充art galleries；没有否定或替换所问lofts。

### row 430：equivalent
The 1948 Commonwealth Prime Ministers' Conference was hosted by the Prime Minister from what British party?
标准：["Labour"]
答案：Labour Party
理由：Labour Party与Labour同一政党。

### row 434：uncertain
Which university did the third pick by the Philadelphia 76ers in the 2014 NBA draft attend before he was drafted?
标准：["University of Kansas"]
答案：Kansas Jayhawks
理由：Kansas Jayhawks为运动队，标准University of Kansas为大学；先保留转喻歧义。

### row 435：incorrect
Who is the original writer of the 1977 horror film?
标准：["Wes Craven"]
答案：Michael DeGaetano
理由：逐题审阅最终答案与标准：Michael DeGaetano / ["Wes Craven"]。实体、数值、时间或所问字段不一致，维持错误。

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
答案：filmmaker
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 439：uncertain
What is the pioneer who has a park dedicated to him near Lexington, North Carolina famous for?
标准：["Wilderness Road"]
答案：American pioneer
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 440：equivalent
The Gate is a song from the album scheduled for release in what month?
标准：["November 2017"]
答案：November
理由：题目只问month，November完整回答标准November 2017中的月份。

### row 441：incorrect
Who developed the jet fighters operated by the 41st Tactical Squadron of the Polish Air Force?
标准：["the Mikoyan design bureau"]
答案：Lockheed Martin
理由：逐题审阅最终答案与标准：Lockheed Martin / ["the Mikoyan design bureau"]；实体、数值、时间或所问字段不一致，维持错误。

### row 442：equivalent
The Porsche 968 was the last in a line of front-engined sports cars following the 944 and which earlier model?
标准：["924"]
答案：Porsche 924
理由：逐题核对完整最终答案，明确表达标准可接受的同一答案；句式、说明或形式差异不改变所问核心字段。

### row 444：incorrect
The subject of the biography "Name Dropper" was born in what year?
标准：["1961"]
答案：1891
理由：逐题审阅最终答案：1891；标准：["1961"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 445：equivalent
What was the title of the debut studio album by Weezer which contained the hit Buddy Holly and Undone – The Sweater Song?
标准：["The Blue Album"]
答案：Weezer
理由：问题限定debut，Weezer为1994同名首专The Blue Album；原始模型轨迹已明确别名关系。

### row 448：uncertain
Which plant genus is part of a family with a longer name, Morning glory or Rothmannia?
标准：["Morning glory"]
答案：Convolvulaceae
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 449：uncertain
What band did both Delores Holmes and an inductee to the Rock and Roll Hall of Fame sing in?
标准：["E Street Band"]
答案：Bruce Springsteen Band
理由：Bruce Springsteen Band与E Street Band并非可直接假定同一时期同一乐队。

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
答案：London
理由：逐题审阅最终答案：London；标准：["Chicago, IL"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 469：uncertain
Who was the brother of the wife of the Democratic Party nomination for Vice President in 1972?
标准：["President John F. Kennedy"]
答案：Robert F. Kennedy
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 470：incorrect
What is the name of  rocker, who was awarded "Rock Goddess of the Year" in the Annual Loudwide Music Awards, who sang with high pitched screams in her band's albums?
标准：["Maria Brink"]
答案：In This Moment
理由：逐题审阅最终答案：In This Moment；标准：["Maria Brink"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 481：uncertain
Where is the company that owns thanKing Horse pub restaurant chain based ?
标准：["Bury St Edmunds,"]
答案：England
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 482：incorrect
Where is the University Joe Odom played football for located?
标准：["West Lafayette, Indiana"]
答案：Natchitoches, Louisiana
理由：逐题审阅最终答案：Natchitoches, Louisiana；标准：["West Lafayette, Indiana"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 485：incorrect
Wiener Werkstätte Style was part of the movement that took place during what eras?
标准：["late 19th and early 20th centuries"]
答案：early 20th century
理由：逐题审阅最终答案：early 20th century；标准：["late 19th and early 20th centuries"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 489：incorrect
Where did the tribe Mato-tope chief over reside?
标准：["North Dakota"]
答案：Mandan tribe
理由：逐题审阅最终答案与标准：Mandan tribe / ["North Dakota"]；实体、数值、时间或所问字段不一致，维持错误。

### row 491：equivalent
Which author has won more Pulitzer Prizes, Thomas Friedman or Henri Bergson?
标准：["Thomas Loren Friedman"]
答案：Thomas Friedman
理由：Thomas Friedman与Thomas Loren Friedman同一人，省略中间名。

### row 493：incorrect
Whose given first name is longer, Theo Angelopoulos and Budd Boetticher (nicknames)?
标准：["Theodoros \"Theo\" Angelopoulos"]
答案：Budd Boetticher
理由：逐题审阅最终答案与标准：Budd Boetticher / ["Theodoros \"Theo\" Angelopoulos"]。实体、数值、时间或所问字段不一致，维持错误。

### row 497：incorrect
What month did the an online adult website whose last print magazine was published in the summer of 2007 recognize Nikita Gross?
标准：["January"]
答案：December 2010
理由：逐题审阅最终答案与标准：December 2010 / ["January"]；实体、数值、时间或所问字段不一致，维持错误。

### row 498：incorrect
Which airport is busier, Palm Springs International Airport or Trenton–Mercer Airport?
标准：["Trenton–Mercer Airport"]
答案：Palm Springs International Airport
理由：逐题审阅最终答案：Palm Springs International Airport；标准：["Trenton–Mercer Airport"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 500：incorrect
What was the third studio album released by Richard Melville Hall?
标准：["Everything Is Wrong"]
答案：Keys to the World
理由：逐题审阅最终答案与标准：Keys to the World / ["Everything Is Wrong"]；实体、数值、时间或所问字段不一致，维持错误。

### row 501：uncertain
Where is the university located in which the current editor-in-chief of Review of Policy Reseach is from?
标准：["Toronto"]
答案：Ryerson University
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 504：incorrect
Where is the headquarters for the service broadcaster the show Tenko is on?
标准：["Broadcasting House in London"]
答案：Australian Broadcasting Corporation
理由：逐题审阅最终答案与标准：Australian Broadcasting Corporation / ["Broadcasting House in London"]；实体、数值、时间或所问字段不一致，维持错误。

### row 509：incorrect
Where is the closest relative to the whale located?
标准：["sub-Saharan Africa"]
答案：hippopotamuses
理由：逐题审阅最终答案：hippopotamuses；标准：["sub-Saharan Africa"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 510：incorrect
What English campaigner for the suffragette movement did Angela Down portray?
标准：["Sylvia Pankhurst"]
答案：Emmeline Pankhurst
理由：逐题审阅最终答案：Emmeline Pankhurst；标准：["Sylvia Pankhurst"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 511：incorrect
Christopher Oscar Pena was recognized by an entertainment-industry brand aimed at what?
标准：["people working in film and the performing arts"]
答案：sexuality
理由：逐题审阅最终答案：sexuality；标准：["people working in film and the performing arts"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 522：incorrect
Were Dee Dee Ramone and Ben Weasel ever in the same band?
标准：["no"]
答案：Yes
理由：逐题审阅最终答案：Yes；标准：["no"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 532：incorrect
Where is the headquarter of the American multinational chemical corporation who's part is Dow AgroSciences?
标准：["Midland, Michigan, United States"]
答案：Indianapolis, Indiana
理由：逐题审阅最终答案：Indianapolis, Indiana；标准：["Midland, Michigan, United States"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 534：incorrect
What is the prefix given to the end of the name to avoid confusion for the winner of the 1996 Record of the Year Grammy?
标准：["II"]
答案：The Best
理由：逐题审阅最终答案与标准：The Best / ["II"]；实体、数值、时间或所问字段不一致，维持错误。

### row 535：incorrect
When was the movie released that starred an American male actor born on February 28, 1923 and was written by Christopher Knopf?
标准：["December 23, 1977"]
答案：1998
理由：逐题审阅最终答案与标准：1998 / ["December 23, 1977"]；实体、数值、时间或所问字段不一致，维持错误。

### row 536：incorrect
Who is the author of the 1993 production Madge Ryan participated in?
标准：["Euripides"]
答案：Joe Orton
理由：逐题审阅最终答案与标准：Joe Orton / ["Euripides"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：The X Factor
理由：逐题审阅最终答案与标准：The X Factor / ["You Can Be a Star"]；实体、数值、时间或所问字段不一致，维持错误。

### row 541：incorrect
What two singers who worked together on the song I Would Like to See You Again also performed as part of a country music group which was active between 1985 and 1995?
标准：["Johnny Cash, Waylon Jennings"]
答案：Johnny Cash
理由：明确要求两位歌手，最终只给Johnny Cash，遗漏Waylon Jennings，不加分。

### row 542：incorrect
The M104 155mm Projectile was specifically designed to carry about 11.7 pounds of what prototypical substance?
标准：["mustard gas"]
答案：white phosphorus
理由：逐题审阅最终答案：white phosphorus；标准：["mustard gas"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 543：equivalent
What was the address of the building on U.S. Route 3 that was the tallest building in New Hampshire when completed in 1972?
标准：["1000 Elm Street"]
答案：1000 Elm Street, Manchester, New Hampshire
理由：1000 Elm Street, Manchester, New Hampshire保留标准地址1000 Elm Street并补充相容城市和州。

### row 544：incorrect
In what part of England is John Folwes' country house located?
标准：["West Dorset, South West England."]
答案：Berkshire
理由：逐题审阅最终答案：Berkshire；标准：["West Dorset, South West England."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 545：incorrect
What is the global rank by population of the city that Daewoong Pharmaceutical Co., Ltd is based in?
标准：["world's 16th largest city"]
答案：third
理由：逐题审阅最终答案：third；标准：["world's 16th largest city"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 546：equivalent
what year was the cover artist of Multiverse: Exploring Poul Anderson's Worlds born ?
标准：["September 13, 1960"]
答案：1960
理由：题目只问year，1960完整提取标准September 13, 1960中的年份。

### row 548：incorrect
An actress in Strange Fruit was better known for a role in CBS sitcom.  Which sitcom is this actress better known for than her role in Strange Fruit?
标准：["The Jeffersons"]
答案：The King of Queens
理由：逐题审阅最终答案：The King of Queens；标准：["The Jeffersons"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 549：incorrect
Who was born first Doug Liman or Saul Metzstein?
标准：["Douglas Eric \"Doug\" Liman"]
答案：Saul Metzstein
理由：逐题审阅最终答案：Saul Metzstein；标准：["Douglas Eric \"Doug\" Liman"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 550：incorrect
What year was George Harrison's top UK charted song voted the nations 11th favorite 1980s number?
标准：["2015"]
答案：1981
理由：逐题审阅最终答案：1981；标准：["2015"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 553：incorrect
The Environment Act 1995 passed under the tutelage of a politician associated with what political party?
标准：["British Conservative Party"]
答案：United Kingdom government's Department for Environment, Food and Rural Affairs (DEFRA)
理由：逐题审阅最终答案与标准：United Kingdom government's Department for Environment, Food and Rural Affairs (DEFRA) / ["British Conservative Party"]；实体、数值、时间或所问字段不一致，维持错误。

### row 555：incorrect
With whom did Lever Brothers merge to create an Indonesian soap factory?
标准：["Margarine Unie"]
答案：Lever Brothers
理由：逐题审阅最终答案：Lever Brothers；标准：["Margarine Unie"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 556：uncertain
the work of The Last Poets and Gil Scott Heron inspired music that fits under what larger sub-genre?
标准：["underground hip hop"]
答案：hip hop
理由：hip hop省略所问sub-genre的underground限定。

### row 557：incorrect
Which date occurred first the end of Riley Hawk's amateur career or end of production of Skateboard Magazine ?
标准：["October 15, 2013"]
答案：Winter 1964
理由：逐题审阅最终答案与标准：Winter 1964 / ["October 15, 2013"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Vincent Wong
理由：逐题审阅最终答案：Vincent Wong；标准：["Bosco Wong Chung-chak"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 564：equivalent
What is the first name of the author who wrote the play in which Rønnaug Alten made her stage debut at Den Nationale Scene in 1930 as "Viola"?
标准：["William"]
答案：William Shakespeare
理由：William Shakespeare明确给所问first name William，并附加姓氏。

### row 566：incorrect
Which film was was made first The Young Black Stallion or Wild Hearts Can't Be Broken?
标准：["Wild Hearts Can’t Be Broken"]
答案：The Black Stallion
理由：逐题审阅最终答案：The Black Stallion；标准：["Wild Hearts Can’t Be Broken"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 567：incorrect
Are Billy and Barak both breeds of scenthound? (Barak is also known as a Bosnian Coarse-haired Hound)?
标准：["yes"]
答案：No
理由：逐题审阅最终答案与标准：No / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Lightning connector
理由：逐题审阅最终答案：Lightning connector；标准：["Retina Display"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 572：incorrect
Rejuvelac is kind of grain water invented and promoted by a "holistic health" practitioner born in which year ?
标准：["1909"]
答案：1939
理由：逐题审阅最终答案与标准：1939 / ["1909"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 575：equivalent
How many years in prison did the Norfolk farmer defended by Anthony Scrivener serve?
标准：["three"]
答案：three years
理由：three years与three在服刑年数问题下同一数量，附加单位。

### row 577：incorrect
What is Rachelle Amy Beinart's role in the film that follows a group of rebels on a mission?
标准：["stunt performances"]
答案：Child of the Forest
理由：逐题审阅最终答案与标准：Child of the Forest / ["stunt performances"]；实体、数值、时间或所问字段不一致，维持错误。

### row 578：incorrect
The water-based dark ride in Walt Disney is connected to a song known for what?
标准：["most performed song of all time"]
答案：anthem-like statements
理由：逐题审阅最终答案与标准：anthem-like statements / ["most performed song of all time"]；实体、数值、时间或所问字段不一致，维持错误。

### row 579：incorrect
What is this fictional scientifically and technologically advanced militaristic alien race, from which Sequoia descends, is called?
标准：["the Ruul"]
答案：Kree
理由：逐题审阅最终答案：Kree；标准：["the Ruul"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 581：label_issue
Who did the Star and Dagger bass player marry?
标准：["Sean Yseult."]
答案：Martin Bendeler
理由：题目问丈夫，标准Sean Yseult为贝斯手本人；标签疑误，不按同义修正。

### row 582：incorrect
Which American pro basketball player who won gold at the 2008 Summer Olympics was signed by the Utah Jazz during the 2005-05 offseason?
标准：["Carlos Austin Boozer Jr."]
答案：Deron Williams
理由：逐题审阅最终答案：Deron Williams；标准：["Carlos Austin Boozer Jr."]。所答实体、数值或所问字段不一致，不作等价修正。

### row 586：equivalent
Where is the location of Liberty Square park in Disneyland California?
标准：["Anaheim"]
答案：Disneyland Park in Anaheim, California
理由：明确给Anaheim, California，附加Disneyland Park地点限定而未改变标准城市。

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
答案：Albany County, New York
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

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
答案：two
理由：逐题审阅最终答案与标准：two / ["five times"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 608：uncertain
Ralph Faudree served as the American equivalent to what United Kingdom and Australian position?
标准：["pro-vice-chancellor"]
答案：provost
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

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

### row 612：uncertain
What do Josef Veltjens and Hermann Goering have in common?
标准：["A veteran World War I fighter pilot ace"]
答案：German
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 613：incorrect
How many people live in the County serviced by The Collier Area Transit system?
标准：["321,520"]
答案：332,427
理由：逐题审阅最终答案与标准：332,427 / ["321,520"]；实体、数值、时间或所问字段不一致，维持错误。

### row 614：incorrect
In addition to the individual born on August 21, who else wrote He's The Great Imposter?
标准：["Sharon Sheeley"]
答案：Robert Crichton
理由：逐题审阅最终答案：Robert Crichton；标准：["Sharon Sheeley"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 615：incorrect
Who appeared in the Olympics first, Piet Norval or Emilio Sánchez?
标准：["Sanchez"]
答案：Piet Norval
理由：逐题审阅最终答案：Piet Norval；标准：["Sanchez"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 625：uncertain
What was the given name of the singer who is most closely associated with The Dakotas ?
标准：["William Howard Ashton,"]
答案：Billy J. Kramer
理由：问题问given name，Billy J. Kramer为艺名，不能替代出生名William Howard Ashton。

### row 631：equivalent
Which interviewee featured in The History of Sex also hosted the radio show "Sexually Speaking"?
标准：["Dr. Ruth Westheimer"]
答案：Dr. Ruth
理由：Dr. Ruth与Dr. Ruth Westheimer在指定节目及人物语境下同一主持人。

### row 632：incorrect
This event which was part of the 1954 AAA National Championship Trail was held at a racing circuit located at the corner of what?
标准：["16th Street and Georgetown Road"]
答案：Watkins Glen
理由：逐题审阅最终答案：Watkins Glen；标准：["16th Street and Georgetown Road"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 638：incorrect
Where was the community schools to which Franklin Community High School was part of headquartered ?
标准：["Franklin, Indiana"]
答案：Franklin Township, Marion County, Indiana, United States
理由：逐题审阅最终答案：Franklin Township, Marion County, Indiana, United States；标准：["Franklin, Indiana"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 639：incorrect
Where was the artist behind "Shit" born and raised?
标准：["Atlanta, Georgia"]
答案：Padua, Italy
理由：逐题审阅最终答案与标准：Padua, Italy / ["Atlanta, Georgia"]；实体、数值、时间或所问字段不一致，维持错误。

### row 644：equivalent
How many seasons has a popular tv show had, in which one of the episodes is called Moho House?
标准：["28"]
答案：twenty-eight
理由：twenty-eight与28同一剧季数量。

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
答案：Ostrava and Frydek-Mistek, Czech Republic
理由：逐题审阅最终答案：Ostrava and Frydek-Mistek, Czech Republic；标准：["Ufa, Russia"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 652：incorrect
When did British politician Damian Green state that said that e-Borders would be collecting information an all passengers on 100% of non-EEA flights to the UK?
标准：["April"]
答案：March 2012
理由：逐题审阅最终答案：March 2012；标准：["April"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 653：incorrect
Which animal races annually for a national title as part of a post-season NCAA Division I Football Bowl Subdivision college football game?\?
标准：["Dachshunds"]
答案：None
理由：逐题审阅最终答案与标准：None / ["Dachshunds"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 657：incorrect
What movie was released at a later date, My Dog Tulip or Monsters vs. Aliens?
标准：["Monsters vs. Aliens"]
答案：My Dog Tulip
理由：逐题审阅最终答案与标准：My Dog Tulip / ["Monsters vs. Aliens"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 664：incorrect
Are Local H and For Against both from the United States?
标准：["yes"]
答案：No
理由：逐题审阅最终答案：No；标准：["yes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 666：equivalent
Ciril Cvetko is the brother of a scholar who participates in what analysis of music?
标准：["Musicology"]
答案：musicological
理由：musicological与Musicology为同一音乐学领域的形容词和名词。

### row 667：equivalent
Who is a poet, Rumi or Farouk El-Baz?
标准：["Rumi (30 September 1207 – 17 December 1273), was a 13th-century Persian Sunni Muslim poet"]
答案：Rumi
理由：Rumi是标准长句中被指认的诗人，省略不必需传记描述。

### row 669：uncertain
What type of diary did one of the founders of the John Bishop Memorial Hospital in Srinagar write?
标准：["a travel diary"]
答案：diary
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 670：equivalent
who is older, Maria Sharapova or Chanda Rubin?
标准：["Chanda Rubin (born February 18, 1976)"]
答案：Chanda Rubin
理由：Chanda Rubin与带出生日期的Chanda Rubin同一选项。

### row 672：uncertain
Which American former competitive swimmer was Mitzi Kremer team mate?
标准：["Dara Grace Torres"]
答案：Mary Wayte
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 675：equivalent
Which Lithuanian-Canadian anthropologist, primatologist, conservationist, ethologist, and author was chosen by  Louis Leakey, along with Jane Goodall, Dian Fossey to study hominids in their natural environments?
标准：["Birutė Marija Filomena Galdikas"]
答案：Birutė Galdikas
理由：Birutė Galdikas与Birutė Marija Filomena Galdikas同一人，省略中间名。

### row 676：incorrect
Which was released first, The Climb or Voices of Iraq?
标准：["Voices of Iraq"]
答案：The Climb (1999 film)
理由：逐题审阅最终答案与标准：The Climb (1999 film) / ["Voices of Iraq"]；实体、数值、时间或所问字段不一致，维持错误。

### row 677：equivalent
In between Burton C. Bell and Billy Idol who is known professionally as Billy Idol?
标准：["William Michael Albert Broad"]
答案：Billy Idol
理由：Billy Idol与William Michael Albert Broad同一人的艺名与本名；题目要求在两人中选身份。

### row 678：incorrect
Opel once owned and manufactured the brand known under one shared name in New Zealand and Australia, and that brand is now a subsidiary of what company?
标准：["General Motors"]
答案：Groupe PSA
理由：逐题审阅最终答案：Groupe PSA；标准：["General Motors"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：$1.2 billion
理由：逐题审阅最终答案：$1.2 billion；标准：["$10.5 million"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 686：incorrect
Who was also an actor, Serri or John Fogerty?
标准：["Serri"]
答案：John Fogerty
理由：逐题审阅最终答案与标准：John Fogerty / ["Serri"]。实体、数值、时间或所问字段不一致，维持错误。

### row 687：equivalent
literary magazine Okyeame was inspired by this first prime Minister of Ghana whom led Ghana to independence from what country?
标准：["Britain"]
答案：United Kingdom
理由：United Kingdom与Britain在独立来源国问题中指同一国家。

### row 688：equivalent
The competition Lev Oborin won in 1927 is held in what city?
标准：["Warsaw, Poland"]
答案：Warsaw
理由：题目只问city，Warsaw完整回答Warsaw, Poland中的城市。

### row 695：incorrect
What term is the current chairman of Prince William County serving?
标准：["fourth term"]
答案：Corey A. Stewart
理由：逐题审阅最终答案与标准：Corey A. Stewart / ["fourth term"]；实体、数值、时间或所问字段不一致，维持错误。

### row 701：incorrect
The Chinese actress also known as Crystal Liu stars in Night Peacock with which three other actresses?
标准：["Liu Ye, Yu Shaoqun and Leon Lai"]
答案：Liu Yifei
理由：逐题审阅最终答案与标准：Liu Yifei / ["Liu Ye, Yu Shaoqun and Leon Lai"]；实体、数值、时间或所問字段不一致，维持错误。

### row 702：equivalent
What retailer did Albert Heijn start up that eventually merged with the Delhaize Group?
标准：["Koninklijke Ahold N.V."]
答案：Ahold
理由：Ahold与Koninklijke Ahold N.V.同一零售集团，省略皇家及法律后缀。

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
答案：Yes
理由：布尔题标准为by，标签损坏；Yes不能与该字符串语义等价。

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

### row 718：equivalent
Which guitarist that played on the LP Street Survivors and was a member of an American Southern Rock band from May 1976 until his death Oct 1977?
标准：["Steven Earl \"Steve\" Gaines"]
答案：Steve Gaines
理由：Steve Gaines与Steven Earl Steve Gaines同一吉他手的常用名和全名。

### row 719：equivalent
What is the nationality of the poet who wrote Une Tempete and first performed it in Tunisia?
标准：["French"]
答案：Francophone and French
理由：明确给French国籍并附加Francophone法语使用描述，未改变标准国籍。

### row 720：incorrect
Which countries forces fought in The Battle of Hürtgen Forest which was covered in the shooter video game Darkest Hour: Europe '44-'45?
标准：["American and German"]
答案：American
理由：逐题审阅最终答案：American；标准：["American and German"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 726：incorrect
Which tropical storm has been present in the Central Pacific Ocean but not in the western north Pacific Ocean?
标准：["Ana"]
答案：2006 Central Pacific cyclone
理由：逐题审阅最终答案与标准：2006 Central Pacific cyclone / ["Ana"]；实体、数值、时间或所问字段不一致，维持错误。

### row 729：equivalent
Which star of Zork was also the voice of Pac-Man?
标准：["Martin Ingerman"]
答案：Marty Ingels
理由：轨迹明确Martin Ingerman known professionally as Marty Ingels，同一演员的本名与艺名。

### row 732：incorrect
What is the main difference between the game Plateau and the game Colt Express?
标准：["Colt Express is a railway-themed"]
答案：abstract strategy board game
理由：逐题审阅最终答案：abstract strategy board game；标准：["Colt Express is a railway-themed"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 734：equivalent
Both WAGS Atlanta and WAGS are what?
标准：["American reality television series"]
答案：reality television series
理由：题目问节目类型，reality television series完整回答类别；标准American为附加国别。

### row 735：equivalent
Vivian Pinn taught at which college founded in Massachusetts in 1852?
标准：["Tufts College"]
答案：Tufts University
理由：Tufts University与Tufts College为同一大学的现名/历史名。

### row 737：equivalent
Which Bob Stoops coached team beat the 2016 Auburn Tigers football team?
标准：["2016 Oklahoma Sooners football team"]
答案：Oklahoma Sooners
理由：Oklahoma Sooners与2016 Oklahoma Sooners football team同一限定赛季球队，题目已给2016语境。

### row 739：uncertain
What airline holding company located in Solna Municipality, Sweden owns a technical aircraft maintenance company located in Arlanda, Sweden?
标准：["SAS Group"]
答案：SAS Scandinavian Airlines
理由：SAS Scandinavian Airlines与SAS Group为成员航空公司与控股集团关系，不能直接等价。

### row 740：equivalent
Which tower is taller, 712 Fifth Avenue or Manhattan Life Insurance Building?
标准：["712 5th Avenue"]
答案：712 Fifth Avenue
理由：712 Fifth Avenue与712 5th Avenue同一建筑，序数拼写不同。

### row 743：equivalent
What are the publishing years of this American and New York based film magazine published by Hachette Filipacchi Media U.S., where April Bernard worked as senior editor?
标准：["between 1987 and 2010"]
答案：1987 to 2010
理由：1987 to 2010完整给出between 1987 and 2010的出版年份范围。

### row 745：uncertain
When was the track from which a sample was featured in "Take Me to the Clouds Above" released?
标准：["16 March 1987"]
答案：1987
理由：1987省略标准16 March日期，保留精度不足。

### row 746：incorrect
What is the relation between current manager of Chinese club Tianjin Quanjian and Paolo Cannavaro?
标准：["brother"]
答案：manager
理由：逐题审阅最终答案与标准：manager / ["brother"]；实体、数值、时间或所问字段不一致，维持错误。

### row 747：incorrect
What was the capacity of the stadium that Colección Privada that was filmed on October 10, 2000?
标准：["15,500"]
答案：Estadio Monumental "U"
理由：逐题审阅最终答案与标准：Estadio Monumental "U" / ["15,500"]；实体、数值、时间或所问字段不一致，维持错误。

### row 749：uncertain
What language, also known as the Amazigh, is part of Siwa Oasis?
标准：["Berber"]
答案：Siwi
理由：Siwi为Berber语言分支，尚未确认问题要求总类还是具体语言。

### row 750：incorrect
Here's Little Richard is a debut album containing a song written by Little Richard, Enotris Johnson and who else?
标准：["Robert \"Bumps\" Blackwell"]
答案：Lee Allen
理由：逐题审阅最终答案：Lee Allen；标准：["Robert \"Bumps\" Blackwell"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 761：uncertain
What kind of music do The Stone Roses and The Lemonheads play?
标准：["rock band"]
答案：alternative rock
理由：alternative rock是rock子类型，轨迹对两乐队共同子类型证据不充分。

### row 762：uncertain
what caused the death of over 250 people in Accra, Ghana?
标准：["an explosion and a fire occurred at a petrol station"]
答案：2015 Accra explosion
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

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
答案：Season 8
理由：逐题审阅最终答案与标准：Season 8 / ["first"]；实体、数值、时间或所问字段不一致，维持错误。

### row 769：incorrect
Suicide's 1977 released album features a song based on what brand's comic character?
标准：["Marvel"]
答案：Winnie the Pooh
理由：逐题审阅最终答案与标准：Winnie the Pooh / ["Marvel"]；实体、数值、时间或所问字段不一致，维持错误。

### row 771：incorrect
What is the height of the tallest mountain from which the Glen River flows?
标准：["850 m"]
答案：Mount Katahdin
理由：逐题审阅最终答案：Mount Katahdin；标准：["850 m"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 773：equivalent
When was the improvisational troupe, which trained Amy Sedaris, Paul Dinello, and Stephen Colber, founded?
标准：["1959"]
答案：December 16, 1959
理由：December 16, 1959为The Second City成立日，给出标准1959的相容细化日期。

### row 774：equivalent
In whose government did the original owner of Heythrop Park come to prominence?
标准：["William's"]
答案：William's government
理由：William's government与William's在问题已问government的语境下同一所属政府。

### row 775：equivalent
The M1919 and the M1 was used by what military?
标准：["U.S."]
答案：U.S. Army
理由：U.S. Army是所问武器使用者美国军队，明确保留U.S.归属并细化为陆军。

### row 777：incorrect
Cyrina Fiallo has guest starred on which Michael Jacobs-created sitcom?
标准：["Girl Meets World"]
答案：Everybody Hates Chris
理由：逐题审阅最终答案：Everybody Hates Chris；标准：["Girl Meets World"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 779：equivalent
Zach Parise's father played in which league?
标准：["NHL"]
答案：National Hockey League (NHL)
理由：National Hockey League (NHL)为标准NHL的全称和缩写。

### row 780：incorrect
What stadium does the team who has Kent Baer as the defensive coordinator play its home games?
标准：["Sam Boyd Stadium"]
答案：Spartan Stadium
理由：逐题审阅最终答案：Spartan Stadium；标准：["Sam Boyd Stadium"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 782：uncertain
Which of the university at which Jack M. Guttentag  is a professor emeritus of finance was established in 1881 through a donation?
标准：["Wharton School of the University"]
答案：University of Pennsylvania
理由：University of Pennsylvania为母校，题目1881 donation限定的是Wharton School具体学院。

### row 785：incorrect
What criteria subjectively qualifies the Houston Astrodome to be called the Eighth Wonder of the World?
标准：["comparable to the seven Wonders of the World"]
答案：revolutionary
理由：逐题审阅最终答案：revolutionary；标准：["comparable to the seven Wonders of the World"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 786：incorrect
What other jobs did the man that co-produced Gyara Hazar Ladkian have?
标准：["film lyricist"]
答案：poet
理由：逐题审阅最终答案：poet；标准：["film lyricist"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 787：incorrect
What song included on the 59th edition of Now That's What I Call Music was written and recorded by an Australian recording artist?
标准：["\"Cheap Thrills\" by Sia"]
答案："Can't Get You Out of My Head"
理由：逐题审阅最终答案与标准："Can't Get You Out of My Head" / ["\"Cheap Thrills\" by Sia"]；实体、数值、时间或所问字段不一致，维持错误。

### row 788：equivalent
What is the rule that makes a major difference between the National League and the American League that allows another player to bat for the pitcher?
标准：["the designated hitter rule"]
答案：Designated Hitter
理由：Designated Hitter与designated hitter rule在已明确rule的问题语境中同一规则。

### row 789：incorrect
Jamie Harris is best known for his role as The Hook-Handed Man in a movie directed by who ?
标准：["Brad Silberling"]
答案：Steven Spielberg
理由：逐题审阅最终答案：Steven Spielberg；标准：["Brad Silberling"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 790：equivalent
Igor Naming Agency named a resort located where?
标准：["Las Vegas Strip"]
答案：Las Vegas Strip in Paradise, Nevada
理由：Las Vegas Strip in Paradise, Nevada保留标准Las Vegas Strip位置并附加相容所在地。

### row 791：incorrect
Who is a guest in the final two episodes of season eighteen of South Park?
标准：["PewDiePie"]
答案：Cher
理由：逐题审阅最终答案与标准：Cher / ["PewDiePie"]；实体、数值、时间或所问字段不一致，维持错误。

### row 794：equivalent
Which American actor portray Steve Urkel in "Family Matters"?
标准：["Jaleel Ahmad White"]
答案：Jaleel White
理由：Jaleel White与Jaleel Ahmad White同一演员，省略中间名。

### row 795：incorrect
How much Argentina currency was involved in Boudougate?
标准：["2.3 million pesos"]
答案：Argentine peso
理由：逐题审阅最终答案与标准：Argentine peso / ["2.3 million pesos"]；实体、数值、时间或所问字段不一致，维持错误。

### row 797：incorrect
Which Royal Air Force is located in a town that had a population of 2,841 on 15 April 2012?
标准：["Mount Pleasant"]
答案：RAF Grafton Underwood
理由：逐题审阅最终答案与标准：RAF Grafton Underwood / ["Mount Pleasant"]；实体、数值、时间或所问字段不一致，维持错误。

### row 798：incorrect
What did Eric Radomski produce that premiered on Disney XD on May 26, 2013?
标准：["Avengers Assemble"]
答案：Dude, That's My Ghost!
理由：逐题审阅最终答案：Dude, That's My Ghost!；标准：["Avengers Assemble"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 799：incorrect
What Hindi thriller directed by Deepak SHivdasani features choreography by Phulwa Khamkar?
标准：["Julie 2"]
答案：Happy New Year
理由：逐题审阅最终答案：Happy New Year；标准：["Julie 2"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 810：equivalent
Psychopsis and Aubrieta are both genuses of which type of plants?
标准：["flowering plants"]
答案：flowering plant
理由：flowering plant与flowering plants是相同植物类别，单复数不同。

### row 811：incorrect
The eastern coast of Ivan Zammit's birth city is located along what body of water?
标准：["Grand Harbour"]
答案：Mediterranean Sea
理由：逐题审阅最终答案：Mediterranean Sea；标准：["Grand Harbour"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Shaw
理由：逐题审阅最终答案与标准：Shaw / ["Dave Thomas"]；实体、数值、时间或所问字段不一致，维持错误。

### row 816：incorrect
what producer of The Real Housewives of Orange County also hosts "Watch What Happens Live with Andy Cohen"?
标准：["Andy Cohen"]
答案：Adam Karpel
理由：逐题审阅最终答案与标准：Adam Karpel / ["Andy Cohen"]；实体、数值、时间或所问字段不一致，维持错误。

### row 817：label_issue
Who authorized this infantry that was organized in the northern states during the Civil War and was commanded by RObert GOuld Shaw?
标准：["Emancipation Proclamation"]
答案：United States War Department
理由：原标签实体类型或事实关系疑误，单列保留原EM，不增加等价正确数。

### row 818：incorrect
Which jazz singer has a 2003 album entitled The Boy Next Door?
标准：["Stacey Kent"]
答案：Ella Fitzgerald
理由：逐题审阅最终答案与标准：Ella Fitzgerald / ["Stacey Kent"]；实体、数值、时间或所问字段不一致，维持错误。

### row 819：incorrect
Stabat Mater was written by a composer of what nationality?
标准：["Polish"]
答案：Italian
理由：逐题审阅最终答案：Italian；标准：["Polish"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 826：incorrect
In which album was American rapper Kendrick Lamar's first number-one single on the US "Billboard" Hot 100 included?
标准：["\"1989\" (2014)"]
答案：good kid, m.A.A.d city
理由：逐题审阅最终答案：good kid, m.A.A.d city；标准：["\"1989\" (2014)"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Over two centuries
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 834：incorrect
Casino and Culto A La Vida are cocktails, one of which contains Havana Club 7 and what else?
标准：["It features Havana Club 7 Añejo Rum and Cranberry juice"]
答案：Havana Club Anejo Reserva
理由：逐题审阅最终答案与标准：Havana Club Anejo Reserva / ["It features Havana Club 7 Añejo Rum and Cranberry juice"]；实体、数值、时间或所问字段不一致，维持错误。

### row 835：equivalent
Which university is this American philosopher, theologian, and Christian apologist, who supports theistic science, professor at?
标准：["Biola University"]
答案：Talbot School of Theology at Biola University
理由：Talbot School of Theology at Biola University明确给标准Biola University任教机构并附加具体学院。

### row 838：incorrect
What film was written and directed by Joby Harold with music written by Samuel Sim?
标准：["Awake"]
答案：Home Fires
理由：逐题审阅最终答案：Home Fires；标准：["Awake"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 839：incorrect
Are both, Boise State University and Syracuse University, public colleges?
标准：["no"]
答案：Yes
理由：逐题审阅最终答案：Yes；标准：["no"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 845：incorrect
Where in Greek mythology was the father of Benthesikyme venerated as a chief deity?
标准：["Pylos and Thebes"]
答案：Poseidon
理由：逐题审阅最终答案：Poseidon；标准：["Pylos and Thebes"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 847：equivalent
What "God Gave Me You" artist wrote the song "Imagine That" for Diamond Rio?
标准：["Bryan Shelton White"]
答案：Bryan White
理由：Bryan White与Bryan Shelton White同一歌手，省略中间名。

### row 849：incorrect
What format does a 1170 kHz AM station that Jim Angel presented the news for have?
标准：["an oldies format"]
答案：Talk radio
理由：逐题审阅最终答案与标准：Talk radio / ["an oldies format"]。实体、数值、时间或所问字段不一致，维持错误。

### row 850：incorrect
Who is younger, Wayne Coyne or Toshiko Koshijima?
标准：["Toshiko Koshijima"]
答案：Wayne Coyne
理由：逐题审阅最终答案与标准：Wayne Coyne / ["Toshiko Koshijima"]。实体、数值、时间或所问字段不一致，维持错误。

### row 851：incorrect
Which musical group has released more albums, The Telescopes or Candlelight Red?
标准：["Candlelight Red"]
答案：The Telescopes
理由：逐题审阅最终答案：The Telescopes；标准：["Candlelight Red"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 852：equivalent
Who was born earlier, Robert Mulligan or James Foley?
标准：["Robert Patrick Mulligan"]
答案：Robert Mulligan
理由：Robert Mulligan与Robert Patrick Mulligan同一导演，省略中间名。

### row 853：incorrect
What judge who was on the show "Dancing with the Stars" was born on the 31st of March, 1963?
标准：["Paul Joseph Mercurio"]
答案：Len Goodman
理由：逐题审阅最终答案：Len Goodman；标准：["Paul Joseph Mercurio"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 855：incorrect
José Baviera starred in the 1962 film by the filmmaker who worked in what countries?
标准：["Spain, Mexico and France"]
答案：Argentina
理由：逐题审阅最终答案与标准：Argentina / ["Spain, Mexico and France"]；实体、数值、时间或所问字段不一致，维持错误。

### row 857：incorrect
Brendon Urie wrote new perspective after firing which bassist?
标准：["Brent Wilson was fired"]
答案：Jon Walker
理由：逐题审阅最终答案：Jon Walker；标准：["Brent Wilson was fired"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 858：incorrect
Which magazine began publication first, Reunions magazine or Money?
标准：["Money"]
答案：Reunions magazine
理由：逐题审阅最终答案与标准：Reunions magazine / ["Money"]。实体、数值、时间或所问字段不一致，维持错误。

### row 859：equivalent
How high on the US "Billboard" Hot 100 chart did Dan Smith's song reach in 2013?
标准：["number 5"]
答案：number five
理由：number five与number 5同一排名，英文数词和数字不同。

### row 860：incorrect
Which of the city at the south of Shelly Beach, New South Wales is a local government area in the Hunter region of New South Wales, Australia?
标准：["City of Newcastle"]
答案：Lake Macquarie
理由：逐题审阅最终答案与标准：Lake Macquarie / ["City of Newcastle"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 864：incorrect
Which Western action-adventure video game by Rockstar did Tyler Bunch act for?
标准：["Red Dead Redemption"]
答案：Red Dead Revolver
理由：逐题审阅最终答案与标准：Red Dead Revolver / ["Red Dead Redemption"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 871：incorrect
Were Ransom Riggs and John Berry from the same country?
标准：["yes"]
答案：No
理由：逐题审阅最终答案：No；标准：["yes"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：Michael Cohen
理由：逐题审阅最终答案与标准：Michael Cohen / ["John Faso"]；实体、数值、时间或所问字段不一致，维持错误。

### row 880：incorrect
What year did the series on CBS, starring the actor who known for his role in "Rebel Without a Cause," air?
标准：["1952"]
答案：1972
理由：逐题审阅最终答案与标准：1972 / ["1952"]；实体、数值、时间或所问字段不一致，维持错误。

### row 882：incorrect
How many minutes outside of Carson City is the Moonlite BunnyRanch on Moonlight Road?
标准：["a few minutes"]
答案：one mile
理由：逐题审阅最终答案与标准：one mile / ["a few minutes"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：Edward II of England
理由：Edward II of England与King Edward II同一君主，附加国家并省略头衔。

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

### row 893：incorrect
Phillip Pullman's book set in a parallel universe featuring a character named Lyra Belacqua was put into audio in what year?
标准：["2002"]
答案：1997
理由：逐题审阅最终答案：1997；标准：["2002"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 895：incorrect
Which British engineering company is best known for its luxury motor cars in the era of British history that covers the brief reign of King Edward VII?
标准：["D. Napier & Son"]
答案：Daimler Company
理由：逐题审阅最终答案：Daimler Company；标准：["D. Napier & Son"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 904：equivalent
How many degrees and minutes south of the equator are the bone fragments of the extinct Ascension night heron found?
标准：["7°56'"]
答案：7°56' south
理由：7°56' south与题目已明确south of equator的标准7°56'一致。

### row 908：incorrect
The Rome Protocols were signed by three Prime Ministers one of which was assassinated as part of what?
标准：["a failed coup attempt"]
答案：Nazi Germany
理由：逐题审阅最终答案与标准：Nazi Germany / ["a failed coup attempt"]；实体、数值、时间或所问字段不一致，维持错误。

### row 913：incorrect
Queen Elizabeth Grammar School, Wakefield is a type of secondary school that caters to children of what age cohort?
标准：["between 11 or 13 and 18"]
答案：secondary school
理由：逐题审阅最终答案与标准：secondary school / ["between 11 or 13 and 18"]；实体、数值、时间或所问字段不一致，维持错误。

### row 914：uncertain
Arundel Castle was damaged during a war between which two groups?
标准：["Parliamentarians (\"Roundheads\") and Royalists (\"Cavaliers\")"]
答案：Parliamentarians
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 916：incorrect
Do the University of Florida and University of Texas System combine to have both a 2000 acre campus and over 216,000 students?
标准：["yes"]
答案：No
理由：逐题审阅最终答案与标准：No / ["yes"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：1 million
理由：逐题审阅最终答案：1 million；标准：["2 million"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 926：incorrect
What population ranking is the Oklahoma city located south of a wilderness area spanning over 5000 acres?
标准：["fifth-largest"]
答案：27th
理由：逐题审阅最终答案：27th；标准：["fifth-largest"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 928：incorrect
The 2011–12 Houston Rockets season began with the drafting of the player who now plays for what team?
标准：["Boston Celtics"]
答案：Houston Rockets
理由：逐题审阅最终答案：Houston Rockets；标准：["Boston Celtics"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：David August
理由：教授问题的标准Fred MacMurray为演员，缺少实体关系支持。

### row 935：incorrect
Which band has more members, Kitchens of Distinction or Royal Blood?
标准：["Kitchens of Distinction"]
答案：Royal Blood
理由：逐题审阅最终答案：Royal Blood；标准：["Kitchens of Distinction"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 937：equivalent
What video game character did the voice actress in the animated film Alpha and Omega voice?
标准：["Kairi in the video game series \"Kingdom Hearts\"."]
答案：Kairi
理由：Kairi直接提取标准中的角色名，题目未要求游戏系列名。

### row 940：equivalent
Brahmarshi Vishwamitra is a 1991 film produced & directed by a man that served as Chief Minister of Andhra Pradesh for how many years?
标准：["seven"]
答案：seven years
理由：seven years与seven在任期年数问题中同一数量，附加单位。

### row 942：incorrect
Were was the Mexican state after which there is Villa Unión, Sinaloa located?
标准：["tip of the Baja California"]
答案：Guanajuato
理由：逐题审阅最终答案与标准：Guanajuato / ["tip of the Baja California"]；实体、数值、时间或所问字段不一致，维持错误。

### row 943：incorrect
Penny Rae Bridges starred in a television sitcom with what other actor?
标准：["Ben Savage"]
答案：Alex Rocco
理由：逐题审阅最终答案：Alex Rocco；标准：["Ben Savage"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 944：incorrect
What type of elevation does Aldgate railway station, Adelaide and Aldgate, South Australia have in common?
标准：["Hills"]
答案：suburb
理由：逐题审阅最终答案与标准：suburb / ["Hills"]；实体、数值、时间或所问字段不一致，维持错误。

### row 945：label_issue
In what year did Farda Amiga win a race at the Saratoga Race course?
标准：["(foaled February 1, 1999)"]
答案：2002
理由：金标准foaled February 1, 1999为出生年，题目问Saratoga赛获胜年份，标签字段错误。

### row 946：incorrect
A celebrity magazine that has featured Snoop Dogg and footballers such as Riyad Mahrez and the creator's team-mate Juan Mata was launched by which former Manchester United player?
标准：["Ferdinand"]
答案：Donny Deutsch
理由：逐题审阅最终答案与标准：Donny Deutsch / ["Ferdinand"]；实体、数值、时间或所问字段不一致，维持错误。

### row 950：incorrect
What position did the winner of the MVP in Pool C of the 2017 WBC play?
标准：["third baseman"]
答案：shortstop
理由：逐题审阅最终答案：shortstop；标准：["third baseman"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 955：incorrect
What group of Elektra Records recording artists are known to be an indie pop band?
标准：["Saint Motel"]
答案：Little Boots
理由：逐题审阅最终答案与标准：Little Boots / ["Saint Motel"]；实体、数值、时间或所问字段不一致，维持错误。

### row 956：incorrect
Which Australian professional women's basketball team has an American playing in it?
标准：["Adelaide Lightning"]
答案：Dandenong Rangers
理由：逐题审阅最终答案：Dandenong Rangers；标准：["Adelaide Lightning"]。所答实体、数值或所问字段不一致，不作等价修正。

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

### row 965：incorrect
Taylor Momsen and Craig Mabbitt from Escape the Fate have what in common?
标准：["lead singer"]
答案：American rock band
理由：逐题审阅最终答案与标准：American rock band / ["lead singer"]；实体、数值、时间或所问字段不一致，维持错误。

### row 968：incorrect
What trio was the songwriter of "What Are We Doin' Lonesome" from?
标准：["trio with his younger brothers Steve and Rudy"]
答案：Dottie West
理由：逐题审阅最终答案：Dottie West；标准：["trio with his younger brothers Steve and Rudy"]。所答实体、数值或所问字段不一致，不作等价修正。

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
答案：West Midlands Police Authority
理由：逐题审阅最终答案：West Midlands Police Authority；标准：["defence of the Cathedral"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 978：equivalent
Oklahoma State Cowboys are part of what NCAA Division?
标准：["NCAA Division I"]
答案：Division I Football Bowl Subdivision
理由：Division I Football Bowl Subdivision明确保留标准NCAA Division I，并给出该队FBS具体组别。

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

### row 981：equivalent
What station broadcast the episode "Marry Me a Little, Marry Me a Little More" , of the series created by Max Mutchnick and David Kohan?
标准：["National Broadcasting Company"]
答案：National Broadcasting Company (NBC)
理由：National Broadcasting Company (NBC)为标准电视网的全称及缩写。

### row 984：incorrect
This British television series was adapted from one of the better-known novels of a 19th-century writer and was first published in what magazine?
标准：["Household Words"]
答案：The Dark Blue
理由：逐题审阅最终答案与标准：The Dark Blue / ["Household Words"]；实体、数值、时间或所问字段不一致，维持错误。

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

### row 989：incorrect
Who else besides "The Golden Jet" was born in Point Anne, Ontario?
标准：["Dennis Hull, as well as painter Manley MacDonald."]
答案：Paul Henderson
理由：逐题审阅最终答案与标准：Paul Henderson / ["Dennis Hull, as well as painter Manley MacDonald."]；实体、数值、时间或所问字段不一致，维持错误。

### row 990：equivalent
Jessica Ashley has recorded her own songs and has also written songs for which singer known for her song "Leave (Get Out)"?
标准：["Joanna Noëlle Levesque"]
答案：JoJo
理由：JoJo与Joanna Noëlle Levesque同一歌手的艺名和本名。

### row 992：incorrect
What was the former name of the company which operates Hunterston Terminal?
标准：["Peel Holdings"]
答案：Hunterston Ore Terminal
理由：逐题审阅最终答案：Hunterston Ore Terminal；标准：["Peel Holdings"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 995：incorrect
What is another name for the butterfly of the Hesperiidae family that is found in the third largest country in Africa?
标准：["the buff-tipped skipper"]
答案：mountain sandman
理由：逐题审阅最终答案与标准：mountain sandman / ["the buff-tipped skipper"]；实体、数值、时间或所问字段不一致，维持错误。

### row 996：incorrect
The Runge-Kutta methods were developed by M.W. Kutta and a German mathematician, physicist, and Spectroscopist that was born in what year?
标准：["1856"]
答案：1867
理由：逐题审阅最终答案：1867；标准：["1856"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 998：equivalent
Where did Ian Harland study prior to studying at the oldest college at the University of Cambridge?
标准：["The Dragon School in Oxford"]
答案：The Dragon School
理由：The Dragon School与The Dragon School in Oxford同一学校，省略题中语境下非必要地点。

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
答案：SønderjyskE Ishockey
理由：逐题审阅最终答案：SønderjyskE Ishockey；标准：["Denmark men's national ice hockey"]。所答实体、数值或所问字段不一致，不作等价修正。

### row 1004：uncertain
Who is the manufacturer of the plane that shot down Jameel Sayhood?
标准：["McDonnell Douglas"]
答案：Boeing
理由：精度、关键字段、上下级范围或合法替代答案存在歧义，未确认等价，暂不加分。

### row 1007：incorrect
What actor played the male lead in a teen comedy about a high school nerd directed by Steve Rash?
标准：["Patrick Dempsey"]
答案：Scott Baio
理由：逐题审阅最终答案与标准：Scott Baio / ["Patrick Dempsey"]；实体、数值、时间或所问字段不一致，维持错误。

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
答案：film industry
理由：film industry给出题目中两位电影从业者在entertainment领域的正确具体行业。

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

### row 1018：incorrect
John E. EchoHawk is a leading member in a social movement that wants to reverse what ?
标准：["the paternalistic policies enacted upon Native American tribes"]
答案：Native American self-determination movement
理由：逐题审阅最终答案与标准：Native American self-determination movement / ["the paternalistic policies enacted upon Native American tribes"]；实体、数值、时间或所问字段不一致，维持错误。

### row 1021：incorrect
Brinckerhoff, New Yorkhad a role in a CBS sitcom created by whom?
标准：["Justin Adler"]
答案：Jerry Bruckheimer
理由：逐题审阅最终答案与标准：Jerry Bruckheimer / ["Justin Adler"]；实体、数值、时间或所问字段不一致，维持错误。
