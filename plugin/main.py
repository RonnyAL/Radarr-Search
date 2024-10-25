import webbrowser
import urllib.parse

from flox import Flox, utils, ICON_BROWSER, ICON_SETTINGS
from pyarr import RadarrAPI
from requests.exceptions import ConnectionError

CACHE_DIR = 'Radarr-Search'
UNAUTHORIZED = {'error': 'Unauthorized'}
DEFAULT_URL = 'http://localhost:7878'


@utils.cache('radarr_movies.json', max_age=300)
def get_radarr_movies(radarr):
    movies = radarr.get_movies()
    if movies == UNAUTHORIZED:
        utils.remove_cache('radarr_movies.json')
        return []
    return movies

@utils.cache('radarr_new_movies.json', max_age=3)
def get_radarr_movies(radarr, query):
    return radarr.lookup_movies(term=query)

def format_subtitle(text):
    return text.replace('\r\n', ' ').replace('\n', ' ')

class RadarrSearch(Flox):

    def init_api(self):
        self.url, self.api_key = self.settings.get('url', DEFAULT_URL), self.settings.get('api_key')
        self.rd = RadarrAPI(self.url, self.api_key)

    def query(self, query):
        self.init_api()
        if self.api_key == "":
            self.add_item(
                title='Please set your API key',
                subtitle=f'Plugins > {self.name} > API Key',
                icon=ICON_SETTINGS,
                method=self.open_setting_dialog
            )
            return
        self.movies_results(query)
        if len(self._results) == 0:
            self.new_movies(query)

    def movies_results(self, query):
        try:
            movies = get_radarr_movies(self.rd)
        except ConnectionError:
            self.add_item(
                title='Connection Error',
                subtitle='Please check your settings',
                icon=ICON_SETTINGS,
                method=self.open_setting_dialog
            )
            return
        if movies == []:
            self.add_item(
                title='Unauthorized or No movies found!',
                subtitle='Please check your API key.',
                icon=ICON_SETTINGS,
                method=self.open_setting_dialog
            )
            return
        for movie in movies:
            if query.lower() in movie['title'].lower():
                self.add_item(
                    title=movie['title'],
                    subtitle=format_subtitle(movie['overview']),
                    icon=self.icon,
                    context=movie,
                    method=self.open_movie,
                    parameters=[self.url, movie['titleSlug']],
                )

    def new_movies(self, query):
        new_shows = self.rd.lookup_movies(query)
        for movie in new_shows:
            try:
                overview = movie['overview']
            except KeyError:
                overview = '...'
            self.add_item(
                title=movie['title'],
                subtitle=format_subtitle(overview),
                icon=self.icon,
                method=self.add_new,
                parameters=[self.url, query],
            )

    def context_menu(self, data):
        movie = data
        url = self.settings['url']
        self.add_item(
            title='Open in browser',
            icon=ICON_BROWSER,
            method=self.open_show,
            parameters=[url, movie['titleSlug']],
        )

    def open_activity(self):
        url = self.settings['url']
        webbrowser.open(f"{url}/activity/queue")

    def open_movie(self, url, titleSlug):
        webbrowser.open(f'{url}/movies/{titleSlug}')

    def add_new(self, url, search_term):
        search_term = urllib.parse.quote(search_term)
        url = f'{url}/add/new?term={search_term}'
        webbrowser.open(url)


if __name__ == "__main__":
    RadarrSearch()
