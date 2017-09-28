from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
import scrapy 

''' 
To use this class for authentication:
- pip install selenium 
- use AuthenticationSpider as your parent class rather than the normal scrapy.Spider 
- set the appropriate variables in your spider class (see below in FreelancerSpider)
- ensure you have 'chromedriver' in the correct location; this can be downloaded from 
	"http://chromedriver.storage.googleapis.com/$VERSION/chromedriver_$PLATFORM.zip"
	where $VERSION can be found at "http://chromedriver.storage.googleapis.com/LATEST_RELEASE"
	(currently 2.32), and $PLATFORM is one of [linux32, linux64, mac64, win32].
	So for windows, the current url is:
	http://chromedriver.storage.googleapis.com/2.32/chromedriver_win32.zip
	Just extract that file somewhere and point the DRIVER_LOCATION variable to it
'''

DRIVER_LOCATION = './chromedriver'

class AuthenticationSpider(scrapy.Spider):

	# Define these variables for login - see FreelancerSpider class below for an example
	username_element_path = '' 	# Path to username field
	password_element_path = ''  # Path to password field
	submit_element_path = ''  	# Path to the login button's field
	wait_element_path   = ''	# Optional. This waits on an element 
								# to load before getting cookies
	username = '' 
	password = ''
	login_url  = ''
	
	def __init__(self, *args, **kwargs):
		super(AuthenticationSpider, self).__init__(*args, **kwargs)
		self.login()

	def login(self):
		options = webdriver.ChromeOptions()
		options.add_argument('headless')
		driver = webdriver.Chrome(DRIVER_LOCATION, chrome_options=options)
		driver.get(self.login_url)

		username = driver.find_element_by_xpath(self.username_element_path)
		password = driver.find_element_by_xpath(self.password_element_path)
		submit   = driver.find_element_by_xpath(self.submit_element_path)

		username.send_keys(self.username)
		password.send_keys(self.password)
		submit.submit()

		# Some sites require additional cookies to load via ajax before full authentication,
		# so we wait for some element on the redirected page to signal that everything is finished
		if self.wait_element_path:
			self.logger.info('Waiting for all login cookies to load...')
			element = WebDriverWait(driver, 10).until(
				lambda x: x.find_element_by_xpath(self.wait_element_path))

		self._selenium_cookies = driver.get_cookies()
		driver.close()

	@classmethod
	def from_crawler(cls, crawler, *args, **kwargs):
		spider = super(AuthenticationSpider, cls).from_crawler(crawler, *args, **kwargs)
		crawler.signals.connect(spider.request_scheduled, scrapy.signals.request_scheduled)
		return spider

	def request_scheduled(self, request, spider):
		""" Attached login cookies to all requests """
		new_cookies = list(self._selenium_cookies)
		old_cookies = request.cookies
		if type(old_cookies) is dict: 
			old_cookies = [old_cookies]

		for cookie in old_cookies:
			if cookie: new_cookies.append(cookie)

		request.cookies = new_cookies
		self.logger.info('Added login cookies')


class FreelancerSpider(AuthenticationSpider):
	name = 'freelancer'
	start_urls = ['https://www.freelancer.com/dashboard/']

	# Define these variables for login
	username_element_path = '//*[@id="username"]' # Path to username field
	password_element_path = '//*[@id="passwd"]'   # Path to password field
	submit_element_path = '//*[@id="login_btn"]'  # Path to the login button's field
	wait_element_path   = '//*[@id="eventlist"]'  # Optional. This waits on an element 
												  # to load before getting cookies
	username = 'fakeemail1234@aol.com' 
	password = 'password1234'
	login_url  = 'https://www.freelancer.com/login'

	def parse(self, response):
		assert(response.url == self.start_urls[0]), \
			'Maybe failed to login? Url of response:' + str(response.url)
		print('Successfully logged in!')




