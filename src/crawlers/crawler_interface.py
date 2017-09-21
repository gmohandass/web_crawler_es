from src.commons.tasks import publish_to_es_bulk
from src.es.es_client import ESClient


class CrawlerInterface(object):

    def __init__(self, es_host, test=True):
        self.es = ESClient(es_host, test_run=test)

    def add_to_queue(self, url, website_name):
        publish_to_es_bulk.delay(es=self.es, url=url, website_name=website_name)

    def execute(self, keyword_list):
        raise NotImplementedError('You must implement the run() method yourself!')
