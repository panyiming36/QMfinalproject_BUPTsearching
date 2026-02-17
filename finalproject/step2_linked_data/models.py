# models.py
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, FOAF
import os
from config import Config

class RDFDataModel:
    """
    RDF Data Model - responsible for loading and basic querying of RDF data
    """
    
    def __init__(self, ttl_path):
        """
        Initialize with path to TTL file
        
        Args:
            ttl_path (str): Full path to the TTL file
        """
        self.ttl_path = ttl_path
        self.graph = None
        # Fix: Define schema as the full URI string, not URIRef object
        self.schema = "http://schema.org/"
        self.loaded = False
        
    def load(self):
        """
        Load TTL file into memory
        
        Returns:
            Graph: Loaded RDF graph
        
        Raises:
            FileNotFoundError: If TTL file doesn't exist
            Exception: If parsing fails
        """
        print(f"Loading RDF data from: {self.ttl_path}")
        
        # Check if file exists
        if not os.path.exists(self.ttl_path):
            raise FileNotFoundError(f"TTL file not found: {self.ttl_path}")
        
        # Create new graph and load data
        self.graph = Graph()
        
        try:
            self.graph.parse(self.ttl_path, format="turtle")
            self.loaded = True
            print(f"✅ Successfully loaded! Total triples: {len(self.graph)}")
            return self.graph
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            raise
    
    def get_statistics(self):
        """
        Get statistics about the data
        
        Returns:
            dict: Statistics including paper count, author count, etc.
        """
        if not self.loaded:
            raise Exception("Data not loaded yet. Call load() first.")
        
        # Fix: Use URIRef to create proper URI objects for querying
        scholarly_article = URIRef(self.schema + "ScholarlyArticle")
        person = URIRef("http://xmlns.com/foaf/0.1/Person")
        organization = URIRef(self.schema + "Organization")
        periodical = URIRef(self.schema + "Periodical")
        defined_term = URIRef(self.schema + "DefinedTerm")
        
        # Count different entity types
        papers = list(self.graph.subjects(RDF.type, scholarly_article))
        authors = list(self.graph.subjects(RDF.type, person))
        orgs = list(self.graph.subjects(RDF.type, organization))
        journals = list(self.graph.subjects(RDF.type, periodical))
        keywords = list(self.graph.subjects(RDF.type, defined_term))
        
        stats = {
            'papers': len(papers),
            'authors': len(authors),
            'organizations': len(orgs),
            'journals': len(journals),
            'keywords': len(keywords),
            'triples': len(self.graph)
        }
        
        return stats
    
    def resource_exists(self, uri):
        """
        Check if a resource exists in the graph
        
        Args:
            uri (str): Resource URI to check
            
        Returns:
            bool: True if resource exists
        """
        if not self.loaded:
            raise Exception("Data not loaded yet. Call load() first.")
        
        return (URIRef(uri), None, None) in self.graph
    
    def get_resource_graph(self, uri):
        """
        Get all triples about a specific resource
        
        Args:
            uri (str): Resource URI
            
        Returns:
            Graph: Graph containing all triples with this resource as subject
        """
        if not self.loaded:
            raise Exception("Data not loaded yet. Call load() first.")
        
        result = Graph()
        uri_ref = URIRef(uri)
        
        for s, p, o in self.graph.triples((uri_ref, None, None)):
            result.add((s, p, o))
        
        return result
    
    def get_all_papers(self):
        """
        Get all paper URIs
        
        Returns:
            list: List of paper URIs
        """
        if not self.loaded:
            raise Exception("Data not loaded yet. Call load() first.")
        
        scholarly_article = URIRef(self.schema + "ScholarlyArticle")
        return list(self.graph.subjects(RDF.type, scholarly_article))
    
    def get_paper_title(self, paper_uri):
        """
        Get title of a paper
        
        Args:
            paper_uri (URIRef): Paper URI
            
        Returns:
            Literal: Paper title or None
        """
        name = URIRef(self.schema + "name")
        return self.graph.value(paper_uri, name)
    
    def get_paper_authors(self, paper_uri):
        """
        Get authors of a paper
        
        Args:
            paper_uri (URIRef): Paper URI
            
        Returns:
            list: List of author URIs
        """
        author = URIRef(self.schema + "author")
        return list(self.graph.objects(paper_uri, author))
    
    def get_paper_year(self, paper_uri):
        """
        Get publication year of a paper
        
        Args:
            paper_uri (URIRef): Paper URI
            
        Returns:
            Literal: Publication year or None
        """
        date_published = URIRef(self.schema + "datePublished")
        return self.graph.value(paper_uri, date_published)
    
    def get_author_name(self, author_uri):
        """
        Get name of an author
        
        Args:
            author_uri (URIRef): Author URI
            
        Returns:
            Literal: Author name or None
        """
        name = URIRef("http://xmlns.com/foaf/0.1/name")
        return self.graph.value(author_uri, name)
    
    def get_author_affiliation(self, author_uri):
        """
        Get affiliation (organization) of an author
        
        Args:
            author_uri (URIRef): Author URI
            
        Returns:
            URIRef: Organization URI or None
        """
        affiliation = URIRef(self.schema + "affiliation")
        return self.graph.value(author_uri, affiliation)
    
    def get_organization_name(self, org_uri):
        """
        Get name of an organization
        
        Args:
            org_uri (URIRef): Organization URI
            
        Returns:
            Literal: Organization name or None
        """
        name = URIRef(self.schema + "name")
        return self.graph.value(org_uri, name)
    
    def get_organization_members(self, org_uri):
        """
        Get members of an organization
        
        Args:
            org_uri (URIRef): Organization URI
            
        Returns:
            list: List of member (author) URIs
        """
        member = URIRef(self.schema + "member")
        return list(self.graph.objects(org_uri, member))
    
    def execute_query(self, query_string):
        """
        Execute a raw SPARQL query
        
        Args:
            query_string (str): SPARQL query string
            
        Returns:
            QueryResult: SPARQL query results
        """
        if not self.loaded:
            raise Exception("Data not loaded yet. Call load() first.")
        
        return self.graph.query(query_string)


# Test code - run this file directly to test
if __name__ == '__main__':
    print("Testing RDFDataModel...")
    
    # Use Config.TTL_PATH from config.py
    model = RDFDataModel(Config.TTL_PATH)
    
    try:
        # Load data
        model.load()
        
        # Get statistics
        stats = model.get_statistics()
        print("\nStatistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test getting first paper
        papers = model.get_all_papers()
        if papers:
            first_paper = papers[0]
            print(f"\nFirst paper URI: {first_paper}")
            
            title = model.get_paper_title(first_paper)
            print(f"Title: {title}")
            
            year = model.get_paper_year(first_paper)
            print(f"Year: {year}")
            
            authors = model.get_paper_authors(first_paper)
            print(f"Authors ({len(authors)}):")
            for author in authors[:3]:  # Show first 3 authors
                name = model.get_author_name(author)
                print(f"  - {name} ({author})")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")