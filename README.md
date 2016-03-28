## Movie picker Flask application

This code is used to demonstrate how to build a Flask application.

There are a few branches that represent different periods of development:

* [solved5](https://github.com/lost-theory/moviepicker/tree/solved5): Basic Flask application that builds on top of an existing command line movie picker program. No database or persistence, just read-only data pulled on the fly from Wikipedia (categories), OMDbAPI.com (movie data), and IMDb (poster images).
* [solved6](https://github.com/lost-theory/moviepicker/tree/solved6): Adds a sqlite database, models (categories, users, and lists of movies per user), login & registration, and AJAX calls.
