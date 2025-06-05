from neo4j import GraphDatabase

def test_connection():
    # Connection details
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "eparth25@"  # Updated password
    
    try:
        # Create driver
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' as message")
            print(result.single()["message"])
        
        # Close driver
        driver.close()
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 