"""Original vector-style artwork, drawn locally. No stock imagery or brand marks."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H=1920,1080
BLUE='#2F5D9F'; INK='#44546A'; RED='#C0392B'; GOLD='#F2B600'
PALE='#E6EFF9'; LINE='#C8D8EB'; MUTED='#7B91AB'; WHITE='#FFFFFF'
FONT='C:/Windows/Fonts/NotoSansTC-VF.ttf'

@lru_cache(None)
def font(size,bold=False):
    f=ImageFont.truetype(FONT,size)
    f.set_variation_by_axes([700 if bold else 400])
    return f

class Art:
    def __init__(self):
        self.im=Image.new('RGBA',(W*2,H*2)); self.d=ImageDraw.Draw(self.im)
    def rect(self,b,fill=WHITE,r=20,outline=None,width=2):
        self.d.rounded_rectangle(tuple(v*2 for v in b),radius=r*2,fill=fill,outline=outline,width=width*2)
    def poly(self,p,fill,outline=None,width=2):
        p=[(x*2,y*2) for x,y in p];self.d.polygon(p,fill=fill)
        if outline:self.d.line(p+[p[0]],fill=outline,width=width*2,joint='curve')
    def line(self,p,fill=BLUE,width=3): self.d.line([(x*2,y*2) for x,y in p],fill=fill,width=width*2,joint='curve')
    def oval(self,b,fill,outline=None,width=2):self.d.ellipse(tuple(v*2 for v in b),fill=fill,outline=outline,width=width*2)
    def text(self,x,y,s,size=32,color=INK,bold=False,anchor='lt'):
        self.d.text((x*2,y*2),s,font=font(size*2,bold),fill=color,anchor=anchor)
    def fit(self,x,y,s,maxw,size=32,color=INK,bold=False):
        while self.d.textlength(s,font=font(size*2,bold))>maxw*2:size-=1
        self.text(x,y,s,size,color,bold)
    def card(self,x,y,w,h,r=26,fill=WHITE):
        self.rect((x+2,y+13,x+w+2,y+h+13),'#D7E2EF',r)
        self.rect((x,y,x+w,y+h),fill,r,LINE,1)
    def pill(self,x,y,s,color=BLUE,bg=PALE,size=24):
        w=self.d.textlength(s,font=font(size*2,True))/2+36
        self.rect((x,y,x+w,y+size+24),bg,16)
        self.text(x+18,y+10,s,size,color,True)
    def plane(self,x,y,w,h):
        self.poly([(x,y+h*.3+14),(x+w*.68,y+14),(x+w,y+h*.65+14),(x+w*.32,y+h+14)],'#CCDAED')
        self.poly([(x,y+h*.3),(x+w*.68,y),(x+w,y+h*.65),(x+w*.32,y+h)],'#F5F8FC',LINE)
    def person(self,x,y,k=1,color=BLUE,pose='stand'):
        def p(a,b):return (x+a*k,y+b*k)
        def b(a,c,d,e):return (*p(a,c),*p(d,e))
        self.oval(b(-48,186,52,209),'#C8D8E8')
        self.line([p(-17,116),p(-22,177)],INK,max(2,int(15*k)))
        self.line([p(17,116),p(27,177)],INK,max(2,int(15*k)))
        self.rect(b(-35,176,-8,187),INK,5);self.rect(b(15,176,44,187),INK,5)
        self.rect(b(-37,46,37,126),color,20)
        self.line([p(-31,61),p(-54,101),p(-29,118)],color,max(2,int(15*k)))
        self.line([p(30,60),p(50,99),p(76,82 if pose=='point' else 111)],color,max(2,int(15*k)))
        self.oval(b(66,72 if pose=='point' else 101,85,91 if pose=='point' else 120),'#E9BDA9')
        self.rect(b(-10,27,10,55),'#E9BDA9',5)
        self.oval(b(-29,-16,29,45),'#F1D0BA')
        self.oval(b(-29,-22,30,17),INK)
        self.rect(b(-30,-1,-16,25),INK,5)
        self.poly([p(-13,46),p(0,64),p(12,46)],WHITE)
    def car(self,x,y,k=1,color=BLUE):
        def b(a,c,d,e):return (x+a*k,y+c*k,x+d*k,y+e*k)
        self.oval(b(0,90,280,125),'#C4D4E5')
        self.poly([(x+25*k,y+53*k),(x+74*k,y),(x+180*k,y),(x+236*k,y+53*k)],color)
        self.rect(b(0,48,274,105),color,20)
        self.poly([(x+80*k,y+10*k),(x+120*k,y+10*k),(x+120*k,y+48*k),(x+48*k,y+48*k)],'#CFE4F6')
        self.poly([(x+133*k,y+10*k),(x+174*k,y+10*k),(x+217*k,y+48*k),(x+133*k,y+48*k)],'#CFE4F6')
        for a in [53,219]:
            self.oval(b(a-24,81,a+24,129),INK);self.oval(b(a-12,93,a+12,117),'#EDF3F9')
        self.rect(b(240,61,268,76),'#FFF4C4',4)
    def check(self,x,y,k=1,color=BLUE):self.line([(x,y+9*k),(x+10*k,y+19*k),(x+29*k,y-5*k)],color,max(2,int(5*k)))
    def arrow(self,x,y,x2,y2,color=BLUE):
        self.line([(x,y),(x2,y2)],color,3)
        a=math.atan2(y2-y,x2-x)
        self.line([(x2-15*math.cos(a-.5),y2-15*math.sin(a-.5)),(x2,y2),(x2-15*math.cos(a+.5),y2-15*math.sin(a+.5))],color,3)
    def monitor(self,x,y,w=340,h=200):
        self.rect((x,y,x+w,y+h),INK,18)
        self.rect((x+12,y+12,x+w-12,y+h-18),WHITE,10)
        self.rect((x+w*.44,y+h,x+w*.56,y+h+34),MUTED,4)
        self.rect((x+w*.29,y+h+30,x+w*.72,y+h+43),INK,8)
        for i,v in enumerate([.48,.7,.39,.9]):
            self.rect((x+w*(.12+i*.205),y+h*.77-v*h*.42,x+w*(.23+i*.205),y+h*.77),[LINE,BLUE,LINE,RED][i],4)
        self.text(x+w*.5,y+h-32,'示意',15,MUTED,anchor='mt')
    def desk(self,x,y,w=420):
        self.poly([(x,y),(x+w*.76,y-40),(x+w,y+35),(x+w*.25,y+80)],'#BDCEE3')
        self.line([(x+45,y+28),(x+45,y+176)],MUTED,12)
        self.line([(x+w-30,y+40),(x+w-30,y+176)],MUTED,12)
        self.line([(x+w*.7,y),(x+w*.7,y+136)],LINE,10)
    def lock(self,x,y,k=1):
        self.d.arc((int((x+12*k)*2),int(y*2),int((x+64*k)*2),int((y+64*k)*2)),180,360,fill=BLUE,width=max(2,int(7*k*2)))
        self.rect((x,y+30*k,x+76*k,y+92*k),BLUE,12)
        self.oval((x+33*k,y+50*k,x+44*k,y+62*k),WHITE)
        self.rect((x+37*k,y+55*k,x+40*k,y+75*k),WHITE,1)
    def lines(self,x,y,width=250,count=3,gap=25):
        for i in range(count):self.rect((x,y+i*gap,x+width*(1 if i%2==0 else .7),y+7+i*gap),LINE,3)
    def finish(self): return self.im.resize((W,H),Image.Resampling.LANCZOS)

def make_scene(s):
    layers=[]; i=s['id']; lead=s['lead']
    def when(phrase,early=.5):
        pos=s['text'].find(phrase)
        if pos<0:return .5
        p=0
        for w in s['words']:
            idx=s['text'].find(w['text'],p);p=idx+len(w['text'])
            if idx>=pos:return max(.35,lead+w['start']-early-.45)
        return .35
    def layer(a,t=0,drift=1,exit=None):
        im=a.finish();bbox=im.getbbox()
        if bbox:layers.append(dict(im=im.crop(bbox),x=bbox[0],y=bbox[1],t=t,drift=drift,exit=exit))
    a=Art()
    eyebrow=['LEXUS  /  售後服務','產出 1  /  公開輿情洞察','產出 1  /  公開輿情洞察','產出 1  /  公開輿情洞察','產出 1  /  公開輿情洞察','產出 2  /  AI 溝通計畫','產出 2  /  AI 溝通計畫','產出 2  /  AI 溝通計畫','產出 2  /  AI 溝通計畫','回廠率研究所'][i]
    titles=['人走了，才知道','把討論，化為可讀的訊號','逐句看見，離開的念頭','同樣的風險，不同的需求','讓經理，提早看見風險','在對的時機，準備關懷','每一個數字，都有出處','讓每則關懷，經過人的判斷','把回應，帶回下一次關懷','從看見風險，到說對的話'][i]
    a.text(110,68,eyebrow,24,BLUE,True)
    a.text(108,118,titles,58,INK,True)
    a.line([(110,214),(1810,214)],LINE,1)
    a.text(1810,76,'2026 和泰 AI 黑客松',23,MUTED,False,anchor='rt')
    source='論壇公開資料｜母體為論壇發言者' if i<=4 else '示意｜流程與介面示意'
    a.text(110,903,source,23,MUTED)
    a.text(1810,903,'回廠率研究所',23,MUTED,anchor='rt')
    layer(a,.35 if i else 1.05,0)

    if i==0:
        a=Art();a.plane(100,577,890,258)
        a.rect((155,305,700,595),'#EDF3FA',22,LINE)
        for x in [180,346,512]: a.rect((x,330,x+139,545),'#DDEAF6',8)
        a.desk(344,594,470);a.monitor(386,352,344,218);a.person(260,455,1.27,BLUE,'point')
        a.pill(188,762,'售後服務部經理');a.pill(440,657,'月報',size=23)
        layer(a,1.25)
        a=Art();a.card(1112,276,670,190);a.text(1150,300,'售後發言者',26,MUTED)
        for n in range(6):a.person(1195+n*99,365,.33,RED if n==5 else BLUE)
        layer(a,when('在公開論壇上'))
        a=Art();a.text(1127,493,'每 6 位，有 1 位',61,BLUE,True);a.text(1130,580,'正在找出口',48,INK,True)
        a.text(1133,654,'高風險占全部發言者 16.4%',27,MUTED)
        layer(a,when('每六位'))
        a=Art();a.arrow(1118,766,1370,766);a.person(1427,700,.55,'#8A9AAA')
        a.rect((1520,705,1783,816),'#E4EAF1',20);a.text(1560,740,'一般外廠',34,INK,True)
        layer(a,when('有些車主不再回廠了'))

    elif i==1:
        for n,label in enumerate(['PTT','Mobile01','Dcard']):
            a=Art();x=130+n*35;y=294+n*167;a.card(x,y,425,132)
            a.text(x+29,y+20,label,32,BLUE,True)
            a.text(x+29,y+76,'人名',21,MUTED);a.text(x+156,y+76,'店名',21,MUTED);a.text(x+280,y+76,'帳號',21,MUTED)
            for xx in [x+82,x+209,x+333]:
                for z in range(3):a.rect((xx+z*13,y+75,xx+z*13+10,y+93),INK,1)
            a.arrow(x+446,y+70,758,534)
            layer(a,.7+n*.35)
        a=Art();a.plane(690,590,465,209);a.poly([(720,357),(1110,357),(970,538),(970,625),(874,655),(874,538)],'#C9DBEF',BLUE)
        a.rect((773,333,1055,413),WHITE,15,LINE);a.text(812,351,'去識別',37,BLUE,True)
        a.text(784,665,'遮蔽流程示意',23,MUTED)
        a.pill(748,711,'資料沿光帶匯入');layer(a,.7)
        a=Art();a.card(1250,312,528,270);a.text(1293,347,'累積售後語料',28,MUTED)
        a.text(1290,403,'21,183',100,BLUE,True);a.text(1713,470,'句',28,INK)
        a.text(1296,528,'論壇公開資料',22,MUTED);layer(a,when('累積兩萬'))
        a=Art();a.card(1250,633,528,178);a.lock(1295,668,.86)
        a.text(1395,669,'和泰內網',36,INK,True);a.text(1395,727,'資料與模型都留在內網',23,MUTED)
        layer(a,when('資料和模型'))

    elif i==2:
        a=Art();a.card(110,275,590,290);a.pill(142,302,'本機 AI 模型')
        for n,label in enumerate(['無','不滿','考慮離開','已離開']):
            x=144+(n%2)*263;y=391+(n//2)*74
            a.rect((x,y,x+237,y+53),PALE if n<2 else '#F8EAE8',13)
            a.text(x+20,y+10,label,27,BLUE if n<2 else RED,True)
        layer(a,.5)
        for n,(value,label,phrase,color) in enumerate([('1,671','句流失句','一千六百',BLUE),('186','句沒抱怨就找出口','其中一百',RED)]):
            a=Art();x=110+n*305;a.card(x,604,283,216)
            a.text(x+29,628,value,68,color,True);a.fit(x+29,713,label,232,25,INK,True)
            a.text(x+29,773,'論壇公開資料',20,MUTED);layer(a,when(phrase))
        a=Art();a.card(762,274,1045,555);a.text(801,300,'九面向流失率',31,INK,True)
        a.text(1767,309,'論壇公開資料',21,MUTED,anchor='rt')
        rows=[('零件供應',17.3),('價格',15.0),('報價透明',9.5),('技術品質',8.9),('等待預約',7.4),('保固延保',7.2),('態度',4.7),('便利設施',3.0),('銷售交車',1.4)]
        for n,(label,v) in enumerate(rows):
            y=362+n*49;co=RED if n==0 else GOLD if n==1 else BLUE
            a.text(803,y,label,25,INK,n<2)
            a.rect((972,y+2,1650,y+28),'#EDF2F8',6)
            a.rect((972,y+2,972+v/17.3*655,y+28),co,6)
            a.text(1765,y-1,f'{v:.1f}%',27,RED if n==0 else INK,True,anchor='rt')
        layer(a,when('系統同時統計',1.2))

    elif i==3:
        types=[('過保精算派','511','過保後比價',BLUE),('品質失望派','247','想換車','#597CA6'),('口碑建議者','195','會帶別人走','#7890AE'),('靜默出走者','128','直接去了外廠',INK)]
        for n,(label,num,desc,col) in enumerate(types):
            a=Art();x=110+n*430;a.plane(x,533,400,139);a.person(x+179,376,1.15,col,pose='point' if n==2 else 'stand')
            a.pill(x+34,286,label,col)
            # Small profession-independent symbolic objects.
            if n==0:
                a.rect((x+239,458,x+303,540),WHITE,8,BLUE)
                a.rect((x+249,468,x+293,486),PALE,3)
                for xx in range(3):
                    for yy in range(2):a.oval((x+251+xx*15,496+yy*17,x+258+xx*15,503+yy*17),BLUE)
            elif n==1:
                for yy in [443,463,483]:a.rect((x+243,yy,x+310,yy+47),WHITE,5,LINE)
                a.lines(x+253,494,42,2,14)
            elif n==2:
                a.poly([(x+237,453),(x+285,431),(x+285,491),(x+237,474)],GOLD)
                a.line([(x+293,443),(x+311,434)],GOLD,4);a.line([(x+295,474),(x+314,485)],GOLD,4)
            else:a.arrow(x+236,473,x+313,473,MUTED)
            a.text(x+198,671,num,75,BLUE,True,anchor='mt');a.text(x+198,760,desc,27,INK,anchor='mt')
            layer(a,when(label,.9),1)
        a=Art();a.pill(675,832,'未分類 199 人｜觀察名單・不投遞',INK,'#E5EBF2',25)
        layer(a,when('無法歸類',.7),0)

    elif i==4:
        a=Art();a.plane(104,571,659,263);a.person(266,511,1.05,BLUE,'point')
        a.desk(383,654,297);a.monitor(382,451,290,165);a.pill(168,788,'售後服務部經理',size=24)
        a.card(111,286,256,114);a.text(143,323,'模型判斷',32,BLUE,True)
        a.card(407,286,277,114);a.text(439,323,'八條規則',32,BLUE,True)
        a.text(381,324,'＋',30,BLUE,True);layer(a,.5)
        a=Art();a.card(787,273,1008,560)
        a.text(826,308,'風險看板',36,INK,True);a.pill(1532,304,'每日更新',size=21)
        a.text(827,369,'戰情總覽    報告池    原始輿情',25,MUTED)
        for n,(lab,num,col) in enumerate([('高風險','1,049',RED),('中風險','231',GOLD),('低風險','5,114',BLUE)]):
            x=826+n*312;a.rect((x,428,x+280,608),'#F2F5F9',18)
            a.oval((x+22,455,x+38,471),col);a.text(x+50,444,lab,29,INK,True)
            a.text(x+23,509,num,63,RED if n==0 else BLUE,True)
        a.text(831,777,'風險分由模型判斷與規則合成',24,MUTED)
        layer(a,when('分成高',1))
        a=Art();a.text(828,656,'74%',65,RED,True);a.text(1015,671,'高風險有流失句',26,INK)
        a.text(1325,656,'1.8%',65,BLUE,True);a.text(1515,674,'低風險有流失句',24,INK)
        layer(a,when('四分之三',1))

    elif i==5:
        a=Art();a.plane(107,619,696,209);a.rect((166,297,705,655),'#E5EEF8',22)
        a.text(217,336,'LEXUS  /  售後服務',28,BLUE,True)
        a.car(209,479,.81,'#8BAACB');a.person(576,446,1.11,BLUE,'point')
        a.rect((500,603,732,714),WHITE,13,LINE);a.rect((529,566,704,625),INK,10)
        a.pill(159,798,'服務廠客戶關係專員',size=26);layer(a,.4)
        entries=[('保固到期前','60 天','保固到期前'),('回廠間隔逾建議週期','1.5 倍','在對的時機'),('刪項後','首次回廠','刪項之後'),('客訴結案後','第 7 天','或客訴結案'),('零件待料超過','7 天','在對的時機')]
        a=Art();a.line([(859,327),(859,812)],LINE,6);layer(a,.6,0)
        for n,(lab,val,phrase) in enumerate(entries):
            a=Art();y=280+n*113;a.oval((846,y+35,872,y+61),GOLD if n==0 else BLUE)
            a.card(905,y,874,91,r=18);a.text(937,y+29,lab,29,INK)
            a.text(1740,y+23,val,40,BLUE,True,anchor='rt')
            layer(a,when(phrase,1) if n in [0,2,3] else .8+n*.2,.4)

    elif i==6:
        a=Art();a.plane(90,637,753,193);a.card(143,287,605,477)
        a.pill(176,318,'客群 × 時機',size=24);a.text(179,391,'關懷訊息草稿',38,INK,True)
        a.lines(181,463,481,4,38);a.pill(181,642,'引用：官方條款編號',size=22)
        a.text(576,697,'示意',22,MUTED);layer(a,.4)
        a=Art();a.arrow(790,506,1020,506);a.oval((842,452,948,558),WHITE,LINE)
        a.check(877,492,1.1);a.text(896,591,'逐字比對',29,BLUE,True,anchor='mt')
        layer(a,when('每一個數字',.7))
        a=Art();a.card(1073,289,706,379);a.text(1114,318,'官方條款',32,INK,True)
        a.text(1110,370,'76',116,BLUE,True);a.text(1280,446,'條',32,INK)
        for n in range(6):
            x=1445+n*37;a.rect((x,385+(n%2)*17,x+29,526),'#BCD0E8' if n%2 else BLUE,4)
            a.line([(x+8,412),(x+21,412)],WHITE,2)
        a.pill(1113,567,'官網 40',size=27);a.pill(1375,567,'手冊 36',size=27)
        layer(a,when('只引用七十六',1))
        a=Art();a.card(1073,711,706,116)
        a.text(1113,745,'未公開價格',31,INK,True);a.text(1458,745,'不寫入',34,RED,True)
        layer(a,when('官方沒有',.8))

    elif i==7:
        a=Art();a.plane(105,633,631,189);a.person(295,440,1.48,BLUE,'point')
        a.desk(432,626,255);a.monitor(420,442,250,151)
        a.pill(125,806,'服務廠客戶關係專員',size=24);layer(a,.4)
        a=Art();a.card(790,282,1000,552);a.text(835,316,'溝通審核佇列',36,INK,True)
        a.pill(1530,314,'示意',size=23);a.text(840,397,'待審核草稿',26,MUTED)
        a.lines(840,455,744,3,37)
        for n,(label,col) in enumerate([('核准',BLUE),('改寫',BLUE),('退回',INK)]):
            x=840+n*302;a.rect((x,594,x+257,675),col if n==0 else PALE,15)
            a.text(x+128,614,label,33,WHITE if n==0 else col,True,anchor='mt')
        a.text(840,732,'客訴回訪不計頻率上限',25,INK)
        a.text(840,777,'觀察名單車主也回訪',24,MUTED);layer(a,.8)
        a=Art();a.rect((1138,589,1404,680),None,17,GOLD,5)
        a.poly([(1267,650),(1267,696),(1280,682),(1293,705),(1306,698),(1292,675),(1312,670)],INK)
        a.rect((836,530,1323,542),GOLD,5);layer(a,when('選擇核准',.8),0,when('只有人工核准',.3))
        a=Art();a.rect((835,589,1102,680),None,17,GOLD,5)
        a.check(1045,621,.65,WHITE);a.pill(454,323,'人工核准才投遞',BLUE,PALE,27)
        layer(a,when('只有人工核准',.3))

    elif i==8:
        a=Art();a.plane(109,610,525,224);a.monitor(188,372,320,220)
        a.pill(177,706,'溝通系統',size=28);layer(a,.5)
        a=Art()
        for n,label in enumerate(['LINE','Email','App','專員電話']):
            y=288+n*132;a.arrow(552,508,782,y+41);a.card(797,y,325,88,18)
            a.text(960,y+23,label,31,BLUE,True,anchor='mt');a.arrow(1140,y+41,1378,515)
        layer(a,.7)
        a=Art();a.rect((1410,283,1640,716),INK,37);a.rect((1423,307,1627,687),WHITE,24)
        a.rect((1481,304,1580,327),INK,10);a.pill(1451,363,'示意',size=22)
        a.rect((1441,447,1610,550),PALE,15);a.lines(1454,471,142,2,29)
        a.check(1510,601,1.05);a.person(1716,537,.98,BLUE,'point');layer(a,.7)
        a=Art();a.pill(1169,767,'點擊・預約・回廠',size=29)
        a.arrow(1125,791,654,791);a.pill(214,820,'校正觸發門檻・再訓練模型',size=25)
        layer(a,when('車主是否',.5))

    elif i==9:
        a=Art();a.plane(184,599,1535,258)
        a.oval((496,300,1435,776),None,LINE,3)
        a.person(344,514,1.2,BLUE,'point');a.person(1514,514,1.2,'#7890AE','point')
        a.pill(598,326,'輿情洞察',size=27);a.pill(1138,705,'AI 溝通',size=27)
        a.text(960,441,'Lexus 車主流失預警',62,INK,True,anchor='mt')
        a.text(960,536,'與 AI 溝通系統',62,BLUE,True,anchor='mt')
        a.text(960,652,'回廠率研究所',31,MUTED,False,anchor='mt')
        a.text(960,699,'2026 和泰 AI 黑客松',24,MUTED,False,anchor='mt')
        layer(a,.4)
    return layers

def background():
    import numpy as np
    yy,xx=np.mgrid[0:H,0:W];p=(yy/H*.66+xx/W*.12)[...,None]
    base=np.array([255,255,255])*(1-p)+np.array([220,232,245])*p
    # Broad soft bloom and diagonal light, computed once.
    glow=np.exp(-((xx-1390)**2/(690**2)+(yy-340)**2/(310**2)))[...,None]
    beam=np.exp(-((xx+yy*.65-1200)/175)**2)[...,None]*.25
    base=base+(255-base)*np.minimum(1,glow*.78+beam)
    im=Image.fromarray(base.clip(0,255).astype('uint8')).convert('RGBA')
    a=Art()
    for j in range(14):
        x=(j*337+144)%W;y=(j*137+239)%H;r=12+j%4*11
        a.oval((x-r,y-r,x+r,y+r),'#FFFFFF65')
    im.alpha_composite(a.finish())
    return im
