from neo4j import GraphDatabase
import os
import pandas as pd
from typing import List, Dict, Any

class Neo4jConnection:
    def __init__(self):
        # Neo4j connection details for local desktop installation
        self.uri = "bolt://localhost:7687"
        self.user = "neo4j"
        self.password = "eparth25@"  # Updated password
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test the connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("Successfully connected to Neo4j")
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            return False

    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()

    def create_paper_nodes(self, papers_df: pd.DataFrame) -> bool:
        """Create paper nodes in Neo4j from DataFrame."""
        if not self.driver:
            return False

        try:
            with self.driver.session() as session:
                # Create paper nodes
                for _, paper in papers_df.iterrows():
                    session.run("""
                        MERGE (p:Paper {id: $id})
                        SET p.title = $title,
                            p.year = $year,
                            p.venue = $venue,
                            p.abstract = $abstract,
                            p.url = $url
                    """, {
                        'id': paper['id'],
                        'title': paper['title'],
                        'year': paper['year'],
                        'venue': paper['venue'],
                        'abstract': paper['abstract'],
                        'url': paper['url']
                    })
                return True
        except Exception as e:
            print(f"Error creating paper nodes: {str(e)}")
            return False

    def create_citation_relationships(self, citations_df: pd.DataFrame) -> bool:
        """Create citation relationships between papers."""
        if not self.driver:
            return False

        try:
            with self.driver.session() as session:
                for _, citation in citations_df.iterrows():
                    session.run("""
                        MATCH (citing:Paper {id: $citing_id})
                        MATCH (cited:Paper {id: $cited_id})
                        MERGE (citing)-[r:CITES]->(cited)
                    """, {
                        'citing_id': citation['citing_paper_id'],
                        'cited_id': citation['cited_paper_id']
                    })
                return True
        except Exception as e:
            print(f"Error creating citation relationships: {str(e)}")
            return False

    def get_most_cited_papers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most cited papers."""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)<-[c:CITES]-()
                    RETURN p.id as id,
                           p.title as title,
                           p.year as year,
                           count(c) as citation_count
                    ORDER BY citation_count DESC
                    LIMIT $limit
                """, {'limit': limit})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting most cited papers: {str(e)}")
            return []

    def get_citation_network(self, paper_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get citation network for a specific paper."""
        if not self.driver:
            return {}

        try:
            with self.driver.session() as session:
                # First get the source paper
                source_result = session.run("""
                    MATCH (p:Paper {id: $paper_id})
                    RETURN p.id as source_id, p.title as source_title
                """, {'paper_id': paper_id})
                source = source_result.single()
                if not source:
                    return {}
                
                # Then get the cited papers
                cited_result = session.run("""
                    MATCH (p:Paper {id: $paper_id})-[:CITES]->(cited:Paper)
                    RETURN collect(distinct cited.id) as cited_ids,
                           collect(distinct cited.title) as cited_titles
                """, {'paper_id': paper_id})
                cited = cited_result.single()
                
                if not cited:
                    return {
                        'source_id': source['source_id'],
                        'source_title': source['source_title'],
                        'cited_ids': [],
                        'cited_titles': []
                    }
                
                return {
                    'source_id': source['source_id'],
                    'source_title': source['source_title'],
                    'cited_ids': cited['cited_ids'],
                    'cited_titles': cited['cited_titles']
                }
        except Exception as e:
            print(f"Error getting citation network: {str(e)}")
            return {}

    def get_pagerank_scores(self) -> List[Dict[str, Any]]:
        """Calculate influence scores for papers using citation counts."""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)
                    OPTIONAL MATCH (p)<-[c:CITES]-()
                    WITH p, count(c) as citation_count
                    RETURN p.id as id,
                           p.title as title,
                           p.year as year,
                           citation_count as influence_score
                    ORDER BY citation_count DESC
                    LIMIT 10
                """)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error calculating influence scores: {str(e)}")
            return [] 