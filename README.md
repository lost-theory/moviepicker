## Movie picker Flask application

This code is used to demonstrate how to build a Flask application.

Here are the commits / branches that represent different periods of development:

* [5e984ac](https://github.com/lost-theory/moviepicker/blob/5e984ac/movies.py): The original movie picker command line code.
* [solved5](https://github.com/lost-theory/moviepicker/tree/solved5): Basic Flask application that builds on top of the existing command line program. No database or persistence, just read-only data pulled on the fly from Wikipedia (movie categories), OMDbAPI.com (movie data), and IMDb (poster images). Uses a Bootstrap theme.
* [solved6](https://github.com/lost-theory/moviepicker/tree/solved6): Adds a sqlite database, models (categories, users, and lists of movies per user), login & registration, secure handling of passwords with [passlib](https://pythonhosted.org/passlib/), and AJAX calls.
* [flask_sqlalchemy](https://github.com/lost-theory/moviepicker/tree/flask_sqlalchemy): Adds the Flask-SQLAlchemy extension, replacing the hand-rolled sqlite code. Application code was pretty much unchanged (just renaming methods). Templates only required one line of changes.
* [comments](https://github.com/lost-theory/moviepicker/tree/comments): Adds a username to the User model. Replaces the one-to-many User -> Movies relation with a many-to-many relation, removing the need for duplicate Movie rows. Now that each Movie has a unique movie_id, add a Comment model that lets users leave comments on each movie via the movie details page.
