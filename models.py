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
MIN_PASSWORD_LENGTH = 8

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(512), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    movies = db.relationship('Movie', backref=db.backref('user', lazy='select'))

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password_hash = pbkdf2_sha512.encrypt(password)

    def __repr__(self):
        return '<User id={!r} username={!r} email={!r}>'.format(self.id, self.username, self.email)

    @classmethod
    def create(cls, username, email, password, confirm):
        if not username.isalnum():
            raise RuntimeError("Invalid username. Only letters and numbers are allowed.")
        if "@" not in email or "." not in email:
            raise RuntimeError("Invalid email address.")
        if password != confirm:
            raise RuntimeError("Passwords do not match.")
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise RuntimeError("Passwords must be at least {} characters long.".format(MIN_PASSWORD_LENGTH))

        u = cls(username, email, password)
        db.session.add(u)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError, exc:
            if "username" in exc.message:
                raise RuntimeError("That username is already in use.")
            elif "email" in exc.message:
                raise RuntimeError("That email address is already in use.")
            else:
                raise
        return u

    @classmethod
    def validate(cls, username_or_email, password):
        u = cls.query.filter(
            db.or_(cls.username == username_or_email, cls.email == username_or_email)
        ).one_or_none()
        if not u:
            raise RuntimeError("Invalid username/email or password.")
        if not pbkdf2_sha512.verify(password, u.password_hash):
            raise RuntimeError("Invalid username/email or password.")
        return u

    def add_to_list(self, title):
        m = Movie(title=title)
        self.movies.append(m)
        db.session.add(self)
        db.session.commit()
        return m

    def remove_from_list(self, title):
        movies = Movie.query.filter_by(user_id=self.id, title=title).all()
        for m in movies:
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

    def __repr__(self):
        return '<Movie title={!r} for user_id={!r}>'.format(self.title, self.user_id)

#####

if __name__ == "__main__":
    from app import app
    print "Use db.create_all() to create the database."
    with app.app_context():
        import code; code.interact(local=locals())
