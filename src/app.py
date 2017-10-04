# Set up site 
from flask import Flask, Response, request, render_template
flask_app = Flask(__name__)
flask_app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')

# Find and filter all classes contained in /crawlers
from commons.config import ES_URL
from crawlers.crawler_interface import CrawlerInterface
import inspect
import requests
import json
import importlib 
import glob
import os 

classes = []
files   = glob.glob(os.path.join('crawlers', '*.py'))
for f in files:
    f = f.replace(os.path.sep, '.').replace('.py','')
    module   = importlib.import_module(f)
    classes += inspect.getmembers(module, inspect.isclass)

SCRAPER_NAMES, SCRAPER_CLASS = zip(*[
    (name, clss)
    for name, clss in classes
    if name != 'CrawlerInterface' and issubclass(clss, CrawlerInterface)
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
    scraper  = request.args.get('scraper', None)
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


# Start a Crawler using keywords
@flask_app.route('/crawl/<scraper>/<keyword>', methods=['GET'])
def crawl(scraper, keyword):
    scraper_lower  = scraper.lower()
    all_names_lower= [name.lower() for name in SCRAPER_NAMES]
    if scraper_lower not in all_names_lower:
        return Response(json.dumps({'response': "scraper not found"}), status=400, mimetype='application/json')
    
    scraper = SCRAPER_CLASS[ all_names_lower.index(scraper_lower) ]
    scraper().execute([keyword])
    return Response(json.dumps({'response': "Success"}), status=200, mimetype='application/json')


# Create an index
@flask_app.route('/create/<table_name>', methods=['GET'])
def create(table_name):
    test(table_name)
    return requests.get(ES_URL + "/_cat/indices").content



if __name__ == "__main__":
    flask_app.run()