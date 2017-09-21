

import requests
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector

from crawler_interface import CrawlerInterface


class Freelancer(CrawlerInterface):
    def __init__(self, es_host, base_url, test=True):
        super(Freelancer, self).__init__(es_host, test)
        self.base_url = base_url

    def construct_search_query(self, keyword_lst):
        payloads = [{'keyword': keyword} for keyword in keyword_lst]
        base_url = self.base_url + "/jobs/regions"
        return (requests.get(base_url, params=payload) for payload in payloads)

    def grab_projects(self, resp):
        http_encoding = resp.encoding if 'charset' in resp.headers.get('content-type', '').lower() else None
        html_encoding = EncodingDetector.find_declared_encoding(resp.content, is_html=True)
        encoding = html_encoding or http_encoding
        soup = BeautifulSoup(resp.content, from_encoding=encoding)
        links = [self.base_url + link['href'] for link in soup.find_all('a', href=True) if
                 link['href'].startswith("/projects/")]
        # TODO: Send everything to es (possibly bulk)
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
            self.spyder(requests.get(self.base_url + next_page_link), next_page_link)

    def printt(self):
        print "test"

    def execute(self, keyword_list):
        main_results = self.construct_search_query(keyword_list)
        for res in main_results:
            self.spyder(res)


freelancer = Freelancer(es_host='http://34.230.32.193:9200', base_url="https://www.freelancer.com")
freelancer.execute(["Artificial Intelligence"])
