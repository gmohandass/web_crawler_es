from elastic_spider import ElasticSpider
import scrapy 
import json 

CATEGORY = 'data-science-analytics'
MAX_PAGE = 1

# Path to individual job links
LISTING_PATH = 'a.job-title-link::attr(href)'
NEXT_PG_PATH = 'ul.pagination li.next a::attr(href)'

# Paths to elements on a job listing page
CONTAINER_PATH 	= 'div#layout div.container'
TITLE_PATH 		= 'h1::text'
SKILL_PATH 		= 'a.o-tag-skill::text'
POSTED_PATH 	= 'span[itemprop="datePosted"]::attr("data-eo-popover-html-unsafe")'
INFO_PRIME_PATH = 'p.m-0-bottom strong::text'  # Hourly/Fixed, Expertise level
INFO_SUB_PATH   = 'p.m-0-bottom ~ small::text' # Rate/Time period, Start date 
DETAIL_PATH     = 'p.break::text'
DETAIL_MISC_PATH= 'p.break ~ ul li'
OTHER_SKILL_PATH= 'p.break ~ ul li span::attr("data-ng-init")'

# Path to client info on job listing page 
CLIENT_INFO_PATH = 'div.col-md-3 p.m-md-bottom'
CLIENT_JOIN_PATH = 'div.col-md-3 p.m-md-bottom ~ small::text'


class UpworkSpider(ElasticSpider):
	name  = 'upwork'
	index_name = 'crawler_upwork_test'
	start_urls = ['https://www.upwork.com/o/jobs/browse/c/%s/' % CATEGORY]


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
		data = { 'link'	: response.url }

		# Strip results after extracting all
		strip_list    = lambda lst: [s.strip() for s in lst]
		strip_extract = lambda css_path: strip_list(base.css(css_path).extract())
		string_extract= lambda css_path: strip_list(base.css(css_path).xpath('string()').extract())

		# Create lambda functions then wrap in try/except to avoid any fatal breaks
		field_functions = {
			'title'     : lambda: strip_extract(TITLE_PATH)[0],
			'skills'	: lambda: strip_extract(SKILL_PATH),
			'posted'	: lambda: strip_extract(POSTED_PATH)[0],
			'pay_type'  : lambda: strip_extract(INFO_PRIME_PATH)[0],
			'expertise' : lambda: strip_extract(INFO_PRIME_PATH)[1],
			'pay_detail': lambda: strip_extract(INFO_SUB_PATH)[:-1],
			'start_date': lambda: strip_extract(INFO_SUB_PATH)[-1],
			'detail'    : lambda: strip_extract(DETAIL_PATH),

			# Unsure of all potential values at this point; seen: project type, project stage, ...
			'detail_misc' : lambda: string_extract(DETAIL_MISC_PATH), 

			# Technically part of detail_misc, but contains a _lot_ of info on other skills, not parsable 
			# from just the string due to being hidden in an attribute. Likely pretty fragile.
			'other_skills': lambda: json.loads(strip_extract(OTHER_SKILL_PATH)[0].split('skills = ')[1]),
		
			# Client info
			'client_location'  : lambda: string_extract(CLIENT_INFO_PATH)[1],
			'client_history'   : lambda: string_extract(CLIENT_INFO_PATH)[2:],
			'client_join_date' : lambda: strip_extract(CLIENT_JOIN_PATH)[0],
		}

		for field in field_functions:
			try: 	
				data[field] = field_functions[field]()
			except Exception as e:
				self.log('Exception fetching field "%s": %s' % (field, e))
				data[field] = None

		self.add_to_db(data)
		yield data 
