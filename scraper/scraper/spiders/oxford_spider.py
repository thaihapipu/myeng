from pathlib import Path

import scrapy
import json
from scraper.spiders.Util import Db

class OxfordBrowseSpider(scrapy.Spider):
    name = "oxford-browse"
    start_urls = ["https://www.oxfordlearnersdictionaries.com/browse/english/"]
    urls: list[str] = []

    def start_requests2(self):
        urls = [
            "https://quotes.toscrape.com/page/1/",
            "https://quotes.toscrape.com/page/2/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        for url in response.css("[id='browse-letters'] span a::attr(href)").getall():
            if url is not None:
                yield response.follow(url,self.parse_letter_index)
        
    
    def parse_letter_index(self, response):
        for url in response.css("[id='groupResult'] span a::attr(href)").getall():
            yield {'url':url}

class OxfordWordListSpider(scrapy.Spider):
    name = "oxford-word-list"
    
    def start_requests(self):
        
        with open('scraper/spiders/oxford-browse-result.json') as f:
            urls = json.load(f)
        for item in urls:
            yield scrapy.Request(url=item["url"], callback=self.parse)

    def parse(self, response):
        val = []
        for a in response.css("[id='result'] ul li a"):
            word = a.css("data::text").get()
            wordtype_element = a.css("data pos")
            word = word.replace(str(wordtype_element),"").strip()
            url = a.attrib["href"].replace("https://www.oxfordlearnersdictionaries.com/definition/english/", "")
            
            pos = a.css("data pos::text").get()
            if pos is None:
                pos = ""
            #wordtypes = [item.strip() for item in wordtypes.split(',')]
            #for wordtype in wordtypes:
                #val.append((word,wordtype,url))
                #print(f"{word}: {wordtype}")
            val.append((word,pos,url))
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        sql = "INSERT IGNORE INTO oxfordword (word, pos, url) VALUES (%s, %s, %s)"
        mycursor.executemany(sql, val)
        mydb.commit()
        print(mycursor.rowcount, "was inserted.")
        
class OxfordProcessingSpider(scrapy.Spider):
    name = "oxford-pronunciation"
    
    def start_requests(self):
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT id,url FROM english.oxfordword where status = 0  LIMIT 40000")
        myresult = mycursor.fetchall()

        for x in myresult:
            url = "https://www.oxfordlearnersdictionaries.com/definition/english/" + x[1]
            yield scrapy.Request(url=url, meta={'id':x[0]})

    def parse(self, response):
        webtop = response.css("div.webtop")
        cefr = webtop.css("div.symbols a::attr(href)").get()
        cefrlist = ["a1","a2","b1","b2","c1","c2"]
        if cefr is not None:
            cefr = cefr[-2:]
        if cefr not in cefrlist:
            cefr = ''

        sounduk = soundus = ipa = ipauk = ipaus = ''
        BrE = webtop.css("span.phonetics div.phons_br")
        if BrE is not None:
            soundurl = BrE.css("div.sound::attr(data-src-mp3)").get()
            if soundurl is not None:
                sounduk = soundurl.replace("https://www.oxfordlearnersdictionaries.com/media/english/","")
            ipauk = BrE.css("span.phon::text").get()
        AmE = webtop.css("span.phonetics div.phons_n_am")
        if AmE is not None:
            soundurl = AmE.css("div.sound::attr(data-src-mp3)").get()
            if soundurl is not None:
                soundus = soundurl.replace("https://www.oxfordlearnersdictionaries.com/media/english/","")
            ipaus = AmE.css("span.phon::text").get()
        if(ipauk == ipaus): 
            ipa = ipauk
            if ipa is None: ipa = ''
        else:
            ipa = ipauk
            if ipaus is not None:
                ipa += "|" + ipaus
        val = (cefr, sounduk, soundus, ipa,response.meta['id'])
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        sql = "UPDATE oxfordword SET cefr = %s,sourceuk = %s,sourceus = %s,ipa = %s,status = '2' WHERE id = %s"
        mycursor.execute(sql, val)
        mydb.commit()
    #print(mycursor.rowcount, "was inserted.")