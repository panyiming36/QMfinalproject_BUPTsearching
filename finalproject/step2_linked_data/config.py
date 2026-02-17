# config.py
import os

class Config:
    """Configuration file - all system settings are centralized here"""
    
    # TTL file path - location of your data file (important!)
    # Using raw string (r'') to avoid escape character issues in Windows paths
    TTL_PATH = r"C:\Users\14036\Desktop\finalproject\unified_store\complete_store.ttl"
    
    # Server configuration
    HOST = 'localhost'        # Host address (use '0.0.0.0' for local network access)
    PORT = 8080             # Port number (8080 is common for development)
    DEBUG = True              # Debug mode (True for development, False for production)
    
    # Namespaces - used to simplify URIs in display
    NAMESPACES = {
        'schema': 'http://schema.org/',           # Schema.org vocabulary
        'dcterms': 'http://purl.org/dc/terms/',   # Dublin Core metadata terms
        'foaf': 'http://xmlns.com/foaf/0.1/',     # Friend of a Friend vocabulary
        'bupt': 'http://bupt.edu.cn/research/',    # Your custom namespace
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',  # RDF basics
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',       # RDF Schema
        'xsd': 'http://www.w3.org/2001/XMLSchema#'              # XML Schema data types
    }
    
    # Pagination settings - items per page
    ITEMS_PER_PAGE = 20