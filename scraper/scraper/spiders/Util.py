import mysql.connector

class Db:
    __db = None
    def get_connection():
        if Db.__db is None:
            Db.__db = mysql.connector.connect(
                host="localhost",
                user="admin",
                password="Gamezonedb!59",
                database="english"
            )
        return Db.__db
