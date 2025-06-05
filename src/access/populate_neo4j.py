import os
import pandas as pd
import sqlite3
from neo4j_operations import Neo4jConnection
from typing import List, Dict, Any
import re

def extract_citations_from_abstract(abstract: str) -> List[str]:
    """Extract citation references from abstract text."""
    citations = []
    if pd.isna(abstract) or not abstract:
        return citations
        
    # Look for patterns like "et al. (2020)" or "Smith et al. (2020)"
    citation_patterns = [
        r'([A-Z][a-z]+ et al\. \(\d{4}\))',  # Smith et al. (2020)
        r'([A-Z][a-z]+ and [A-Z][a-z]+ \(\d{4}\))',  # Smith and Jones (2020)
        r'([A-Z][a-z]+ \(\d{4}\))'  # Smith (2020)
    ]
    
    for pattern in citation_patterns:
        matches = re.finditer(pattern, abstract)
        citations.extend(match.group(1) for match in matches)
    
    return list(set(citations))  # Remove duplicates

def get_paper_id_from_citation(citation: str, papers_df: pd.DataFrame) -> str:
    """Get paper ID from citation by matching year and authors."""
    # Extract year from citation
    year_match = re.search(r'\((\d{4})\)', citation)
    if not year_match:
        return None
    year = int(year_match.group(1))
    
    # Extract authors
    authors = citation.split('(')[0].strip()
    
    # Find matching papers
    matching_papers = papers_df[
        (papers_df['year'] == year) & 
        (papers_df['title'].str.contains(authors.split()[0], case=False, na=False))
    ]
    
    if len(matching_papers) > 0:
        return matching_papers.iloc[0]['id']
    return None

def create_citations_dataframe(papers_df: pd.DataFrame) -> pd.DataFrame:
    """Create DataFrame of citation relationships."""
    citations_data = []
    
    for _, paper in papers_df.iterrows():
        if pd.notna(paper['abstract']):
            cited_refs = extract_citations_from_abstract(paper['abstract'])
            for cited_ref in cited_refs:
                cited_id = get_paper_id_from_citation(cited_ref, papers_df)
                if cited_id and cited_id != paper['id']:  # Don't self-cite
                    citations_data.append({
                        'citing_paper_id': paper['id'],
                        'cited_paper_id': cited_id
                    })
    
    return pd.DataFrame(citations_data)

def main():
    # Database paths
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DB_PATH = os.path.join(DATA_DIR, "academic_metadata.db")
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Load papers data
        papers_df = pd.read_sql_query("""
            SELECT id, title, year, venue, abstract, url
            FROM papers
        """, conn)
        
        if papers_df.empty:
            print("No papers found in the database")
            return
            
        print(f"Loaded {len(papers_df)} papers from database")
        
        # Create citations DataFrame
        citations_df = create_citations_dataframe(papers_df)
        
        if citations_df.empty:
            print("No citations found in the papers")
            return
            
        print(f"Found {len(citations_df)} citation relationships")
        
        # Connect to Neo4j
        neo4j_conn = Neo4jConnection()
        if not neo4j_conn.connect():
            print("Failed to connect to Neo4j database")
            return
        
        try:
            # Create paper nodes
            print("Creating paper nodes...")
            if neo4j_conn.create_paper_nodes(papers_df):
                print("Successfully created paper nodes")
            else:
                print("Failed to create paper nodes")
                return
            
            # Create citation relationships
            print("Creating citation relationships...")
            if neo4j_conn.create_citation_relationships(citations_df):
                print("Successfully created citation relationships")
            else:
                print("Failed to create citation relationships")
                return
            
            print("Neo4j database population completed successfully!")
        
        finally:
            neo4j_conn.close()
    
    finally:
        conn.close()

if __name__ == "__main__":
    main() 