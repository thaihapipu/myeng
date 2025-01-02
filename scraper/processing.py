from scraper.spiders.Util import Db

def langeek_images():
    mycursor.execute("SELECT * FROM english.word_sounds")
    myresult = mycursor.fetchall()

    with open("images.txt", "a") as file:
        for x in myresult:
            is_cam = x[4] == 'cambridge'
            #print(f"is_cam: {is_cam}")
            filename = x[2]
            urluk = x[5]
            urluk = urluk.split('|')[0]
            urlus = x[6]
            if(is_cam):
                urluk = "https://dictionary.cambridge.org/media/english/uk_pron/" + urluk
                urlus = "https://dictionary.cambridge.org/media/english/us_pron/" + urlus
            else:
                urluk = "https://www.oxfordlearnersdictionaries.com/media/english/" + urluk
                urlus = "https://www.oxfordlearnersdictionaries.com/media/english/" + urlus

            file.write(f'"{filename}":"{urluk}",\n')

            # Open the file in append mode ('a') to add a new line without overwriting
        
            
        #mycursor.execute(f"UPDATE langeekword SET pic_ids = '{pic_ids}' WHERE id = '{id}'")
    #mydb.commit()

mydb = Db.get_connection()
mycursor = mydb.cursor()

langeek_images()