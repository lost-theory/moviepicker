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

from flask import Flask, render_template, request

from movies import MoviePicker, Movie, fetch_wikipedia_titles, fetch_omdb_info

CATEGORIES = [
    'American_action_thriller_films',
    'American_biographical_films',
    'American_crime_drama_films',
    'American_drama_films',
    'American_epic_films',
    'American_romantic_comedy_films',
    'American_satirical_films',
    'American_science_fiction_films',
]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html", categories=CATEGORIES)

@app.route('/movies/<category>')
def show_category(category):
    titles = fetch_wikipedia_titles(category)
    return render_template("movies.html", category=category, titles=titles)

@app.route('/random')
def random_movie():
    cat = random.choice(CATEGORIES)
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
    #app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host='0.0.0.0', debug=True)
