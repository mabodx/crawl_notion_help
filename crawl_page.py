import requests
from bs4 import BeautifulSoup
import openai
import csv
import json

# Load the API key from the config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    openai.api_key = config['openai_api_key']

def extract_core_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    core_text = []
    for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol']):
        if element.name in ['h1', 'h2', 'h3']:
            core_text.append(f"\n{element.get_text()}\n")
        elif element.name == 'p':
            core_text.append(f"{element.get_text()}\n")
        elif element.name in ['ul', 'ol']:
            for li in element.find_all('li'):
                core_text.append(f"- {li.get_text()}\n")
    return core_text

def format_text_with_llm(text):
    prompt = f"Please clean up and format the following text:\n\n{text}\n\nMake sure the output is clean, readable, and well-structured."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
        temperature=0.5
    )
    return response.choices[0].message['content'].strip()

def split_into_chunks(text_list, max_chunk_size=750):
    chunks = []
    current_chunk = ""
    current_list = []
    for text in text_list:
        if text.startswith('- '):
            if current_list:
                if len(current_chunk) + len("\n".join(current_list)) <= max_chunk_size:
                    current_chunk += "\n".join(current_list) + "\n"
                    current_list = []
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = "\n".join(current_list) + "\n"
                    current_list = []
            current_list.append(text)
        else:
            if current_list:
                if len(current_chunk) + len("\n".join(current_list)) <= max_chunk_size:
                    current_chunk += "\n".join(current_list) + "\n"
                    current_list = []
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = "\n".join(current_list) + "\n"
                    current_list = []
            if len(current_chunk) + len(text) <= max_chunk_size:
                current_chunk += text
            else:
                chunks.append(current_chunk.strip())
                current_chunk = text
    if current_list:
        current_chunk += "\n".join(current_list) + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def process_urls(urls):
    all_chunks = {}
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
            core_text = extract_core_text(response.content)
            formatted_text = format_text_with_llm("".join(core_text))
            chunks = split_into_chunks(formatted_text.splitlines())
            all_chunks[url] = chunks
            print(f"Processed {url} successfully.")
            break
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
    return all_chunks

def read_urls_from_csv(file_path):
    urls = []
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            urls.append(row[0])
    return urls

def write_chunks_to_csv(chunks_dict, file_path):
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        for url, chunks in chunks_dict.items():
            for i, chunk in enumerate(chunks):
                writer.writerow([url, i + 1, chunk])

urls = read_urls_from_csv('all_page_example.csv')
articles_chunks = process_urls(urls)
write_chunks_to_csv(articles_chunks, 'processed_articles.csv')

print("All URLs have been processed and chunks have been saved to 'processed_articles.csv'.")
