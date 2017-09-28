# Add necessary directories to the path
import sys
import os

curr_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.sep.join(curr_path.split(os.path.sep)[:-1])
sys.path.append(os.path.join(base_path, 'src'))
sys.path.append(os.path.join(base_path, 'src', 'crawlers'))


# Set up site 
from flask import Flask, Response, request, render_template
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site
from twisted.internet import reactor

flask_app = Flask(__name__)
flask_app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

resource  = WSGIResource(reactor, reactor.getThreadPool(), flask_app)
site = Site(resource)

# Everything else
from commons.config import ES_URL
import inspect
import requests
import json
import pkgutil

# Find and filter all classes contained in /crawlers
CLASSES = [
    (name, clss) 
    for module in [
        loader.find_module(name).load_module(name)
        for loader, name, is_pkg in pkgutil.iter_modules(['./crawlers'])
    ]
    for name, clss in inspect.getmembers(module, inspect.isclass)
]

# Just importing CrawlerInterface makes subclass check fail
CrawlerInterface = CLASSES[list(zip(*CLASSES))[0].index('CrawlerInterface')][1]
SCRAPER_NAMES, SCRAPER_CLASS = zip(*[
    (name, clss)
    for name, clss in CLASSES
    if name not in ['CrawlerInterface', 'HTMLCrawlerInterface', 'ParsingCrawlerInterface']
        and issubclass(clss, CrawlerInterface)
])


@flask_app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# List Scrapers
@flask_app.route('/scrapers', methods=['GET'])
def scrapers():
    return render_template('scrapers.jade', **{'scrapers': SCRAPER_NAMES})


# List ES indices
@flask_app.route('/tables', methods=['GET'])
def list_tables():
    return requests.get(ES_URL + "/_cat/indices").content


# Delete ES indices
@flask_app.route('/delete/<table_name>', methods=['GET', 'DELETE'])
def delete(table_name):
    return requests.delete(ES_URL + "/" + table_name).content


# View data for an index
@flask_app.route('/all_data/<table_name>', methods=['GET'])
def all_data(table_name):
    return requests.get(ES_URL + "/%s/_search?pretty=true" % table_name).content


# Start a Crawler using keywords
@flask_app.route('/keyword', methods=['POST'])
def keyword():
    scraper = request.args.get('scraper', None)
    keywords = request.args.getlist('keywords', type=list)
    if (scraper is None) or (keywords is None):
        return Response(json.dumps({'response': "Scraper and Keywords need to be provided"}),
                        status=400, mimetype='application/json')
    
    scraper_lower  = scraper.lower()
    all_names_lower= [name.lower() for name in SCRAPER_NAMES]
    if scraper_lower not in all_names_lower:
        return Response(json.dumps({'response': "scraper not found"}), status=400, mimetype='application/json')
    
    scraper = SCRAPER_CLASS[ all_names_lower.index(scraper_lower) ]
    scraper().execute(keywords)
    return Response(json.dumps({'response': "Success"}), status=200, mimetype='application/json')

from tasks import async
import time
@async
def test(idx):
    print('here')
    time.sleep(5)
    print('done')
    try:
        return requests.put(ES_URL + "/%s" % idx).content
    except Exception as e:
        print(e)

# Start an index
@flask_app.route('/create/<table_name>', methods=['GET'])
def create(table_name):
    test(table_name)
    return requests.get(ES_URL + "/_cat/indices").content



# Start a general site crawler
@flask_app.route('/crawl', methods=['POST'])
def crawl():
    scraper = request.args.get('scraper', None)


if __name__ == "__main__":
    # flask_app.run()

    reactor.listenTCP(5000, site)
    reactor.run()