import os
import json
import sqlite3
from glob import glob

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
DB_PATH = os.path.join(DATA_DIR, "academic_metadata.db")

def ensure_tables(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id TEXT PRIMARY KEY,
            title TEXT,
            year INTEGER,
            venue TEXT,
            abstract TEXT,
            url TEXT,
            collected_at TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT,
            name TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id TEXT,
            keyword TEXT
        )
    ''')
    conn.commit()

def sync_json_to_db():
    conn = sqlite3.connect(DB_PATH)
    ensure_tables(conn)
    cur = conn.cursor()

    json_files = glob(os.path.join(JSON_DIR, '*.json'))
    print(f"Found {len(json_files)} JSON files.")

    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        paper_id = data.get('id')
        title = data.get('title', '')
        year = int(data.get('year', 0)) if data.get('year') else None
        venue = data.get('venue', '')
        abstract = data.get('abstract', '')
        url = data.get('url', '')
        collected_at = data.get('provenance', {}).get('collected_at', '')
        authors = data.get('authors', [])
        keywords = data.get('keywords', [])

        # Upsert paper
        cur.execute('''
            INSERT OR REPLACE INTO papers (id, title, year, venue, abstract, url, collected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (paper_id, title, year, venue, abstract, url, collected_at))

        # Remove old authors/keywords for this paper
        cur.execute('DELETE FROM authors WHERE paper_id = ?', (paper_id,))
        cur.execute('DELETE FROM keywords WHERE paper_id = ?', (paper_id,))

        # Insert authors
        for author in authors:
            if author.strip():
                cur.execute('INSERT INTO authors (paper_id, name) VALUES (?, ?)', (paper_id, author.strip()))

        # Insert keywords
        for keyword in keywords:
            if keyword.strip():
                cur.execute('INSERT INTO keywords (paper_id, keyword) VALUES (?, ?)', (paper_id, keyword.strip()))

    conn.commit()
    conn.close()
    print("Database sync complete.")

if __name__ == "__main__":
    sync_json_to_db() 