from src.tasks import publish_to_es_bulk
from commons.config import ES_URL
import scrapy

class CrawlerInterface(object):
    ''' Common parent to ensure objects are an interface '''

    def __init__(self, test=True):
        self.test = test

    def execute(self, keyword_list):
        ''' Crawl the site specifically for certain keywords '''
        raise NotImplementedError('You must implement the execute() method yourself!')

    def crawl(self):
        ''' Crawl all the site's job postings '''
        raise NotImplementedError('You must implement the crawl() method yourself!')

    def parse(self, response):
        ''' Parse a response page, which comes from urls in self.start_urls '''
        raise NotImplementedError('You must implement the parse() method yourself!')



class HTMLCrawlerInterface(CrawlerInterface):
    ''' Crawl site and just store raw html pages '''
    
    def add_to_queue(self, urls, website_name):
        publish_to_es_bulk.delay(es_host=ES_URL, url=urls, website_name=website_name,
                                 test=self.test)


class ParsingCrawlerInterface(CrawlerInterface):
    ''' Crawl site and parse html into structured dictionary '''
    
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

    def __init__(self, test=True, settings={}):
        super(ParsingCrawlerInterface, self).__init__(test)
        
        settings = scrapy.settings.Settings() 
        for key, value in self._default_settings.items():
            settings.set(key, value)
        for key, value in settings.items():
            settings.set(key, value)

        spider = self._construct_spider( self.parse.__func__ )
        self.crawler = scrapy.crawler.CrawlerRunner(settings)  
        

    def _construct_spider(self, base_parse):
        ''' Constructor to enable dynamic inheritance '''
        if not (self.authentication or self.elastic_db):
            parent_classes = [scrapy.Spider]
        else:
            parent_classes = []
            if self.elastic_db:
                parent_classes.append(ElasticSpider)
            if self.authentication:
                parent_classes.append(AuthenticationSpider)

        class ScrapySpider(*parent_classes): 
            def __init__(self, *args, **kwargs):
                ''' 
                Defining parse in this way is _so_ hacky, but at the moment
                it seems like the best way to merge with the existing code 
                base, while also allowing the classes which inherit from
                ParsingCrawlerInterface to just define parse() without worrying
                about the details of dynamic class inheritance.
                '''
                super(ScrapySpider, self).__init__(*args, **kwargs)
                parse = lambda *args, **kwargs: base_parse(self, *args, **kwargs)

        return ScrapySpider
