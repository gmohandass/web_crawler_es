from commons.config  import ES_URL 
from scrapy.settings import Settings
from scrapy.crawler  import CrawlerProcess
from .elastic_spider import ElasticSpider
from .authentication_spider import AuthenticationSpider
from tasks import call_function
import scrapy


class CrawlerInterface(object):
    ''' Wraps both the crawler and the scrapy handler '''
    
    # Variables which can be overwritten in the inheriting class
    authenticate = False # Use authentication class
    elastic_db   = True  # Use elasticsearch class

    # Default crawler settings - can be overwritting by passing any key to the interface __init__
    _default_settings = {
        'USER_AGENT' : 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) '+
                       'Chrome/13.0.782.112 Safari/535.1',
        'RETRY_TIMES'         : 2,      # Number of time to re-request page on failure
        'ROBOTSTXT_OBEY'      : False,  # Obey robots.txt on the site
        'DOWNLOAD_DELAY'      : 5,      # Seconds between each page request on a site
        'COOKIES_ENABLED'     : True,   # Whether to use cookies
        'CONCURRENT_REQUESTS' : 1,      # Maximum concurrent requests sent
        'AUTOTHROTTLE_ENABLED'     : True,        # http://doc.scrapy.org/en/latest/topics/autothrottle.html
        'AUTOTHROTTLE_DEBUG'       : False,       # Show throttling stats for every response
        'AUTOTHROTTLE_MAX_DELAY'   : 20,          # The maximum download delay to be set in case of high latencies
        'AUTOTHROTTLE_START_DELAY' : 5,           # The initial download delay
        'AUTOTHROTTLE_TARGET_CONCURRENCY' : 1.0,  # Average number of requests to be sent in parallel
    }

    def __init__(self, settings={}):        
        settings = Settings() 
        for key, value in self._default_settings.items():
            settings.set(key, value)
        for key, value in settings.items():
            settings.set(key, value)

        self.spider = self._construct_spider()
        self.crawler= CrawlerProcess(settings)
        self.crawler.crawl(self.spider)
        self.crawl  = lambda: call_function(self.crawler.start)


    def _construct_spider(self):
        ''' Constructor to enable dynamic inheritance '''
        if not (self.authenticate or self.elastic_db):
            parent_classes = [scrapy.Spider]
        else:
            parent_classes = []
            if self.elastic_db:
                parent_classes.append(ElasticSpider)
            if self.authenticate:
                parent_classes.append(AuthenticationSpider)

        class ScrapySpider(*parent_classes): 
            def __init__(cls, *args, **kwargs):
                ''' 
                Dynamic inheritance and function definitions at run time
                '''
                for k,v in self.__class__.__dict__.items():
                    if callable(v):
                        f = getattr(self, k).__func__
                        cls.__dict__[k] = (lambda *args, __f=f, **kwargs:
                            __f(cls, *args, **kwargs)) # Bind function to lambda
                    elif '__' not in k:
                        cls.__dict__[k] = v

                super(ScrapySpider, cls).__init__(*args, **kwargs)
                
            def from_crawler(self, *args, **kwargs): return self
        return ScrapySpider()


    def execute(self, keyword_list):
        ''' Crawl the site specifically for certain keywords '''
        self.spider.start_urls = [self.search_url % kw for kw in keyword_list]
        self.crawl()

