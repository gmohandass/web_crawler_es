from src.crawlers import *

import inspect
import sys

if __name__ == '__main__':

    current_module = sys.modules[__name__]
    scrappers = [x[1] for x in inspect.getmembers(current_module, inspect.isclass) if (issubclass(x[1], CrawlerInterface) and (x[1] != CrawlerInterface))]
    for scrapper in scrappers:
        scrapper(es_host='http://34.230.32.193:9200').execute(["Artificial Intelligence"])