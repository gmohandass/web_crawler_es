import json

from flask import Flask, Response, request
from flasgger import Swagger

from commons.config import *

from src.crawlers import *

import inspect
import sys
import requests


flask_app = Flask(__name__)

swagger = Swagger(flask_app)

SCRAPPERS = [x[0] for x in inspect.getmembers(sys.modules[__name__], inspect.isclass) if
             (issubclass(x[1], CrawlerInterface) and (x[1] != CrawlerInterface))]


@flask_app.route('/', methods=['GET'])
def index():

    """This endpoint returns the health of the service.
    responses:
      200:
        description: A HTML page with the status Healthy
        examples:
          "Healthy"
    """

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


@flask_app.route('/scrappers', methods=['GET'])
def scrappers():
    """This endpoint returns a list of scrappers available for crawling.
    ---
    responses:
      200:
        description: A list of scrappers built for specific websites or general purpose web crawlers.
        examples:
          rgb: ['freelancer', 'chegg', 'generic']
    """
    return Response(json.dumps({'scrappers': SCRAPPERS}), status=200, mimetype='application/json')


# List ES indices
@flask_app.route('/tables', methods=['GET'])
def list_tables():
    """This endpoint returns a list of indices present in the elasticsearch backend.
    ---
    responses:
      200:
        description: A list of indices in the backend ES.
        examples:
          yellow open crawler_gmohandass_test WdvMDF9WRmul7kTRR2QUJg 5 1 1 0 701.2kb 701.2kb
          yellow open crawler_fiverr_test     MR-DXf8ORpOQUNOKJSLtaw 5 1 0 0    810b    810b
    """
    return requests.get(ES_URL + "/_cat/indices").content


# Delete ES indices
@flask_app.route('/tables/<string:table_name>', methods=['DELETE'])
def delete_tables(table_name):
    """
    This endpoint is used to delete a specific index from the backend ES.
    ---
    parameters:
      - name: table_name
        in: path
        type: string
        required: true
        description: the name of the elasticsearch index to delete
    examples:
      500:
        description: Error! The Index you're looking for doesn't exist.
      200:
        description: The index specified has been deleted as requested.
        examples: {"ok":true,"acknowledged":true}
    """
    return requests.delete(ES_URL + "/" + table_name).content


# Start a Crawler
@flask_app.route('/crawler', methods=['POST'])
def crawler():
    """
    This endpoint is used to create new crawler.
    ---
    parameters:
      - name: scrapper
        in: query
        type: string
        required: true
        description: the name of the scrapper to use for crawling websites
      - name: keywords
        in: query
        type: list
        required: true
        description: the name of the scrapper to use for crawling websites
    examples:
      400:
        description: Scrapper and Keywords need to be provided.
        examples: {"response": "Scrapper and Keywords need to be provided"}
      404:
        description: the scrapper requested could not be found.
        examples: {'response': "scrapper not found"}
      200:
        description: The crawler has been created with the requested keywords.
        examples: {"response": "Success"}
    """

    scrapper = request.args.get('scrapper', None)
    keywords = request.args.getlist('keywords', type=list)
    if (scrapper is None) or (keywords is None):
        return Response(json.dumps({'response': "Scrapper and Keywords need to be provided"}),
                        status=400, mimetype='application/json')
    scrapper_lower = scrapper.lower()
    scrapper_filtered = [clss[1] for clss in inspect.getmembers(sys.modules[__name__], inspect.isclass) \
                 if (clss[0].lower() == scrapper_lower)]
    if len(scrapper_filtered) < 1:
        return Response(json.dumps({'response': "scrapper not found"}), status=404, mimetype='application/json')
    scrapper = scrapper_filtered[0]
    scrapper(es_host=ES_URL).execute(keywords)
    return Response(json.dumps({'response': "Success"}), status=200, mimetype='application/json')


if __name__ == "__main__":
    flask_app.run()
