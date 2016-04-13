import os
from datetime import datetime

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

movielist = db.Table('movielist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id')),
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(512), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(512))

    movies = db.relationship('Movie', secondary=movielist, backref=db.backref('users', lazy='dynamic'))

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
        m = Movie.get_or_create(title)
        self.movies.append(m)
        db.session.add(self)
        db.session.commit()
        return m

    def remove_from_list(self, title):
        self.movies = [m for m in self.movies if m.title != title]
        db.session.add(self)
        db.session.commit()

    def to_json(self):
        return dict(
            id=self.id,
            username=self.username,
        )

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

    def to_json(self):
        return dict(
            id=self.id,
            name=self.name,
        )

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), unique=True, nullable=False)

    comments = db.relationship('Comment', backref=db.backref('movie', lazy='select'), lazy='dynamic')

    @classmethod
    def get_or_create(cls, title):
        m = cls.query.filter_by(title=title).one_or_none()
        if m:
            return m
        m = cls(title=title)
        db.session.add(m)
        db.session.commit()
        return m

    def add_comment(self, comment):
        self.comments.append(comment)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Movie id={!r} title={!r}>'.format(self.id, self.title)

    def to_json(self):
        return dict(
            id=self.id,
            title=self.title,
            comments=[row.to_json() for row in self.comments],
        )

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
    contents = db.Column(db.Text, nullable=False)
    is_visible = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def __repr__(self):
        return '<Comment id={!r} movie_id={!r} user_id={!r} created={!r} contents={!r}>'.format(
            self.id,
            self.movie_id,
            self.user_id,
            self.created,
            self.contents if len(self.contents) < 20 else (self.contents[:17] + "..."),
        )

    def to_json(self):
        return dict(
            id=self.id,
            movie_id=self.movie_id,
            user_id=self.user_id,
            contents=self.contents,
            created=self.created.isoformat(),
        )

#####

if __name__ == "__main__":
    from app import app
    print("Use Category.load_default_categories() to load categories.")
    with app.app_context():
        db.create_all()
        import code; code.interact(local=locals())
