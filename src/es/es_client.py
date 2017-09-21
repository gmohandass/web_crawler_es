import functools
import json

import requests
import base64
from datetime import datetime
import uuid
from elasticsearch import Elasticsearch


class ESClient(object):
    def __init__(self, es_host, test_run=True):
        self.es = Elasticsearch([es_host])
        self.test_run = test_run
        self.index_name = "_".join(["crawler", "test", str(uuid.uuid4())]) if test_run else "crawler"

    @staticmethod
    def encode_docs(website_name, url):
        html_obj = requests.get(url).text
        html_obj = html_obj.encode('utf-8').strip()
        doc = {
            "data": base64.b64encode(html_obj),
            "website": website_name,
            "url": url,
            "timestamp": datetime.now()
        }
        return doc

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
            doc = self.encode_docs(website_name, url)
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

    def bulk_publish_docs(self, urls, website_name):
        try:
            encode_docs = functools.partial(self.encode_docs, website_name)
            docs = map(lambda url: json.dumps(encode_docs(url), default=str), urls)
            str_cnd = '\n{ "index" : { "_index" : %s, "_type" : "my_doc" } }\n' % ('"' + self.index_name + '"')
            docs = str_cnd[1:] + str_cnd.join(docs)
            if not self.test_run:
                today = datetime.today()
                self.index_name = "_".join([self.index_name, website_name, today.year,
                                            today.month, today.day])
            response = self.es.bulk(index=self.index_name,
                                    doc_type="my_doc",
                                    body=docs,
                                    pipeline="attachment")
            return response
        except Exception as e:
            raise e