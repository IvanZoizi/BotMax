import sqlite3

class Dbase:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def get_user(self, user_id):
        return self.cursor.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,)).fetchone()