import os
from lxml import etree

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
XML_DIR = os.path.join(DATA_DIR, "xml")
SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")
OUTPUT_DIR = os.path.join(DATA_DIR, "dashboard")

def ensure_dirs():
    """Ensure all required directories exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_dashboard():
    """Generate HTML dashboard using XSLT transformation."""
    # Load XML data
    xml_file = os.path.join(XML_DIR, "papers.xml")
    if not os.path.exists(xml_file):
        print(f"Error: XML file not found at {xml_file}")
        return
    
    # Load XSLT stylesheet
    xslt_file = os.path.join(SCHEMAS_DIR, "dashboard.xsl")
    if not os.path.exists(xslt_file):
        print(f"Error: XSLT file not found at {xslt_file}")
        return
    
    try:
        # Parse XML and XSLT
        xml_doc = etree.parse(xml_file)
        xslt_doc = etree.parse(xslt_file)
        
        # Create transformer
        transform = etree.XSLT(xslt_doc)
        
        # Transform XML to HTML
        result = transform(xml_doc)
        
        # Save HTML output
        output_file = os.path.join(OUTPUT_DIR, "index.html")
        with open(output_file, 'wb') as f:
            f.write(etree.tostring(result, pretty_print=True, encoding='utf-8'))
        
        print(f"Dashboard generated successfully at {output_file}")
        
    except Exception as e:
        print(f"Error generating dashboard: {str(e)}")

def main():
    """Main function."""
    ensure_dirs()
    generate_dashboard()

if __name__ == "__main__":
    main() 