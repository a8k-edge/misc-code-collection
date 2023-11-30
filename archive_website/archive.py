import requests
import sqlite3
import hashlib
from datetime import datetime

conn = sqlite3.connect('web_archive.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS website_changes (
    url TEXT, 
    content_hash TEXT, 
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)''')


def fetch_url(url):
    response = requests.get(url)
    return response.text


def get_content_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()


def archive_url(url):
    content = fetch_url(url)
    content_hash = get_content_hash(content)

    c.execute('SELECT content_hash FROM website_changes WHERE url = ? ORDER BY timestamp DESC LIMIT 1', (url,))
    result = c.fetchone()

    if result and result[0] == content_hash:
        print(f"No changes detected for {url}.")
    else:
        if result:
            print(f"Content of {url} has changed. Archiving new version...")
        else:
            print(f"Archiving new URL: {url}")

        c.execute('INSERT INTO website_changes (url, content_hash) VALUES (?, ?)', (url, content_hash))
        conn.commit()


archive_url('http://example.com')
conn.close()
