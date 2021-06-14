import twitter
import json
from random import randint
from time import sleep
from google_images_search import GoogleImagesSearch
from pycoingecko import CoinGeckoAPI
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import datetime

from schedule import Scheduler


class SafeScheduler(Scheduler):
    #Thanks to https://gist.github.com/mplewis/8483f1c24f2d6259aef6, i "borrowed" your code

    def __init__(self, reschedule_on_failure=True):
        self.reschedule_on_failure = reschedule_on_failure
        super().__init__()

    def _run_job(self, job):
        try:
            super()._run_job(job)
        except Exception:
            logger.error(format_exc())
            job.last_run = datetime.datetime.now()
            job._schedule_next_run()


with open("login.json") as f:
    login = json.load(f)


api = twitter.Api(consumer_key=login["consumer_key"],
                  consumer_secret=login["consumer_secret"],
                  access_token_key=login["access_token_key"],
                  access_token_secret=login["access_token_secret"])


#For the tweeting bits

def getPic(q,n=5):
    gis = GoogleImagesSearch(login["google_api_key"], login["google_cx"]) #api key, cx
    param = {'q':q,'num':n}
    gis.search(search_params=param)

    return (i for i in gis.results())


tLen = 280
def postTweet(c,m=None):
    #if m and "/" not in str(m): m = getPic(m)
    if len(c)<=tLen:
        api.PostUpdate(c,media=m)

    else: #for over 280 posts
        tL=[]
        #print(c)
        while len(c)>tLen:
            sI = c.index(" ",tLen-20,tLen-6)
            #print(sI)
            tL.append(f"{c[:sI]} ({len(tL)+1}/")
            c=f"...{c[sI+1:]}"
        tL.append(f"{c} ({len(tL)+1}/")
        #print(tL)
        api.PostUpdate(f"{tL[0]}{len(tL)})",m)
        for i in tL[1:]:
            #print(i)
            api.PostUpdate(f"{i}{len(tL)})")

def getPrice(c="bitcoin"):
    cg = CoinGeckoAPI()
    return cg.get_price(ids=c, vs_currencies='usd')

def makeMessage():
    try:
        return f"Cum Rocket is now worth ${getPrice('cumrocket')['cumrocket']['usd']}"
    except:
        return "idk man, something went wrong with CoinGecko"

#For image editing
def getCoord(image, perc, perc2=None):
    if not perc2: perc2 = perc
    w,h = image.size
    return (round(w*(perc/100)),round(h*(perc2/100)))

def getCoord2(image, im2, perc, perc2=None):
    if not perc2: perc2 = perc
    w,h = image.size
    oS1 = w - (100-perc)*w/100 - im2.size[0]
    oS2 = h - (100-perc2)*h/100 - im2.size[1]
    return (round(oS1),round(oS2))


def smartResize(im1,im2,denom):
    factor = (1/denom * im1.size[0])/im2.size[0]
    return im2.resize((round(im2.size[0]*factor), round(im2.size[1]*factor)))


def addCum(img,r,m):
    re = smartResize(img,r,3.75)
    img.paste(re,getCoord2(img,re,95,86),re)
    #img.show()
    fac = re.size[1]
    #print(fac)
    font = ImageFont.truetype("adrip1.ttf",round(fac))
    text = m
    ret = ImageDraw.Draw(img)
    ret.text((fac,fac), text, (255,255,255), font=font)    
    
def brazilify(img,alpha=75,braz="brazil.jpg"):
    img.putalpha(255)
    br = Image.open(braz)
    br.putalpha(alpha)
    br = br.resize((img.size[0],img.size[1]))
    return Image.alpha_composite(img,br).convert("RGB")

def makeBackup():
    m = makeMessage()
    img = Image.open("kevin.jpg")
    r = Image.open("two_the_moon.png")
    addCum(img,r,m)
    #img.show()
    img = brazilify(img,75,"matrix.jpg")
    img.save("backupKevT.jpg",quality=10)


def mainAction():
###Granny's Old Fashioned cumpost:

###Get the day
    with open("login.json") as f: #Just to refresh results, probably not the best way of doing things
        login = json.load(f)    

    day = login["day"]

###Prepare Crypto Report
    m = makeMessage()
    try:
###Grab that pic
        pics = getPic("kevin o'leary shark tank",day)
        *_, last = pics
###Make a temp
        my_bytes_io = BytesIO()
        #my_bytes_io.seek(0)
        #NOT NEEDED
        #raw_image_data = last.get_raw_data()
        #image.copy_to(my_bytes_io, raw_image_data)
        last.copy_to(my_bytes_io)
        my_bytes_io.seek(0)
        img = Image.open(my_bytes_io)
        #img.show()
###Add the cum
        #img = Image.open("l.jpg")
        r = Image.open("two_the_moon.png")
    ##    re = smartResize(img,r,3.75)
    ##    img.paste(re,getCoord2(img,re,95,86),re)
    ##    #img.show()
    ##
    ##    fac = re.size[1]
    ##    #print(fac)
    ##
    ##    font = ImageFont.truetype("adrip1.ttf",round(fac))
    ##
    ##    text = m
    ##
    ##    ret = ImageDraw.Draw(img)
    ##
    ##    ret.text((fac,fac), text, (255,255,255), font=font)    
        addCum(img,r,m)
        if randint(0,20)!=0:
            pref="Kevin says"
            qual = 95
        else:
            pref="Brazilian Kevin says"
            img = brazilify(img)
            qual = 1
        img.save("temp_kev_cum.jpg",quality=qual)
###Share with friends and family!
        postTweet(f"{pref} {m}", "temp_kev_cum.jpg")


    except Exception as e:
        print(e)
        makeBackup()
        postTweet(f"Code's down so hacker Kevin here to tell you {m}", "backupKevT.jpg")        

    login["day"]=day+1
    with open("login.json","w") as f:
        json.dump(login,f,indent=2)
    now = datetime.datetime.now()
    if now.minute<10: minit=f"0{now.minute}"
    else: minit = now.minute
    print(f"Done at {now.hour}:{minit}")


scheduler = SafeScheduler()

scheduler.every().day.at("17:38").do(mainAction)
#b = schedule.every(5).seconds.do(j)

print("Ready")

while True:
    scheduler.run_pending()
    sleep(1)


#mainAction()

