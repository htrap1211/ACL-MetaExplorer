#!/usr/bin/env python3
"""
Script to generate HTML dashboard using XSLT transformation.
"""

import os
from pathlib import Path
import lxml.etree as ET

# Constants
DATA_DIR = Path(__file__).parent.parent.parent / "data"
XML_DIR = DATA_DIR / "xml"
XSL_PATH = Path(__file__).parent.parent.parent / "schemas" / "dashboard.xsl"
OUTPUT_DIR = DATA_DIR / "dashboard"

def ensure_directories():
    """Create necessary directories if they don't exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_dashboard():
    """Generate HTML dashboard using XSLT transformation."""
    # Load XML and XSLT
    xml_file = XML_DIR / "papers.xml"
    if not xml_file.exists():
        print("Error: papers.xml not found. Please run the conversion script first.")
        return
    
    # Parse XML and XSLT
    xml_doc = ET.parse(str(xml_file))
    xslt_doc = ET.parse(str(XSL_PATH))
    
    # Create transformer
    transform = ET.XSLT(xslt_doc)
    
    # Transform XML to HTML
    result = transform(xml_doc)
    
    # Save result
    output_file = OUTPUT_DIR / "index.html"
    result.write(str(output_file), pretty_print=True, encoding='utf-8')
    
    print(f"Dashboard generated successfully at: {output_file}")

def main():
    """Main function to orchestrate dashboard generation."""
    ensure_directories()
    generate_dashboard()

if __name__ == "__main__":
    main() 