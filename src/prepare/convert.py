#!/usr/bin/env python3
"""
Script to convert JSON metadata to XML and store in SQLite database.
"""

import os
import json
import sqlite3
from datetime import datetime
from lxml import etree
from tqdm import tqdm

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
JSON_DIR = os.path.join(DATA_DIR, "json")
XML_DIR = os.path.join(DATA_DIR, "xml")
PROV_DIR = os.path.join(DATA_DIR, "prov")
DB_PATH = os.path.join(DATA_DIR, "academic_metadata.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas", "metadata.xsd")
PROV_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas", "prov.xsd")

def ensure_dirs():
    """Ensure all required directories exist."""
    os.makedirs(XML_DIR, exist_ok=True)
    os.makedirs(PROV_DIR, exist_ok=True)

def create_database():
    """Create SQLite database with necessary tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create papers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id TEXT PRIMARY KEY,
        title TEXT,
        year INTEGER,
        venue TEXT,
        abstract TEXT,
        url TEXT,
        collected_at TEXT,
        source TEXT,
        version TEXT
    )
    ''')
    
    # Create authors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id TEXT,
        name TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers (id)
    )
    ''')
    
    # Create keywords table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id TEXT,
        keyword TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers (id)
    )
    ''')
    
    # Create provenance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS provenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id TEXT,
        prov_xml_path TEXT,
        FOREIGN KEY (paper_id) REFERENCES papers (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def create_prov_document(paper_data, collection_time):
    """Create a PROV-XML document for a paper."""
    nsmap = {'prov': 'http://www.w3.org/ns/prov#'}
    
    # Create document root
    doc = etree.Element('{http://www.w3.org/ns/prov#}Document', nsmap=nsmap)
    
    # Create entities section
    entities = etree.SubElement(doc, '{http://www.w3.org/ns/prov#}entities')
    
    # Paper entity
    paper_entity = etree.SubElement(entities, '{http://www.w3.org/ns/prov#}Entity')
    etree.SubElement(paper_entity, '{http://www.w3.org/ns/prov#}id').text = f"paper_{paper_data['id']}"
    etree.SubElement(paper_entity, '{http://www.w3.org/ns/prov#}type').text = 'Paper'
    
    # BibTeX entity
    bibtex_entity = etree.SubElement(entities, '{http://www.w3.org/ns/prov#}Entity')
    etree.SubElement(bibtex_entity, '{http://www.w3.org/ns/prov#}id').text = f"bibtex_{paper_data['id']}"
    etree.SubElement(bibtex_entity, '{http://www.w3.org/ns/prov#}type').text = 'BibTeX'
    
    # Create activities section
    activities = etree.SubElement(doc, '{http://www.w3.org/ns/prov#}activities')
    
    # Collection activity
    collection = etree.SubElement(activities, '{http://www.w3.org/ns/prov#}Activity')
    etree.SubElement(collection, '{http://www.w3.org/ns/prov#}id').text = f"collection_{paper_data['id']}"
    etree.SubElement(collection, '{http://www.w3.org/ns/prov#}type').text = 'DataCollection'
    etree.SubElement(collection, '{http://www.w3.org/ns/prov#}startTime').text = collection_time
    etree.SubElement(collection, '{http://www.w3.org/ns/prov#}endTime').text = collection_time
    
    # Create agents section
    agents = etree.SubElement(doc, '{http://www.w3.org/ns/prov#}agents')
    
    # System agent
    system = etree.SubElement(agents, '{http://www.w3.org/ns/prov#}Agent')
    etree.SubElement(system, '{http://www.w3.org/ns/prov#}id').text = 'system'
    etree.SubElement(system, '{http://www.w3.org/ns/prov#}type').text = 'SoftwareAgent'
    
    # Create relationships section
    relationships = etree.SubElement(doc, '{http://www.w3.org/ns/prov#}relationships')
    
    # WasGeneratedBy relationship
    generated = etree.SubElement(relationships, '{http://www.w3.org/ns/prov#}WasGeneratedBy')
    etree.SubElement(generated, '{http://www.w3.org/ns/prov#}entity').text = f"paper_{paper_data['id']}"
    etree.SubElement(generated, '{http://www.w3.org/ns/prov#}activity').text = f"collection_{paper_data['id']}"
    etree.SubElement(generated, '{http://www.w3.org/ns/prov#}time').text = collection_time
    
    # WasDerivedFrom relationship
    derived = etree.SubElement(relationships, '{http://www.w3.org/ns/prov#}WasDerivedFrom')
    etree.SubElement(derived, '{http://www.w3.org/ns/prov#}generatedEntity').text = f"paper_{paper_data['id']}"
    etree.SubElement(derived, '{http://www.w3.org/ns/prov#}usedEntity').text = f"bibtex_{paper_data['id']}"
    etree.SubElement(derived, '{http://www.w3.org/ns/prov#}activity').text = f"collection_{paper_data['id']}"
    etree.SubElement(derived, '{http://www.w3.org/ns/prov#}time').text = collection_time
    
    # WasAttributedTo relationship
    attributed = etree.SubElement(relationships, '{http://www.w3.org/ns/prov#}WasAttributedTo')
    etree.SubElement(attributed, '{http://www.w3.org/ns/prov#}entity').text = f"paper_{paper_data['id']}"
    etree.SubElement(attributed, '{http://www.w3.org/ns/prov#}agent').text = 'system'
    
    return doc

def json_to_xml(json_file):
    """Convert JSON metadata to XML format."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create XML structure
    paper = etree.Element("paper", id=data['id'])
    
    # Add basic metadata
    etree.SubElement(paper, "title").text = data['title']
    
    # Add authors
    authors = etree.SubElement(paper, "authors")
    for author in data['authors']:
        etree.SubElement(authors, "author").text = author
    
    # Add other fields
    etree.SubElement(paper, "year").text = str(data['year'])
    etree.SubElement(paper, "venue").text = data['venue']
    etree.SubElement(paper, "abstract").text = data['abstract']
    
    # Add keywords
    keywords = etree.SubElement(paper, "keywords")
    for keyword in data['keywords']:
        etree.SubElement(keywords, "keyword").text = keyword
    
    etree.SubElement(paper, "url").text = data['url']
    
    # Add provenance
    provenance = etree.SubElement(paper, "provenance")
    etree.SubElement(provenance, "collected_at").text = data['provenance']['collected_at']
    etree.SubElement(provenance, "source").text = data['provenance']['source']
    etree.SubElement(provenance, "version").text = data['provenance']['version']
    
    return paper

def store_in_database(data, conn):
    """Store paper metadata in SQLite database."""
    cursor = conn.cursor()
    
    # Insert paper data
    cursor.execute('''
    INSERT OR REPLACE INTO papers (id, title, year, venue, abstract, url, collected_at, source, version)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['id'],
        data['title'],
        data['year'],
        data['venue'],
        data['abstract'],
        data['url'],
        data['provenance']['collected_at'],
        data['provenance']['source'],
        data['provenance']['version']
    ))
    
    # Insert authors
    cursor.execute('DELETE FROM authors WHERE paper_id = ?', (data['id'],))
    for author in data['authors']:
        cursor.execute('INSERT INTO authors (paper_id, name) VALUES (?, ?)', (data['id'], author))
    
    # Insert keywords
    cursor.execute('DELETE FROM keywords WHERE paper_id = ?', (data['id'],))
    for keyword in data['keywords']:
        cursor.execute('INSERT INTO keywords (paper_id, keyword) VALUES (?, ?)', (data['id'], keyword))

def process_json_files():
    """Process all JSON files and convert to XML and store in database."""
    ensure_dirs()
    create_database()
    
    # Create root element for all papers
    papers = etree.Element("papers")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Process each JSON file
        json_files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
        for json_file in tqdm(json_files, desc="Processing JSON files"):
            try:
                # Read JSON data
                with open(os.path.join(JSON_DIR, json_file), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to XML
                paper_xml = json_to_xml(os.path.join(JSON_DIR, json_file))
                papers.append(paper_xml)
                
                # Store in database
                store_in_database(data, conn)
                
                # Generate and store PROV-XML
                prov_doc = create_prov_document(data, data['provenance']['collected_at'])
                prov_file = os.path.join(PROV_DIR, f"{data['id']}_prov.xml")
                tree = etree.ElementTree(prov_doc)
                tree.write(prov_file, pretty_print=True, encoding='utf-8', xml_declaration=True)
                
                # Store PROV-XML path in database
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO provenance (paper_id, prov_xml_path)
                VALUES (?, ?)
                ''', (data['id'], prov_file))
                
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")
        
        # Save complete XML file
        tree = etree.ElementTree(papers)
        tree.write(os.path.join(XML_DIR, "papers.xml"), pretty_print=True, encoding='utf-8', xml_declaration=True)
        
        # Commit database changes
        conn.commit()
        
    finally:
        conn.close()

def main():
    """Main function."""
    process_json_files()

if __name__ == "__main__":
    main() 