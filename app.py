'''
Movie picker flask application.
'''

import os
import random
import urllib

from flask import (
    Flask, g, request, url_for, session,
    render_template, redirect,
)
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

from movies import (
    MovieData,
    fetch_wikipedia_titles, fetch_omdb_info, is_valid_category,
)
from models import db, User, Category, Movie, Comment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DBURI', 'sqlite:///movies.db')
app.config['SQLALCHEMY_ECHO'] = bool(os.environ.get('ECHO'))
db.init_app(app)

## flask-admin code ###########################################################

class ProtectedAdminIndexView(AdminIndexView):
    '''Login protected index page for the admin area.'''
    @expose('/')
    def index(self):
        if session.get('user') != 1:
            return redirect(url_for('login'))
        return super(ProtectedAdminIndexView, self).index()

class ProtectedAdminModelView(ModelView):
    '''Login protected views for models in the admin area.'''
    def is_accessible(self):
        return session.get('user') == 1

    def inaccessible_callback(self, *a, **kw):
        return redirect(url_for('login'))

admin = Admin(app, name='MoviePicker Admin', index_view=ProtectedAdminIndexView())

for model in [User, Category, Movie, Comment]:
    admin.add_view(ProtectedAdminModelView(model, db.session))

## application code ###########################################################

@app.route('/')
def index():
    categories = Category.query.all()
    return render_template("index.html", categories=categories)

@app.route('/categories/<category>')
def show_category(category, message=''):
    titles = fetch_wikipedia_titles(category)
    return render_template("category.html", category=category, titles=titles, message=message)

@app.route('/categories', methods=['GET', 'POST'])
def add_category():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'GET':
        return render_template("add_category.html")
    name = request.form.get('category').replace(' ', '_')
    try:
        is_valid_category(name)
        category = Category.create(name)
    except RuntimeError, e:
        return render_template("add_category.html", category=name, error=e.message)

    return show_category(category.name, message='Category created!')

@app.route('/random')
def random_movie():
    cat = random.choice(Category.query.all())
    title = random.choice(fetch_wikipedia_titles(cat.name))
    return redirect(url_for("show_movie", title=title))

@app.route('/movie/<title>')
def show_movie(title):
    movie = Movie.query.filter_by(title=title).one_or_none()
    comments = movie.comments if movie else []
    moviedata = MovieData(fetch_omdb_info(title))
    return render_template("movie.html", moviedata=moviedata, comments=comments)

def register_or_login(form):
    submit = form['submit']
    if submit == 'reg':
        user = User.create(form['r_username'], form['r_email'], form['r_password'], form['r_confirm'])
    elif submit == 'login':
        user = User.validate(form['l_username_or_email'], form['l_password'])
    else:
        raise ValueError("Got unexpected submit value {!r}".format(submit))
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('login.html')
    try:
        user = register_or_login(request.form)
    except RuntimeError, exc:
        error_type = '{}_error'.format(request.form['submit'])
        return render_template('login.html', **{error_type: exc.message})
    session['user'] = user.id
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    if 'user' in session:
        del session['user']
    return redirect(url_for('index'))

@app.route('/user', methods=['GET', 'POST'])
def show_user():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST' and request.form['action'] == 'add':
        User.query.get(session['user']).add_to_list(request.form['title'])
        return "Added."
    elif request.method == 'POST' and request.form['action'] == 'remove':
        User.query.get(session['user']).remove_from_list(request.form['title'])
        return "Removed."

    movies = User.query.get(session['user']).movies
    movies = [MovieData(fetch_omdb_info(movie.title)) for movie in movies]
    return render_template("user.html", movies=movies)

@app.route('/comments', methods=['POST'])
def post_comment():
    if 'user' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    contents = request.form['contents']
    if contents:
        m = Movie.get_or_create(title)
        m.add_comment(Comment(user_id=session['user'], contents=contents))
    return redirect(url_for("show_movie", title=title))

@app.route('/rehost_image')
def rehost_image():
    image = urllib.urlopen(request.args['url'])
    return (image.read(), '200 OK', {'Content-type': 'image/jpeg'})

#####

if __name__ == '__main__':
    #setting the secret here for development purposes only
    #in production you would load this from a config file, environment variable, etc. outside of version control
    #uuid.getnode() returns a (hopefully) unique integer tied to your computer's hardware
    import uuid
    app.secret_key = str(uuid.getnode())
    app.run(host='0.0.0.0', debug=True)
