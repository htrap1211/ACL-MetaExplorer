#!/usr/bin/env python3
"""
Script to scrape paper metadata from ACL Anthology.
"""

import os
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import bibtexparser
from urllib.parse import urljoin
import spacy
from collections import Counter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rake_nltk import Rake
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://aclanthology.org/events/"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
RAW_HTML_DIR = os.path.join(DATA_DIR, "raw_html")
BIBTEX_DIR = os.path.join(DATA_DIR, "bibtex")
JSON_DIR = os.path.join(DATA_DIR, "json")

# Configure requests session with retries
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
session.mount('https://', HTTPAdapter(max_retries=retries))
session.mount('http://', HTTPAdapter(max_retries=retries))

# NLP setup
try:
    nlp = spacy.load("en_core_web_sm")
    rake = Rake(min_length=1, max_length=4)  # Allow phrases up to 4 words
except OSError:
    logger.error("Please install the required models by running: python -m spacy download en_core_web_sm")
    raise

# Domain-specific terms and stopwords
NLP_DOMAIN_TERMS = {
    'nlp', 'natural language processing', 'machine learning', 'deep learning',
    'transformer', 'bert', 'gpt', 'llm', 'language model', 'neural network',
    'translation', 'summarization', 'classification', 'sentiment analysis',
    'tokenization', 'embedding', 'vector', 'semantic', 'syntax', 'parsing',
    'dependency', 'pos tagging', 'named entity', 'ner', 'coreference',
    'question answering', 'qa', 'dialogue', 'conversation', 'chatbot',
    'text generation', 'text mining', 'information extraction', 'ie',
    'knowledge graph', 'kg', 'ontology', 'wordnet', 'glove', 'word2vec',
    'fasttext', 'elmo', 'transformer', 'attention', 'self-attention',
    'encoder', 'decoder', 'seq2seq', 'sequence to sequence', 'lstm',
    'gru', 'rnn', 'recurrent neural network', 'cnn', 'convolutional',
    'transfer learning', 'fine-tuning', 'pre-training', 'zero-shot',
    'few-shot', 'prompt', 'prompting', 'chain of thought', 'cot',
    'instruction tuning', 'alignment', 'rlhf', 'reinforcement learning',
    'human feedback', 'evaluation', 'metrics', 'bleu', 'rouge', 'meteor',
    'perplexity', 'accuracy', 'precision', 'recall', 'f1', 'auc',
    'cross-validation', 'hyperparameter', 'optimization', 'gradient',
    'backpropagation', 'loss function', 'objective', 'regularization',
    'dropout', 'batch normalization', 'layer normalization', 'activation',
    'relu', 'gelu', 'softmax', 'cross entropy', 'adam', 'sgd', 'momentum',
    'learning rate', 'scheduler', 'warmup', 'decay', 'early stopping',
    'overfitting', 'underfitting', 'bias', 'variance', 'ensemble',
    'bagging', 'boosting', 'random forest', 'svm', 'support vector',
    'kernel', 'clustering', 'k-means', 'hierarchical', 'topic modeling',
    'lda', 'latent dirichlet allocation', 'pca', 'dimensionality reduction',
    'visualization', 't-sne', 'umap', 'word cloud', 'heatmap', 'confusion matrix'
}

def clean_text(text):
    """Clean and normalize text."""
    if not text or not isinstance(text, str):
        return ""
    
    # Remove special characters and normalize whitespace
    text = re.sub(r'[^\w\s-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def extract_keywords(text, title=""):
    """Extract keywords from text using multiple methods."""
    if not text and not title:
        return []
    
    # Combine title and text for better context
    combined_text = f"{title} {text}" if title else text
    combined_text = clean_text(combined_text)
    
    if not combined_text:
        return []
    
    # Extract keywords using RAKE
    rake.extract_keywords_from_text(combined_text)
    rake_keywords = [kw for kw, score in rake.get_ranked_phrases_with_scores() if score > 1.0]
    
    # Extract keywords using spaCy
    doc = nlp(combined_text)
    spacy_keywords = []
    
    # Extract noun phrases
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 4:  # Limit to 4-word phrases
            spacy_keywords.append(chunk.text.lower())
    
    # Extract individual important words
    for token in doc:
        if (token.pos_ in ("NOUN", "PROPN", "ADJ") and 
            not token.is_stop and 
            len(token.text) > 2 and
            not token.text.isdigit()):
            spacy_keywords.append(token.text.lower())
    
    # Combine and deduplicate keywords
    all_keywords = set(rake_keywords + spacy_keywords)
    
    # Filter and prioritize domain-specific terms
    domain_keywords = []
    other_keywords = []
    
    for keyword in all_keywords:
        if any(term in keyword or keyword in term for term in NLP_DOMAIN_TERMS):
            domain_keywords.append(keyword)
        else:
            other_keywords.append(keyword)
    
    # Return top keywords, prioritizing domain-specific terms
    final_keywords = domain_keywords + other_keywords
    return final_keywords[:15]  # Return top 15 keywords

def ensure_dirs():
    """Ensure all required directories exist."""
    for directory in [RAW_HTML_DIR, BIBTEX_DIR, JSON_DIR]:
        os.makedirs(directory, exist_ok=True)

def download_html(year):
    """Download HTML page for a specific year."""
    url = f"{BASE_URL}acl-{year}/"
    output_file = os.path.join(RAW_HTML_DIR, f"acl_{year}.html")
    
    if os.path.exists(output_file):
        logger.info(f"HTML file for {year} already exists")
        return output_file
    
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logger.info(f"Downloaded HTML for {year}")
        return output_file
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Proceedings for {year} are not yet available")
            return None
        logger.error(f"Error downloading HTML for {year}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error downloading HTML for {year}: {str(e)}")
        return None

def extract_bibtex_links(html_file):
    """Extract BibTeX links from HTML file."""
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'lxml')
    
    bibtex_links = []
    for link in soup.find_all('a', href=True):
        if link['href'].endswith('.bib'):
            # Convert relative URL to absolute URL
            full_url = urljoin(BASE_URL, link['href'])
            bibtex_links.append(full_url)
    
    return bibtex_links

def download_bibtex(url, year):
    """Download BibTeX content."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Extract paper ID from URL
        paper_id = url.split('/')[-1].replace('.bib', '')
        output_file = os.path.join(BIBTEX_DIR, f"{paper_id}.bib")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return output_file
    except Exception as e:
        logger.error(f"Error downloading BibTeX from {url}: {str(e)}")
        return None

def scrape_abstract(url):
    """Scrape abstract from paper page."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # First try the main abstract div
        abstract_div = soup.find('div', class_='card-body acl-abstract')
        if abstract_div:
            abstract_text = abstract_div.find('span')
            if abstract_text:
                abstract = abstract_text.get_text(strip=True)
                if abstract:
                    logger.info(f"Found abstract for {url}")
                    return abstract
        
        # Try the abstract div with different class names
        for class_name in ['abstract', 'abstract-section', 'abstract-content']:
            abstract_div = soup.find('div', class_=class_name)
            if abstract_div:
                abstract = abstract_div.get_text(strip=True)
                if abstract:
                    logger.info(f"Found abstract for {url} in {class_name}")
                    return abstract
        
        # Try finding any div with 'abstract' in its class name
        for div in soup.find_all('div', class_=lambda x: x and 'abstract' in x.lower()):
            abstract = div.get_text(strip=True)
            if abstract and len(abstract) > 50:  # Ensure it's a reasonable length
                logger.info(f"Found abstract for {url} in generic abstract div")
                return abstract
        
        # Try finding any paragraph with 'abstract' in its class name
        for p in soup.find_all('p', class_=lambda x: x and 'abstract' in x.lower()):
            abstract = p.get_text(strip=True)
            if abstract and len(abstract) > 50:  # Ensure it's a reasonable length
                logger.info(f"Found abstract for {url} in abstract paragraph")
                return abstract
        
        # Try finding any element with 'abstract' in its id
        for element in soup.find_all(id=lambda x: x and 'abstract' in x.lower()):
            abstract = element.get_text(strip=True)
            if abstract and len(abstract) > 50:  # Ensure it's a reasonable length
                logger.info(f"Found abstract for {url} in element with abstract id")
                return abstract
        
        # If still not found, try to find any text that looks like an abstract
        # Look for text that starts with common abstract indicators
        abstract_indicators = ['abstract:', 'abstract', 'summary:', 'summary']
        for element in soup.find_all(['p', 'div']):
            text = element.get_text(strip=True).lower()
            if any(text.startswith(indicator) for indicator in abstract_indicators):
                abstract = element.get_text(strip=True)
                if len(abstract) > 50:  # Ensure it's a reasonable length
                    logger.info(f"Found abstract for {url} by text pattern")
                    return abstract
        
        logger.warning(f"No abstract found for {url}")
        return ""
        
    except Exception as e:
        logger.error(f"Error scraping abstract from {url}: {str(e)}")
        return ""

def parse_bibtex(bibtex_file):
    """Parse BibTeX file and convert to JSON."""
    try:
        with open(bibtex_file, 'r', encoding='utf-8') as f:
            bibtex_str = f.read()
        
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_database = bibtexparser.loads(bibtex_str, parser=parser)
        
        if not bib_database.entries:
            return None
        
        # Convert to our desired format
        entry = bib_database.entries[0]
        paper_id = os.path.basename(bibtex_file).replace('.bib', '')
        paper_url = entry.get('url', '')
        title = entry.get('title', '').strip('{}')
        
        # Scrape abstract from paper page
        abstract = scrape_abstract(paper_url)
        
        # Extract keywords from both title and abstract
        extracted_keywords = extract_keywords(abstract, title)
        
        paper_data = {
            'id': paper_id,
            'title': title,
            'authors': [author.strip() for author in entry.get('author', '').split(' and ')],
            'year': entry.get('year', ''),
            'venue': entry.get('booktitle', ''),
            'abstract': abstract,
            'keywords': extracted_keywords,
            'url': paper_url,
            'provenance': {
                'collected_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'ACL Anthology',
                'version': '1.0'
            }
        }
        
        # Save as JSON
        json_file = os.path.join(JSON_DIR, f"{paper_data['id']}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)
        
        return json_file
    except Exception as e:
        logger.error(f"Error parsing BibTeX file {bibtex_file}: {str(e)}")
        return None

def process_papers(years):
    """Process papers for specified years."""
    ensure_dirs()
    
    for year in years:
        logger.info(f"Processing papers from {year}")
        
        # Download HTML
        html_file = download_html(year)
        if not html_file:
            continue
        
        # Extract BibTeX links
        bibtex_links = extract_bibtex_links(html_file)
        logger.info(f"Found {len(bibtex_links)} BibTeX links for {year}")
        
        # Process each BibTeX file
        successful = 0
        failed = 0
        
        for link in tqdm(bibtex_links, desc=f"Processing {year} papers"):
            try:
                bibtex_file = download_bibtex(link, year)
                if bibtex_file:
                    json_file = parse_bibtex(bibtex_file)
                    if json_file:
                        successful += 1
                        logger.debug(f"Successfully processed {os.path.basename(bibtex_file)}")
                    else:
                        failed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error processing {link}: {str(e)}")
                failed += 1
            
            # Be nice to the server but reduce sleep time
            time.sleep(0.5)
            
            # Log progress every 100 papers
            if (successful + failed) % 100 == 0:
                logger.info(f"Progress for {year}: {successful + failed}/{len(bibtex_links)} papers processed "
                          f"({successful} successful, {failed} failed)")
        
        logger.info(f"Completed processing {year}: {successful} successful, {failed} failed")

def main():
    """Main function."""
    # Process papers from 2023 to 2024
    years = range(2023, 2025)
    process_papers(years)

if __name__ == "__main__":
    main() 