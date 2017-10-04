from .crawler_interface import CrawlerInterface
import scrapy 
import json 

CATEGORY = 'data-science-analytics'
MAX_PAGE = 1

# Path to individual job links
LISTING_PATH = 'a.job-title-link::attr(href)'
NEXT_PG_PATH = 'ul.pagination li.next a::attr(href)'

# Path to elements' container on a job listing page
CONTAINER_PATH 	= 'div#layout div.container'


class UpworkSpider(CrawlerInterface):
	name = 'upwork'
	index_name = 'crawler_upwork_test'
	search_url = 'https://www.upwork.com/o/jobs/browse/?q=%s'


	def parse(self, response):
		curr_pg = response.url.split('?page=')[-1]
		curr_pg = curr_pg if len(curr_pg) < 5 else '1'
		self.log('Starting page %s' % curr_pg)
		
		for link in response.css(LISTING_PATH).extract():
			uid = link if '~' not in link else link.split('~')[-1].strip('/')
			if self.exists_in_db(uid, 'link'):
				self.log('Stopping list scrape: link exists in the database')
				return
			yield response.follow(link, self.parse_post)

		self.log('Done page %s' % curr_pg)
		if int(curr_pg) >= MAX_PAGE: return

		next_page = response.css(NEXT_PG_PATH).extract_first()
		yield response.follow(next_page, self.parse)


	def parse_post(self, response):
		base = response.css(CONTAINER_PATH)
		data = { 
			'url'	: response.url,
			'data'  : base.xpath('string()').extract_first(),
		}
		self.add_to_db(data)
		yield data 