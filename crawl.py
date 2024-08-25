import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv

def is_valid_url(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    return (parsed_url.netloc == 'www.notion.so' and 
            path.startswith('/help') and
            'notion-academy' not in path)

def crawl_url(url):
    links = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if is_valid_url(full_url):
                    links.append(full_url)
    except requests.RequestException as e:
        print(f"Error during requests to {url} : {e}")
    return links

def read_csv_into_list(file_path):
    urls = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip the header row if present
        for row in csvreader:
            urls.extend(row)  # Each row can have multiple URLs
    return urls

def crawl_all_urls_from_csv(csv_file_path):
    start_urls = read_csv_into_list(csv_file_path)
    all_valid_links = set()  # Using a set to avoid duplicates
    
    for url in start_urls:
        if is_valid_url(url):
            valid_links = crawl_url(url)
            all_valid_links.update(valid_links)
    
    return list(all_valid_links)

csv_file_path = 'urls.csv'  # Replace with your CSV file path
all_valid_links = crawl_all_urls_from_csv(csv_file_path)

for link in all_valid_links:
    print(link)
