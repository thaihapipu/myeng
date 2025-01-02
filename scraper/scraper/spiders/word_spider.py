import scrapy
import json
from scraper.spiders.Util import Db
from w3lib.html import remove_tags, remove_tags_with_content 
 
class WordProcessingSpider(scrapy.Spider):
    name = "word-processing"
    
    def start_requests(self):
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT ox.id,ox.pos, cam.url FROM english.words as ox JOIN cambridgeword as cam ON ox.word = cam.word where ox.status = 1 AND cam.sourceuk != '' AND cam.sourceus != '' LIMIT 1000")
        myresult = mycursor.fetchall()

        for x in myresult:
            url = "https://dictionary.cambridge.org/dictionary/english/" + x[2]
            yield scrapy.Request(url=url, meta={'id':x[0], 'pos':x[1]})

    def parse(self, response):
        id = response.meta['id']
        pos = response.meta['pos']
        print(f"id: {id}, pos: {pos}")
        maindic = response.css("div.dictionary")
        maindic = maindic[0]
        headwords = maindic.css("div.pos-header")
        sourceuk = ''
        sourceus = ''
        for hw in headwords:
            campos = hw.css("span.pos::text").get(default = 'Not Found')
            if campos == pos:
                sources = hw.css("source")

                for s in sources:
                    if s.attrib["type"] == 'audio/mpeg':
                        src = s.attrib["src"]
                        if "/us_pron/" in src:
                            src = src.replace("/media/english/us_pron/","")
                            sourceus = src
                        else:
                            src = src.replace("/media/english/uk_pron/","")
                            sourceuk = src
                break

        if sourceuk is not None and sourceuk != '':
            sql = "UPDATE words SET camuk = %s, camus = %s, status = '3',soundtype ='2' WHERE id = %s"
            val = (sourceuk, sourceus, id)
            mydb = Db.get_connection()
            mycursor = mydb.cursor()
        
            mycursor.execute(sql, val)
            mydb.commit()
        else:
            sql = f"UPDATE words SET status = '4',soundtype ='1' WHERE id = '{id}'"
            mydb = Db.get_connection()
            mycursor = mydb.cursor()
        
            mycursor.execute(sql)
            mydb.commit()


class WordSensesSpider(scrapy.Spider):
    name = "word-senses"
    
    def start_requests(self):
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT id, url, pos, word FROM english.words where status = 0 limit 90000")
        #mycursor.execute("SELECT id, url, pos, word FROM english.words where word = 'racket'")
        myresult = mycursor.fetchall()

        for x in myresult:
            url = "https://www.oxfordlearnersdictionaries.com/definition/english/" + x[1]
            yield scrapy.Request(url=url, meta={'id':x[0], 'pos':x[2], 'word':x[3]})

    def parse(self, response):
        word_id = response.meta['id']
        pos = response.meta['pos']
        word = response.meta['word']
        cefrlist = ["a1","a2","b1","b2","c1","c2"]
        entry = response.css("div.entry")
        if pos == 'phrasal verb':
            entry = entry.css("span.pv-g")
        group = ''
        mydb = Db.get_connection()
        mycursor = mydb.cursor()
        val = []
        container = entry.xpath("./ol[has-class('senses_multiple')]")
        container.extend( entry.xpath("./ol[has-class('sense_single')]"))
        scraped = False
        if len(container) > 0:
            group_containers = container.css("span.shcut-g")
            if len(group_containers) == 0:
                group_containers = container
            for group_container in group_containers:
                group = group_container.css("h2.shcut::text").get(default = '')
                senses = group_container.css("li.sense")
                for sense in senses:
                    cefr = sense.css("div.symbols a::attr(href)").get()
                    if cefr is not None:
                        cefr = cefr[-2:]
                    if cefr not in cefrlist:
                        cefr = ''
                    labels = sense.css("li.sense > span.labels").xpath("string()").get(default = '')
                    grammar = sense.css("span.grammar::text").get(default = '')
                    #definition = sense.css("span.def").xpath("string()").get()
                    definition = sense.css("span.def").get()
                    if definition is None:
                        continue

                    definition = remove_tags_with_content(definition, which_ones=('div',))
                    definition = scrapy.Selector(text=definition)
                    definition = definition.xpath("string()").get()
                    examples = sense.css("ul.examples").get(default = '').replace(' class=""','').replace(' hclass="examples"','').replace(' hclass="cf"','') \
                        .replace(' htag="ul"','').replace(' htag="li"','').replace(' htag="span"','')
                    
                    val.append((word_id, word, pos, cefr, group, grammar, labels, definition, examples))
                    #print("pos: " + pos)
                    #print("group: " + group)
                    #print("cefr: " + cefr)
                    #print("grammar: " + grammar)
                    #print("labels: " + labels)
                    #print(f"definition: {definition}")
                    #print(f"examples: {examples}")
            if len(val) > 0:
                scraped = True
                sql = "INSERT INTO word_senses (word_id, word, pos, cefr, sense_group, grammar, labels, def, examples) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

                mycursor.executemany(sql, val)
                mydb.commit()
                sql = f"UPDATE words SET status = '2' WHERE id = {word_id}"
                mycursor.execute(sql)
                mydb.commit()
        if not scraped:
            category = 'nonsense'
            ref = container.css("span.xrefs")
            if len(ref) > 0:
                category = 'alias'
            
            sql = f"UPDATE words SET status = '1',category ='{category}' WHERE id = {word_id}"
            mycursor.execute(sql)
            mydb.commit()
            
        return