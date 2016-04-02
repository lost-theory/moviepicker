import os

from passlib.hash import pbkdf2_sha512
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.exc

db = SQLAlchemy()

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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(512), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    movies = db.relationship('Movie', backref=db.backref('user', lazy='select'))

    def __init__(self, email, password):
        self.email = email
        self.password_hash = pbkdf2_sha512.encrypt(password)

    def __repr__(self):
        return '<User id={!r} email={!r}>'.format(self.id, self.email)

    @classmethod
    def create(cls, email, password, confirm):
        if "@" not in email or "." not in email:
            raise RuntimeError("Invalid email address.")
        if password != confirm:
            raise RuntimeError("Passwords do not match.")
        if not password or len(password) < 6:
            raise RuntimeError("Passwords must be at least 6 characters long.")

        u = cls(email, password)
        db.session.add(u)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise RuntimeError("That email address is already in use.")
        return u

    @classmethod
    def validate(cls, email, password):
        u = cls.query.filter_by(email=email).one_or_none()
        if not u:
            raise RuntimeError("Invalid email or password.")
        if not pbkdf2_sha512.verify(password, u.password_hash):
            raise RuntimeError("Invalid email or password.")
        return u

    @staticmethod
    def add_to_list(user_id, title):
        m = Movie(title, user_id)
        db.session.add(m)
        db.session.commit()
        return m

    @staticmethod
    def remove_from_list(user_id, title):
        m = Movie.query.filter_by(user_id=user_id, title=title).one()
        db.session.delete(m)
        db.session.commit()

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Category id={!r} name={!r}>'.format(self.id, self.name)

    @classmethod
    def create(cls, name):
        c = cls(name)
        db.session.add(c)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            raise RuntimeError("Category already exists.")
        return c

    @classmethod
    def load_default_categories(cls):
        for c in DEFAULT_CATEGORIES:
            db.session.add(cls(c))
        db.session.commit()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, user_id):
        self.title = title
        self.user_id = user_id

    def __repr__(self):
        return '<Movie title_id={!r} for user_id={!r}>'.format(self.title, self.user_id)

#####

if __name__ == "__main__":
    from app import app
    print "Use db.create_all() to create the database."
    with app.app_context():
        import code; code.interact(local=locals())
