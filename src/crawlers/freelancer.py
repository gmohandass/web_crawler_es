import requests
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector

from crawler_interface import CrawlerInterface


class Freelancer(CrawlerInterface):
    def __init__(self, es_host, test=True):
        super(Freelancer, self).__init__(es_host, test)
        self.NAME = "freelancer"
        self.BASE_URL = "https://www.freelancer.com"

    def construct_search_query(self, keyword_lst):
        payloads = [{'keyword': keyword} for keyword in keyword_lst]
        base_url = self.BASE_URL + "/jobs/regions"
        return (requests.get(base_url, params=payload) for payload in payloads)

    def grab_projects(self, resp):
        http_encoding = resp.encoding if 'charset' in resp.headers.get('content-type', '').lower() else None
        html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(resp.content, from_encoding=encoding)
        links = [self.BASE_URL + link['href'] for link in soup.find_all('a', href=True) if
                 link['href'].startswith("/projects/")]
        self.add_to_queue(urls=links, website_name=self.NAME)
        return len(links)

    def spyder(self, search_result_html, pagination=None):
        project_len = self.grab_projects(search_result_html)
        if project_len > 0:
            soup = BeautifulSoup(search_result_html.text)
            next_page_link = pagination
            if not pagination:
                elm = soup.find('a', {'class': 'Pagination-item'})
                next_page_link = elm['href']

            next_page_link_root, keyword = next_page_link.split("?")
            next_page_link = "?".join(["".join(map(lambda s: str(int(s) + 1) if s.isdigit() else s,
                                                   list(next_page_link_root))), keyword])
            self.spyder(requests.get(self.BASE_URL + next_page_link), next_page_link)

    def execute(self, keyword_list):
        main_results = self.construct_search_query(keyword_list)
        for res in main_results:
            self.spyder(res)
