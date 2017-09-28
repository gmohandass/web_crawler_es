from __future__ import absolute_import
# from src.celery import app
from twisted.internet import threads
from src.es.es_client import ESClient

def async(f):
	def wrap(*args, **kwargs):
		threads.deferToThread(f, *args, **kwargs)
	return wrap

# @app.task
@async
def publish_to_es_bulk(es_host, url, website_name, test):
    es = ESClient(es_host, test_run=test)
    es.bulk_publish_docs(url, website_name)
