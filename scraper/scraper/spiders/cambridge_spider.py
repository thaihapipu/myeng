from pathlib import Path

import scrapy
import json
from scraper.spiders.Util import Db

class CambridgeBrowseSpider(scrapy.Spider):
    name = "cambridge-browse"
    start_urls = ["https://dictionary.cambridge.org/browse/english/"]

    def parse(self, response):
        for url in response.css("ul.hul-ib LI a::attr(href)").getall():
            if url is not None:
                yield response.follow(url,self.parse_letter_index)
        
    
    def parse_letter_index(self, response):
        for url in response.css("div.i-browse div.lpr-2 a::attr(href)").getall():
            yield {'url':url}
        for url in response.css("div.i-browse div.lpl-2 a::attr(href)").getall():
            yield {'url':url}
            
#Usage: scrapy crawl cambridge-word-list
class CambridgeWordListSpider(scrapy.Spider):
    name = "cambridge-word-list"
    
    def start_requests(self):
        
        with open('scraper/spiders/cambridge-browse-result.json') as f:
            urls = json.load(f)
        #urls = [{"url": "https://dictionary.cambridge.org/browse/english/k/kidney-machine/"}]

        for item in urls:
            yield scrapy.Request(url=item["url"], callback=self.parse)

    def parse(self, response):
        val = []
        for a in response.css("div.han a.tc-bd"):
            word = a.css("span.haf").xpath("string()").get()
            pos = a.css("span.pos::text").get()
            url = a.attrib["href"].replace("/dictionary/english/", "")
            if pos is None:
                pos = ""
            val.append((word,pos,url))
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        sql = "INSERT IGNORE INTO cambridgeword (word, pos, url) VALUES (%s, %s, %s)"
        mycursor.executemany(sql, val)
        mydb.commit()
        #print(val)
        print(mycursor.rowcount, "was inserted.")

#Usage: scrapy crawl cambridge-media
class CambridgeMediaCollectSpider(scrapy.Spider):
    name = "cambridge-media"

    def start_requests(self):
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT id,url FROM english.cambridgeword where status = 0  LIMIT 50000")
        myresult = mycursor.fetchall()

        for x in myresult:
            url = "https://dictionary.cambridge.org/dictionary/english/" + x[1]
            yield scrapy.Request(url=url, meta={'id':x[0]})

    def parse(self, response):
        maindic = response.css("div.dictionary")
        if len(maindic) == 0:
            mydb = Db.get_connection()
            mycursor = mydb.cursor()
            sql = f"UPDATE cambridgeword SET status = '10' WHERE id = '{response.meta['id']}'"
            mycursor.execute(sql)
            mydb.commit()
            return
        else:
            maindic = maindic[0]
        sources = maindic.css("source")
        sourceuk = []
        sourceus = []
        for s in sources:
            if s.attrib["type"] == 'audio/mpeg':
                src = s.attrib["src"]
                if "/us_pron/" in src:
                    src = src.replace("/media/english/us_pron/","")
                    if src not in sourceus:
                        sourceus.append(src)
                else:
                    src = src.replace("/media/english/uk_pron/","")
                    if src not in sourceuk:
                        sourceuk.append(src)
        count = len(sourceuk) + len(sourceus)
        sourceuk = "|".join(sourceuk)
        sourceus = "|".join(sourceus)
        sql = "UPDATE cambridgeword SET mp3count = %s, sourceuk = %s, sourceus = %s, status = '1' WHERE id = %s"
        val = (count, sourceuk, sourceus, response.meta['id'])
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        
        mycursor.execute(sql, val)
        mydb.commit()