#!/usr/bin/env python3
"""
Script to add keywords to existing paper JSON files.
"""

import os
import json
import logging
from tqdm import tqdm
import spacy
from rake_nltk import Rake
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
JSON_DIR = os.path.join(DATA_DIR, "json")

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
    
    # Ensure text and title are strings
    text = str(text) if text is not None else ""
    title = str(title) if title is not None else ""
    
    # Combine title and text for better context
    combined_text = f"{title} {text}" if title else text
    combined_text = clean_text(combined_text)
    
    if not combined_text:
        return []
    
    # Extract keywords using RAKE
    rake.extract_keywords_from_text(combined_text)
    rake_keywords = []
    try:
        for kw, score in rake.get_ranked_phrases_with_scores():
            try:
                # Convert score to float safely
                score_value = float(score) if isinstance(score, (int, float, str)) else 0.0
                if score_value > 1.0:
                    rake_keywords.append(str(kw).strip())
            except (ValueError, TypeError):
                continue
    except Exception as e:
        logger.warning(f"Error processing RAKE keywords: {str(e)}")
    
    # Extract keywords using spaCy
    try:
        doc = nlp(combined_text)
        spacy_keywords = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 4:  # Limit to 4-word phrases
                spacy_keywords.append(str(chunk.text).lower().strip())
        
        # Extract individual important words
        for token in doc:
            if (token.pos_ in ("NOUN", "PROPN", "ADJ") and 
                not token.is_stop and 
                len(token.text) > 2 and
                not str(token.text).isdigit()):
                spacy_keywords.append(str(token.text).lower().strip())
    except Exception as e:
        logger.warning(f"Error processing spaCy keywords: {str(e)}")
        spacy_keywords = []
    
    # Combine and deduplicate keywords
    all_keywords = set(rake_keywords + spacy_keywords)
    
    # Filter and prioritize domain-specific terms
    domain_keywords = []
    other_keywords = []
    
    for keyword in all_keywords:
        try:
            if any(term in keyword or keyword in term for term in NLP_DOMAIN_TERMS):
                domain_keywords.append(str(keyword).strip())
            else:
                other_keywords.append(str(keyword).strip())
        except Exception:
            continue
    
    # Return top keywords, prioritizing domain-specific terms
    final_keywords = domain_keywords + other_keywords
    return final_keywords[:15]  # Return top 15 keywords

def process_json_file(json_file):
    """Process a single JSON file and add keywords."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            paper_data = json.load(f)
        
        # Extract keywords from title and abstract
        title = paper_data.get('title', '')
        abstract = paper_data.get('abstract', '')
        keywords = extract_keywords(abstract, title)
        
        # Update paper data with keywords
        paper_data['keywords'] = keywords
        
        # Save updated data
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger.error(f"Error processing {json_file}: {str(e)}")
        return False

def main():
    """Main function to process all JSON files."""
    # Get all JSON files
    json_files = list(Path(JSON_DIR).glob('*.json'))
    total_files = len(json_files)
    logger.info(f"Found {total_files} JSON files to process")
    
    # Process files with progress bar
    processed = 0
    updated = 0
    
    for json_file in tqdm(json_files, desc="Processing papers"):
        if process_json_file(json_file):
            updated += 1
        processed += 1
        
        # Log progress every 100 files
        if processed % 100 == 0:
            logger.info(f"Progress: {processed}/{total_files} files processed ({updated} updated)")
    
    logger.info(f"Completed processing {total_files} files")
    logger.info(f"Updated {updated} files with keywords")

if __name__ == "__main__":
    main() 