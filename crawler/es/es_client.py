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

    """
    This method can be used to download a webpage and index it into Elasticsearch.
    
    Args:
        url: (String) This parameter expects the url or the page to be indexed in elasticsearch.
        website_name: (String) This parameter expects the name of the website (eg. freelancer).
    
    Returns:
        The response is directed from elasticsearch
    
    Raises:
        KeyError: Raises an exception.
    """
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


"""
Below is an example of how to index a specific web page into elasticsearch.
Elasticsearch url is http://34.230.32.193:9200.
"""
if __name__ == '__main__':
    es_url = 'http://34.230.32.193:9200'
    author = "gmohandass"
    my_es = ESClient(es_url, author)
    my_es.publish_doc("https://www.freelancer.com/projects/graphic-design/build-website-15161743/", "freelancer")
