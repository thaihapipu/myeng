from pathlib import Path

import scrapy
import json
from scraper.spiders.Util import Db

class LongmanBrowseSpider(scrapy.Spider):
    name = "longman-browse"
    start_urls = ["https://www.ldoceonline.com/browse/english/"]

    def parse(self, response):
        for url in response.css("ul.browse_letters li a::attr(href)").getall():
            if url is not None:
                yield response.follow(url,self.parse_letter_index)
        
    
    def parse_letter_index(self, response):
        for url in response.css("ul.browse_groups li a::attr(href)").getall():
            yield {'url':url}

class LongmanWordListSpider(scrapy.Spider):
    name = "longman-word-list"
    
    def start_requests(self):
        
        with open('scraper/spiders/longman-browse-result.json') as f:
            urls = json.load(f)
        #urls = [
        #    {"url": "/browse/english/a/a-bolt-from-out-of-the-blue/"}
        #]

        for item in urls:
            url = "https://www.ldoceonline.com/" + item["url"]
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        val = []
        for a in response.css("ul.browse_results li a"):
            word = a.css("span.alpha_hw::text").get()
            url = a.attrib["href"].replace("/dictionary/", "")

            val.append((word,url))
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        sql = "INSERT IGNORE INTO longmanword (word, url) VALUES (%s, %s)"
        mycursor.executemany(sql, val)
        mydb.commit()
        #print(val)
        print(mycursor.rowcount, "was inserted.")
        