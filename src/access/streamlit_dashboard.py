import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import spacy
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "academic_metadata.db")

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("Please install the spaCy model by running: python -m spacy download en_core_web_sm")
    st.stop()

def extract_keywords(text):
    """Extract keywords from text using spaCy."""
    if not text or not isinstance(text, str):
        return []
    
    doc = nlp(text)
    # Extract nouns, proper nouns, and important adjectives
    keywords = []
    for token in doc:
        if (token.pos_ in ("NOUN", "PROPN", "ADJ") and 
            not token.is_stop and 
            len(token.text) > 2 and
            not token.text.isdigit()):
            keywords.append(token.text.lower())
    
    # Count frequencies and get top keywords
    keyword_freq = Counter(keywords)
    return [kw for kw, _ in keyword_freq.most_common(10)]

def analyze_trends(papers_df):
    """Analyze keyword trends over time."""
    # Filter papers with non-empty abstracts
    papers_with_abstracts = papers_df[papers_df['abstract'].str.strip() != ''].copy()
    
    if len(papers_with_abstracts) == 0:
        return None
    
    # Extract keywords from abstracts
    papers_with_abstracts['extracted_keywords'] = papers_with_abstracts['abstract'].apply(extract_keywords)
    
    # Count keywords per year
    yearly_keywords = {}
    for year in papers_with_abstracts['year'].unique():
        year_papers = papers_with_abstracts[papers_with_abstracts['year'] == year]
        keywords = [kw for keywords_list in year_papers['extracted_keywords'] for kw in keywords_list]
        yearly_keywords[year] = Counter(keywords)
    
    return yearly_keywords

def plot_trends(yearly_keywords, top_n=10):
    """Plot keyword trends over time."""
    # Check if we have any data
    if not yearly_keywords:
        return None
    
    # Get top keywords across all years
    all_keywords = Counter()
    for year_counter in yearly_keywords.values():
        all_keywords.update(year_counter)
    
    if not all_keywords:
        return None
        
    top_keywords = [kw for kw, _ in all_keywords.most_common(top_n)]
    
    # Prepare data for plotting
    years = sorted(yearly_keywords.keys())
    data = []
    for keyword in top_keywords:
        for year in years:
            count = yearly_keywords[year].get(keyword, 0)
            data.append({'Year': year, 'Keyword': keyword, 'Count': count})
    
    if not data:
        return None
        
    df = pd.DataFrame(data)
    
    # Create line plot
    fig = px.line(df, x='Year', y='Count', color='Keyword',
                  title='Top Keyword Trends Over Time',
                  labels={'Count': 'Frequency', 'Year': 'Publication Year'})
    
    return fig

def load_data():
    """Load data from SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    
    # Load papers with optimized query
    papers_df = pd.read_sql_query("""
        SELECT 
            p.id,
            p.title,
            p.year,
            p.venue,
            p.abstract,
            p.url,
            p.collected_at,
            GROUP_CONCAT(DISTINCT a.name) as authors,
            GROUP_CONCAT(DISTINCT k.keyword) as keywords
        FROM papers p
        LEFT JOIN authors a ON p.id = a.paper_id
        LEFT JOIN keywords k ON p.id = k.paper_id
        GROUP BY p.id
    """, conn)
    
    # Convert authors and keywords strings to lists, handling None values
    papers_df['authors'] = papers_df['authors'].apply(lambda x: x.split(',') if pd.notna(x) else [])
    papers_df['keywords'] = papers_df['keywords'].apply(lambda x: x.split(',') if pd.notna(x) else [])
    
    # Ensure all text fields are strings and handle None values
    text_columns = ['venue', 'abstract', 'title']
    for col in text_columns:
        papers_df[col] = papers_df[col].fillna('').astype(str)
        # Remove any extra whitespace
        papers_df[col] = papers_df[col].str.strip()
    
    # Debug print
    print(f"Total papers loaded: {len(papers_df)}")
    print(f"Papers with venues: {len(papers_df[papers_df['venue'] != ''])}")
    print(f"Papers with authors: {len(papers_df[papers_df['authors'].apply(len) > 0])}")
    print(f"Papers with abstracts: {len(papers_df[papers_df['abstract'] != ''])}")
    print(f"Papers with keywords: {len(papers_df[papers_df['keywords'].apply(len) > 0])}")
    
    # Print sample of keywords for debugging
    print("\nSample of keywords:")
    for idx, row in papers_df.head(5).iterrows():
        print(f"Paper {idx}: {row['keywords']}")
    
    conn.close()
    return papers_df

def display_paper_card(paper):
    """Display a single paper card."""
    with st.expander(f"{paper['title']} ({paper['year']})", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display venue
            venue = paper['venue'].strip()
            if venue:
                st.markdown(f"**Venue:** {venue}")
            
            # Display authors
            authors = paper['authors']
            if authors and len(authors) > 0:
                st.markdown("**Authors:** " + ", ".join(authors))
            
            # Display abstract
            abstract = paper['abstract'].strip()
            if abstract:
                st.markdown("**Abstract:**")
                st.markdown(abstract)
                
                # Display extracted keywords
                if 'extracted_keywords' in paper and paper['extracted_keywords']:
                    st.markdown("**Extracted Keywords:**")
                    st.markdown(", ".join(paper['extracted_keywords'][:5]))  # Show top 5 keywords
        
        with col2:
            # Display keywords
            keywords = paper['keywords']
            if keywords and len(keywords) > 0:
                st.markdown("**Keywords:**")
                for keyword in keywords:
                    if keyword.strip():
                        st.markdown(f"- {keyword}")
            
            # Display paper link
            if paper['url']:
                st.markdown(f"[View Paper]({paper['url']})")
        
        # Display collection date
        if paper['collected_at']:
            st.markdown(f"*Collected on: {paper['collected_at']}*")

def main():
    st.set_page_config(
        page_title="Academic Paper Metadata Explorer",
        page_icon="📚",
        layout="wide"
    )
    
    # Load data
    papers_df = load_data()
    
    # Title and description
    st.title("Academic Paper Metadata Explorer")
    st.markdown("Explore academic papers from the ACL Anthology with interactive filtering and search capabilities.")
    
    # Add tabs for different views
    tab1, tab2 = st.tabs(["Paper Explorer", "Trend Analysis"])
    
    with tab1:
        # Get unique values for filters
        years = sorted(papers_df['year'].unique(), reverse=True)
        all_keywords = set()
        for keywords in papers_df['keywords']:
            if isinstance(keywords, list) and keywords:  # Only process non-empty keyword lists
                all_keywords.update(keywords)
        keywords = sorted(all_keywords)
        
        # Statistics cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Papers", len(papers_df))
        with col2:
            all_authors = set()
            for authors in papers_df['authors']:
                if isinstance(authors, list) and authors:  # Only process non-empty author lists
                    all_authors.update(authors)
            st.metric("Unique Authors", len(all_authors))
        with col3:
            st.metric("Years Covered", len(years))
        with col4:
            st.metric("Unique Keywords", len(keywords))
        
        # Filters
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input("Search papers", "", key="search")
        
        with col2:
            year_filter = st.selectbox(
                "Filter by Year",
                ["All Years"] + [str(year) for year in years],
                key="year"
            )
        
        with col3:
            keyword_filter = st.selectbox(
                "Filter by Keyword",
                ["All Keywords"] + keywords,
                key="keyword"
            )
        
        # Apply filters
        filtered_df = papers_df.copy()
        
        if search_query:
            filtered_df = filtered_df[filtered_df['title'].str.lower().str.contains(search_query.lower())]
        
        if year_filter != "All Years":
            filtered_df = filtered_df[filtered_df['year'] == int(year_filter)]
        
        if keyword_filter != "All Keywords":
            filtered_df = filtered_df[filtered_df['keywords'].apply(lambda x: isinstance(x, list) and keyword_filter in x)]
        
        # Display papers with pagination
        st.markdown("---")
        st.markdown(f"### Showing {len(filtered_df)} papers")
        
        # Add pagination
        items_per_page = 10
        total_pages = (len(filtered_df) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1))
            start_idx = (page - 1) * items_per_page
            end_idx = min(start_idx + items_per_page, len(filtered_df))
            current_page_df = filtered_df.iloc[start_idx:end_idx]
        else:
            current_page_df = filtered_df
        
        # Display papers for current page
        for _, paper in current_page_df.iterrows():
            display_paper_card(paper)
    
    with tab2:
        st.markdown("### Keyword Trend Analysis")
        
        # Extract keywords and analyze trends
        yearly_keywords = analyze_trends(papers_df)
        
        if yearly_keywords:
            # Plot trends
            top_n = st.slider("Number of top keywords to display", 5, 20, 10)
            trend_fig = plot_trends(yearly_keywords, top_n)
            
            if trend_fig is not None:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.warning("No keyword trends available. This could be because there are no abstracts in the dataset.")
        else:
            st.warning("No keyword trends available. This could be because there are no abstracts in the dataset.")
        
        # TF-IDF Analysis
        st.markdown("### TF-IDF Analysis by Year")
        years = sorted(papers_df['year'].unique())
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        for year in years:
            year_papers = papers_df[papers_df['year'] == year]
            if len(year_papers) > 0:
                abstracts = year_papers['abstract'].fillna('')
                if len(abstracts) > 0 and any(abstracts.str.strip()):
                    try:
                        tfidf_matrix = vectorizer.fit_transform(abstracts)
                        feature_names = vectorizer.get_feature_names_out()
                        # Get top terms for this year
                        avg_tfidf = tfidf_matrix.mean(axis=0).A1
                        top_indices = avg_tfidf.argsort()[-10:][::-1]
                        top_terms = [feature_names[i] for i in top_indices]
                        st.markdown(f"#### {year}")
                        st.markdown(", ".join(top_terms))
                    except Exception as e:
                        st.warning(f"Could not analyze papers from {year}: {str(e)}")
                else:
                    st.warning(f"No abstracts available for papers from {year}")
            else:
                st.warning(f"No papers available for {year}")

if __name__ == "__main__":
    main() 