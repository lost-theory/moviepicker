'''
Build an OO interface for our movie picker code, but fetching data on-the-fly
from Wikipedia and omdbapi.com.

Example output:

$ python solved4.py 1990s_comedy_films
Pterodactyl Woman from Beverly Hills (1997)
Plot: Pixie is cursed with turning into a Pterodactyl when her husband is caught messing with bones on an ancient burial ground. Her husband, children, friends, and neighbours must come to terms ...
Genre: Comedy
IMDb URL: http://www.imdb.com/title/tt0110910
IMDb rating: 4.8/10

Add movie to your list? no
Le schpountz (1999)
Plot: Irene has no desire to work in his uncle's grocery shop and dreams of becoming an actor. His opportunity comes when a crew of movie makers came to his little village. Irene begins to go ...
Genre: Comedy, Romance
IMDb URL: http://www.imdb.com/title/tt0200091
IMDb rating: 3.3/10

Add movie to your list? no
The Pest (1997)
Plot: A Miami con man agrees to be the human target for a Neo-Nazi manhunter, in order to collect $50,000 if he survives.
Genre: Comedy
IMDb URL: http://www.imdb.com/title/tt0119887
IMDb rating: 4.9/10

Add movie to your list? yes
Mystery Men (1999)
Plot: A group of inept amateur superheroes must try to save the day when a supervillian threatens to destroy a major superhero and the city.
Genre: Action, Comedy, Fantasy
IMDb URL: http://www.imdb.com/title/tt0132347
IMDb rating: 6.0/10

Add movie to your list? yes
A Fish in the Bathtub (1999)
Plot: Sam (Jerry Stiller) and Molly (Anne Meara) are a classic bickering old couple, and their marriage has been 40 years of sparring. Yet, when Sam refuses to move the carp he's keeping in their...
Genre: Comedy
IMDb URL: http://www.imdb.com/title/tt0126908
IMDb rating: 5.7/10

Add movie to your list? yes

== Your movies ==

The Pest
Mystery Men
A Fish in the Bathtub
'''

import json
import random
import urllib

DEFAULT_CATEGORY = "American_science_fiction_action_films"
WIKIPEDIA_CATEGORY_URL = "https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:{}&format=json&cmlimit=250&cmcontinue={}"
OMDBAPI_TITLE_URL = "http://www.omdbapi.com/?t={}&y=&plot=short&r=json&tomatoes=true"

#have the user pick this many movies before quitting
NUM_MOVIES = 3

#use this to build the URL to the movie on IMDB, e.g.: http://www.imdb.com/title/tt0093773
IMDB_URL = "http://www.imdb.com/title/{}"

## API code ###################################################################

def clean_title(title):
    '''
    Removes "(film)", "(serial)", "(1998 film)", etc. from the given Wikipedia
    page title.
    '''
    title = title.replace("(film)", "")
    title = title.replace("(serial)", "")
    title = title.replace("(series)", "")
    if "film)" in title:
        #"Godzilla (2014 film)" -> ['Godzilla ', '2014 film)']
        title, year_of_film = title.split("(", 1)
        #if this assert fails, then I need to think of another way to split this text off the title...
        assert "film)" in year_of_film
    return title.strip()

def filter_titles(members):
    '''
    Filter and clean the raw page titles from Wikipedia categorymembers call.
    '''
    titles = []
    for m in members:
        title = m['title']
        if 'Category:' in title:
            continue #ignore sub-categories
        title = clean_title(title)
        titles.append(title)
    return titles

def fetch_wikipedia_titles(category):
    '''
    Returns a full list of members returned by the Wikipedia categorymembers
    API call.
    '''
    cmcontinue = ""
    out = []
    while True:
        url = WIKIPEDIA_CATEGORY_URL.format(category, cmcontinue)
        response = urllib.urlopen(url)
        data = json.loads(response.read())
        out.extend(data['query']['categorymembers'])
        if 'continue' not in data:
            break
        cmcontinue = data['continue']['cmcontinue']
    return filter_titles(out)

def is_valid_category(category):
    if not category:
        raise RuntimeError("Category must not be blank.")

    #try fetching it to ensure it actually returns some titles
    titles = fetch_wikipedia_titles(category)
    if not titles:
        raise RuntimeError("Category is empty.")

    return True

def fetch_omdb_info(title):
    '''
    Retrieve movie information from OMDb API's title search.
    '''
    url = OMDBAPI_TITLE_URL.format(title.encode('utf8'))
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    if data.get('Error'):
        raise RuntimeError("OMDb API returned {!r} when looking up {!r}".format(data['Error'], title))
    return data

## classes ####################################################################

class MovieData(object):
    '''
    Represents a movie with data from the omdbapi.com.
    '''
    def __init__(self, data):
        self.data = data

    @property
    def title(self):
        return self.data['Title']

    @property
    def imdb_url(self):
        return IMDB_URL.format(self.data['imdbID'])

    @property
    def poster_url(self):
        url = self.data.get('Poster')
        return '' if url == 'N/A' else url

    def __str__(self):
        txt = [
            u"{0[Title]} ({0[Year]})",
            u"Plot: {0[Plot]}",
            u"Genre: {0[Genre]}",
            u"IMDb URL: {imdb_url}",
            u"IMDb rating: {0[imdbRating]}/10",
        ]
        txt = u"\n".join(txt)
        txt = txt.format(
            self.data,
            imdb_url=self.imdb_url,
        )
        return txt.encode('utf8')

    def __html__(self):
        html = u'''
            <h2>{0[Title]} ({0[Year]})</h2>
            <p>{0[Plot]}</p>
            <ul>
                <li><strong>Genre</strong>: {0[Genre]}</li>
                <li><strong>IMDb rating</strong>: {0[imdbRating]}/10</li>
                <li><a href="{imdb_url}">View this movie on IMDb</a>.</li>
            </ul>
        '''.format(
            self.data,
            imdb_url=self.imdb_url,
        )
        return html

class MoviePicker(object):
    '''
    Random movie picker functionality. Returns random movies and keeps track of picked movies.
    '''
    def __init__(self, titles):
        '''
        Initializes the MoviePicker with a list of `titles` that will be picked from randomly.
        '''
        self.titles = random.sample(titles, len(titles))
        self.picked = []

    def get_random_movie(self):
        '''
        Pick a random title, fetch its data from OMDB, and return it as a MovieData object.
        '''
        movie = None
        while not movie:
            title = self.titles.pop()
            try:
                movie = fetch_omdb_info(title)
            except RuntimeError:
                #retry "RuntimeError: OMDb API returned u'Movie not found!'" exceptions
                movie = None
        return MovieData(movie)

    def add_to_list(self, m):
        '''Add the given Movie object `m` to the list of picked movies.'''
        self.picked.append(m)

    def get_list(self):
        '''Returns a list of picked titles.'''
        return [m.title for m in self.picked]

## main #######################################################################

def main(category):
    picker = MoviePicker(fetch_wikipedia_titles(category))
    num_picked = 0
    while num_picked < NUM_MOVIES:
        movie = picker.get_random_movie()
        print movie
        print ""
        answer = raw_input("Add movie to your list? ")
        if answer.lower().startswith('y'):
            picker.add_to_list(movie)
            num_picked += 1
    print "\n== Your movies ==\n"
    for title in picker.get_list():
        print title

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        category = sys.argv[1]
    else:
        category = DEFAULT_CATEGORY
    main(category)
