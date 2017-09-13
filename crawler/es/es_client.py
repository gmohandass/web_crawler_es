import requests
import base64
from datetime import datetime
import uuid
from elasticsearch import Elasticsearch


class ESClient(object):
    def __init__(self, es_host, author, test_run=True):
        self.es = Elasticsearch([es_host])
        self.author = author
        self.test_run = test_run
        self.index_name = "_".join(["crawler", author, "test"]) if test_run else "crawler"

    def publish_doc(self, url, website_name):

        try:
            html_obj = requests.get(url).text
            html_obj = html_obj.encode('utf-8').strip()
            doc = {
                "data": base64.b64encode(html_obj),
                "author": self.author,
                "website": website_name,
                "url": url,
                "timestamp": datetime.now()
            }

            if not self.test_run:
                today = datetime.today()
                self.index_name = "_".join([self.index_name, today.year,
                                            today.month, today.day])
            response = self.es.index(index=self.index_name, doc_type="my_doc",
                                     id=str(uuid.uuid1()),
                                     body=doc,
                                     pipeline="attachment")
            return response
        except Exception as e:
            raise e


if __name__ == '__main__':
    my_es = ESClient('localhost:9200', "gmohandass")
    my_es.publish_doc("https://www.freelancer.com/projects/graphic-design/build-website-15161743/", "freelancer")
