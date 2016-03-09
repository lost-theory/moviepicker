'''
Integrate the "movie picker" OO code from Exercise 4 into the simple Flask web app
we wrote during class #3.

Five views:
  /                    -> Display a list of categories
  /movies/<category>   -> Display a list of all movies for a given category
  /movie/<title>       -> Display movie details from omdbapi.com for the given title
  /random              -> Display a random movie's details from a random category, ask if the user wants to save it to their list
  /user                -> Show a list of the user's saved movies

For saving the random movie we don't actually need to save anything yet. Same goes for
the list of the user's saved movies, just hardcode the list of titles for now.

Bonus: Use Jinja2's "extends" and "block" directives to have all of your templates
inherit from a "base" template.

Bonus: Grab a Bootstrap theme from https://bootswatch.com/ and put that into your
base template so that your app looks nicer!
'''

from flask import Flask, render_template, request

import movies #get this module from your ex4.py solution or https://gist.github.com/lost-theory/9378782e45d2c377f5ec

app = Flask(__name__)

@app.route('/')
def index():
    categories = [
        'American_action_thriller_films',
        'American_biographical_films',
        'American_crime_drama_films',
        'American_drama_films',
        'American_epic_films',
        'American_romantic_comedy_films',
        'American_satirical_films',
        'American_science_fiction_films',
    ]
    categories = "\n".join(['<li><a href="/movies/{0}">{0}</a></li>'.format(c) for c in categories])
    return "<ul>{}</ul>".format(categories)

@app.route('/movies/<category>')
def show_movies(category):
    titles = movies.fetch_wikipedia_titles(category)
    return render_template("movies.html", category=category, titles=titles)

if __name__ == '__main__':
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.run(host='0.0.0.0', use_reloader=True)