from src.tasks import publish_to_es_bulk


class CrawlerInterface(object):
    def __init__(self, es_host, test=True):
        self.test = test
        self.es_host = es_host

    def add_to_queue(self, urls, website_name):
        publish_to_es_bulk.delay(es_host=self.es_host, url=urls, website_name=website_name,
                                 test=self.test)

    def execute(self, keyword_list):
        raise NotImplementedError('You must implement the execute() method yourself!')