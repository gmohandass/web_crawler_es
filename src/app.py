import json

from flask import Flask, Response, request

from commons.config import *

from src.crawlers import *

import inspect
import sys
import requests

flask_app = Flask(__name__)


SCRAPPERS = [x[0] for x in inspect.getmembers(sys.modules[__name__], inspect.isclass) if
             (issubclass(x[1], CrawlerInterface) and (x[1] != CrawlerInterface))]


@flask_app.route('/', methods=['GET'])
def index():

    return '''
        <html>
          <head>
            <title>Home Page</title>
          </head>
          <body>
            <h1>Healthy</h1>
          </body>
        </html>
        '''


# List Scrappers
@flask_app.route('/scrappers', methods=['GET'])
def scrappers():
    return Response(json.dumps({'scrappers': SCRAPPERS}), status=200, mimetype='application/json')


# List ES indices
@flask_app.route('/tables', methods=['GET'])
def list_tables():
    return requests.get(ES_URL + "/_cat/indices").content


# Delete ES indices
@flask_app.route('/tables/<table_name>', methods=['GET', 'DELETE'])
def delete_tables(table_name):
    return requests.delete(ES_URL + "/" + table_name).content


# Start a Crawler
@flask_app.route('/crawler', methods=['POST'])
def crawler():
    scrapper = request.args.get('scrapper', None)
    keywords = request.args.getlist('keywords', type=list)
    if (scrapper is None) or (keywords is None):
        return Response(json.dumps({'response': "Scrapper and Keywords need to be provided"}),
                        status=400, mimetype='application/json')
    scrapper_lower = scrapper.lower()
    scrapper_filtered = [clss[1] for clss in inspect.getmembers(sys.modules[__name__], inspect.isclass) \
                 if (clss[0].lower() == scrapper_lower)]
    if len(scrapper_filtered) < 1:
        return Response(json.dumps({'response': "scrapper not found"}), status=400, mimetype='application/json')
    scrapper = scrapper_filtered[0]
    scrapper(es_host=ES_URL).execute(keywords)
    return Response(json.dumps({'response': "Success"}), status=200, mimetype='application/json')


if __name__ == "__main__":
    flask_app.run()
