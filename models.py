import os
import sqlite3

from passlib.hash import pbkdf2_sha512

SCHEMA = '''
    DROP TABLE if exists users;
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email VARCHAR(512) NOT NULL,
        password_hash VARCHAR(512) NOT NULL
    );
    CREATE UNIQUE INDEX user_email ON users(email);

    DROP TABLE if exists users_movies;
    CREATE TABLE users_movies (
        user_id INTEGER,
        title VARCHAR(512) NOT NULL
    );
    CREATE INDEX users_movies_users_id ON users_movies(user_id);

    DROP TABLE if exists categories;
    CREATE TABLE categories (
        category VARCHAR(512) NOT NULL PRIMARY KEY
    );
'''

DEFAULT_CATEGORIES = [
    'American_action_thriller_films',
    'American_biographical_films',
    'American_crime_drama_films',
    'American_drama_films',
    'American_epic_films',
    'American_romantic_comedy_films',
    'American_satirical_films',
    'American_science_fiction_films',
]

class DB(object):
    def __init__(self, path):
        run_init = not os.path.exists(path)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        if run_init:
            self.init_db()

    def init_db(self):
        curs = self.conn.cursor()
        print "Creating schema."
        curs.executescript(SCHEMA)
        print "Loading default categories."
        for c in DEFAULT_CATEGORIES:
            curs.execute("INSERT INTO categories VALUES (?)", [c])
        self.conn.commit()

    #####

    def create_user(self, email, password, confirm):
        if "@" not in email or "." not in email:
            raise RuntimeError("Invalid email address.")
        if password != confirm:
            raise RuntimeError("Passwords do not match.")
        if not password or len(password) < 6:
            raise RuntimeError("Passwords must be at least 6 characters long.")
        curs = self.conn.cursor()
        if curs.execute("SELECT 1 FROM users WHERE email=?", [email]).fetchone():
            raise RuntimeError("Email address already exists.")
        hashed = pbkdf2_sha512.encrypt(password)
        curs.execute("INSERT INTO users VALUES (NULL, ?, ?)", [email, hashed])
        self.conn.commit()
        return self.validate_user(email, password)

    def validate_user(self, email, password):
        curs = self.conn.cursor()
        user = curs.execute("SELECT id, email, password_hash FROM users WHERE email=?", [
            email,
        ]).fetchone()
        if not user:
            raise RuntimeError("Invalid email or password.")
        if not pbkdf2_sha512.verify(password, user['password_hash']):
            raise RuntimeError("Invalid email or password.")
        return user['id']

    #####

    def get_users_movies(self, user_id):
        curs = self.conn.cursor()
        movies = curs.execute("SELECT title FROM users_movies WHERE user_id=?", [
            user_id,
        ]).fetchall()
        return [row['title'] for row in movies]

    def add_user_movie(self, user_id, title):
        curs = self.conn.cursor()
        curs.execute("INSERT INTO users_movies VALUES (?, ?)", [
            user_id,
            title,
        ])
        self.conn.commit()

    def remove_user_movie(self, user_id, title):
        curs = self.conn.cursor()
        curs.execute("DELETE FROM users_movies WHERE user_id=? AND title=?", [
            user_id,
            title,
        ])
        self.conn.commit()

    #####

    def get_categories(self):
        curs = self.conn.cursor()
        curs.execute("SELECT category FROM categories ORDER BY category")
        return [row['category'] for row in curs.fetchall()]

    def add_category(self, category):
        curs = self.conn.cursor()
        curs.execute("INSERT INTO categories VALUES (?)", [category])
        self.conn.commit()

#####

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        print "\nUse the `db` object to query the database. E.g.: db.conn.execute('select * from users').fetchall()\n"
        db = DB(sys.argv[-1])
        import code
        code.interact(local=locals())
    else:
        print "Provide a path to an sqlite3 db file."
