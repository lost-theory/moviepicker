'''
Integrate the "movie picker" OO code from Exercise 4 into the simple Flask web app
we wrote during class #3.

Five views:
  /                    -> Display a list of categories
  /movies/<category>   -> Display a list of all movies for a given category
  /movie/<title>       -> Display movie details from omdbapi.com for the given title
  /random              -> Display a random movie's details from a random category, ask if the user wants to save it to their list
  /user                -> Show a list of the user's saved movies
'''

import urllib
import random
import sqlite3

from flask import (
    Flask, g, request, url_for,
    render_template, redirect,
)

from movies import (
    MoviePicker, Movie,
    fetch_wikipedia_titles, fetch_omdb_info, is_valid_category,
)
from models import DB

app = Flask(__name__)

#####

@app.before_request
def before_request():
    g.db = DB("movies.db")

@app.teardown_request
def teardown_request(exc):
    g.db.conn.close()

#####

@app.route('/')
def index():
    categories = g.db.get_categories()
    return render_template("index.html", categories=categories)

@app.route('/categories/<category>')
def show_category(category, message=''):
    titles = fetch_wikipedia_titles(category)
    return render_template("category.html", category=category, titles=titles, message=message)

@app.route('/categories', methods=['GET', 'POST'])
def add_category():
    if request.method == 'GET':
        return render_template("add_category.html")
    category = request.form.get('category').replace(' ', '_')
    try:
        is_valid_category(category)
        g.db.add_category(category)
    except RuntimeError, e:
        return render_template("add_category.html", category=category, error=e.message)
    except sqlite3.IntegrityError:
        return render_template("add_category.html", category=category, error="Category already exists.")

    return show_category(category, message='Category created!')

@app.route('/random')
def random_movie():
    cat = random.choice(g.db.get_categories())
    titles = fetch_wikipedia_titles(cat)
    picker = MoviePicker(titles)
    return render_template("movie.html", movie=picker.get_random_movie())

@app.route('/movie/<title>')
def show_movie(title):
    movie = Movie(fetch_omdb_info(title))
    return render_template("movie.html", movie=movie)

@app.route('/user')
def show_user():
    movies = ['Blade Runner', 'Mad Max: Fury Road', 'The Imitation Game']
    movies = [Movie(fetch_omdb_info(movie)) for movie in movies]
    return render_template("user.html", movies=movies)

@app.route('/rehost_image')
def rehost_image():
    image = urllib.urlopen(request.args['url'])
    return (image.read(), '200 OK', {'Content-type': 'image/jpeg'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
