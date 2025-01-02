from pathlib import Path

import scrapy
from scraper.spiders.Util import Db

class LanGeekWordListSpider(scrapy.Spider):
    name = "langeek-word-list"
    
    def start_requests(self):
        for i in range(200000, 230000):
            url = "https://dictionary.langeek.co/en/word/" + str(i)
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        word = response.css("div.tw-bg-blue-light-5 div.tw-bg-blue-light-5 div div div p.tw-mb-0::text").get()
        if word is not None:
            print(word)
            href = response.css("a.tw-text-gray-40::attr(href)").get()
            word_id = href.split('/')[-1].split('?')[0]
            #word_id = parts[-1]
            
            numpic = 0
            picurls = ''
            for url in response.css("img.tw-rounded-2xl::attr(src)").getall():
                url = url.replace("https://cdn.langeek.co/photo/","").replace("?type=jpeg","")
                if numpic > 0:
                    picurls += "|"
                picurls += url
                numpic += 1


            val = (word,numpic,picurls,word_id)

            mydb = Db.get_connection()
            mycursor = mydb.cursor()
            sql = "INSERT IGNORE INTO langeekword (word, numpic, picurls, word_id) VALUES (%s, %s, %s, %s)"
            mycursor.execute(sql, val)
            mydb.commit()
            #print(val)
            print(mycursor.rowcount, "was inserted.")
        