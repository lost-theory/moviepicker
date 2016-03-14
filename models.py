import os
import sqlite3

SCHEMA = '''
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

    def get_categories(self):
        curs = self.conn.cursor()
        curs.execute("SELECT category FROM categories ORDER BY category")
        return [row['category'] for row in curs.fetchall()]

    def add_category(self, category):
        curs = self.conn.cursor()
        curs.execute("INSERT INTO categories VALUES (?)", [category])
        self.conn.commit()
