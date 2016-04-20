'''
To run tests:

$ ~/mp_app_env/bin/python runtests.py
$ ~/mp_app_env/bin/python runtests.py --coverage
'''

import json
import os
import random
import unittest
from functools import wraps

# An empty sqlite URL means using an in-memory DB. We need to set this
# before importing `app`.
os.environ['DBURI'] = "sqlite://"

from mock import patch, mock_open

from app import app, db
from app import User, Category, Movie, Comment
from movies import fetch_wikipedia_titles

app.config['TESTING'] = True  # to get full tracebacks in our tests
app.secret_key = 'testing'  # need this to get sessions to work

class AppTestCase(unittest.TestCase):
    def setUp(self):
        with app.app_context():
            db.create_all()
        self.client = app.test_client()

def with_logged_in_user(f):
    '''
    Register a new random user, run the wrapped test, then log the user out.
    '''
    @wraps(f)
    def wrapper(self, *a, **kw):
        username = "user{}".format(random.randint(10000000, 99999999))
        self.client.post('/login', data=dict(
            r_username=username,
            r_email="{}@wow.test".format(username),
            r_password="asdfasdf",
            r_confirm="asdfasdf",
            submit="reg")
        )
        res = f(self, *a, **kw)
        self.client.get('/logout')
        return res
    return wrapper

## non-app tests ##############################################################

class MoviePickerTests(unittest.TestCase):
    urlopen = mock_open(read_data='{"query": {"categorymembers": [{"title": "Up"}]}}')

    @patch("urllib.urlopen", urlopen)
    def test_fetch_wikipedia_titles(self):
        titles = fetch_wikipedia_titles("Pixar_animated_films")
        assert len(self.urlopen.mock_calls) == 2
        assert "https://en.wikipedia.org/" in str(self.urlopen.mock_calls[0])
        assert "Pixar_animated_films" in str(self.urlopen.mock_calls[0])
        assert "read()" in str(self.urlopen.mock_calls[1])
        assert len(titles) == 1
        assert titles[0] == 'Up'

## app tests ##################################################################

class ViewTests(AppTestCase):
    def test_index_logged_out(self):
        res = self.client.get('/')
        assert res.status == '200 OK'
        assert "<strong>Register</strong> or <strong>Log in</strong>" in res.data

    def test_add_cat_logged_out_redirect(self):
        res = self.client.get('/categories')
        assert res.status == '302 FOUND'
        assert '/login' in res.headers['Location']

    @with_logged_in_user
    def test_add_cat_logged_in(self):
        res = self.client.get('/categories')
        assert res.status == '200 OK'
        assert "<form" in res.data
        assert [line for line in res.data.split('\n') if "input" in line and 'type="text"' in line and 'category' in line]

    @with_logged_in_user
    def test_add_cat_empty_form_error(self):
        res = self.client.post('/categories')
        assert res.status == '200 OK'
        assert '<div class="alert alert-danger">' in res.data
        assert '<strong>Error:</strong> Category must not be blank.' in res.data

    @with_logged_in_user
    def test_add_cat_empty_form_error(self):
        res = self.client.post('/categories', data=dict(category='Pixar_animated_films'))
        assert res.status == '200 OK'
        assert "Pixar animated films" in res.data
        assert "Category created!" in res.data
        assert "Toy Story" in res.data

    def test_reg(self):
        res = self.client.post('/login', data=dict(r_username="test2", r_email="test2@wow.com", r_password="asdfasdf", r_confirm="asdfasdf", submit="reg"))
        assert res.status == '302 FOUND'
        res2 = self.client.get(res.headers['Location'])
        assert res2.status == '200 OK'
        assert 'Signed in as <a href="/user">test2</a>' in res2.data
        self.client.get('/logout') # so we don't pollute other tests

    def test_api_user_json(self):
        res = self.client.get('/api/user')
        assert res.status == '200 OK'
        data = json.loads(res.data)
        assert isinstance(data, dict)
        assert 'result' in data

class ModelTests(AppTestCase):
    def test_user_create(self):
        with app.app_context():
            u = User.create("test", "test@wow.com", "asdfasdf", "asdfasdf")
            db.session.add(u)
            db.session.commit()
            users = User.query.filter_by(email="test@wow.com").all()
            assert len(users) == 1
            assert users[0].username == "test"

    def test_category_create(self):
        with app.app_context():
            c = Category.create("Cheezy movies")
            db.session.add(c)
            db.session.commit()
            cs = Category.query.filter_by(name="Cheezy movies").all()
            assert len(cs) == 1
            assert cs[0].name == "Cheezy movies"

    def test_movie_create(self):
        with app.app_context():
            m = Movie.get_or_create("Monty Python and the Holy Test")
            db.session.add(m)
            db.session.commit()
            ms = Movie.query.filter_by(title="Monty Python and the Holy Test").all()
            assert len(ms) == 1
            assert ms[0].title == "Monty Python and the Holy Test"

    def test_comment_create(self):
        with app.app_context():
            m = Movie.get_or_create("Monty Python and the Holy Test")
            u = User.create("commenter", "comments@wow.com", "asdfasdf", "asdfasdf")
            db.session.add(m)
            db.session.add(u)
            db.session.commit()
            c = Comment(user_id=u.id, contents="4/5. Lots of good testing moments.")
            m.add_comment(c)
            comments = Comment.query.filter_by(user_id=u.id, movie_id=m.id).all()
            assert len(comments) == 1
            assert "good testing moments" in comments[0].contents
