from urllib.parse import urlparse
from collections import defaultdict
from bs4 import BeautifulSoup
import httpx
import asyncio


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def categorize_by_domain(urls):
    domain_counts = defaultdict(int)
    for url in urls:
        domain = get_domain(url['href'])
        domain_counts[domain] += 1
    return domain_counts


def parse_bookmarks(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return [{'href': link.get('href'), 'title': link.get_text()} for link in soup.find_all('a')]


async def check_url(url):
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(url['href'], timeout=5)
            return response.status_code == 200
    except httpx.RequestError:
        return False


async def check_urls(urls):
    return await asyncio.gather(*(check_url(url) for url in urls))


def find_duplicates(bookmarks):
    url_counts = {}
    for bookmark in bookmarks:
        if bookmark['href'] in url_counts:
            url_counts[bookmark['href']]['count'] += 1
        else:
            url_counts[bookmark['href']] = {'count': 1, 'bookmark': bookmark}
    return {url: item for url, item in url_counts.items() if item['count'] > 1}
