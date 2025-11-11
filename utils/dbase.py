import sqlite3

class Dbase:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cursor = self.conn.cursor()

    def get_user(self, user_id):
        return self.cursor.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,)).fetchone()

    def new_user(self, user_id, name, email, goal, steps):
        self.cursor.execute("""INSERT INTO users (user_id, name, email, goal, steps) VALUES (?, ?, ?, ?, ?)""", (user_id, name, email, goal, steps))
        self.conn.commit()

    def get_top_users(self):
        return self.cursor.execute("""SELECT name, everyday FROM users ORDER BY everyday DESC""").fetchall()


if __name__ == '__main__' :
    dbase = Dbase("../db.sqlite")
    print(dbase.get_top_users())