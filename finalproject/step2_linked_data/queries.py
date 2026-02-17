# queries.py
class SPARQLQueries:
    """
    SPARQL Queries - Centralized management of all query statements
    Purpose: Provide data for web pages, encapsulate complex SPARQL syntax
    Data source: Graph loaded into memory by models.py
    """
    
    def __init__(self, graph):
        """
        Initialize query module
        
        Args:
            graph: RDF graph object from models.py (data in memory)
        """
        self.graph = graph
    
    def search_papers(self, keyword):
        """
        Search papers by keyword (title or author)
        
        Purpose: Used by search page
        Input: User's keyword, e.g., "artificial intelligence"
        Output: List of matching papers (title, author, year)
        
        SPARQL explanation:
        - CONTAINS: Fuzzy matching, returns if contains keyword
        - OPTIONAL: Some papers may not have author info, still display
        - LIMIT 50: Return at most 50 results to avoid too much data
        """
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT DISTINCT ?paper ?title ?authorName ?year WHERE {{
            ?paper a schema:ScholarlyArticle .
            ?paper schema:name ?title .
            OPTIONAL {{
                ?paper schema:author ?author .
                ?author foaf:name ?authorName .
            }}
            OPTIONAL {{ ?paper schema:datePublished ?year }}
            FILTER(CONTAINS(?title, "{keyword}") || 
                   CONTAINS(?authorName, "{keyword}"))
        }}
        LIMIT 50
        """
        return self.graph.query(query)
    
    def get_papers_list(self, limit=20, offset=0):
        """
        Get paginated list of papers
        
        Purpose: Used by papers list page
        Input: limit=items per page, offset=number to skip (for pagination)
        Output: List of papers (URI, title, author, year)
        
        Pagination principle:
        - Page 1: limit=20, offset=0  (items 1-20)
        - Page 2: limit=20, offset=20 (items 21-40)
        - Page 3: limit=20, offset=40 (items 41-60)
        """
        query = """
        PREFIX schema: <http://schema.org/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT ?paper ?title ?authorName ?year WHERE {
            ?paper a schema:ScholarlyArticle .
            ?paper schema:name ?title .
            OPTIONAL {
                ?paper schema:author ?author .
                ?author foaf:name ?authorName .
            }
            OPTIONAL { ?paper schema:datePublished ?year }
        }
        """
        
        # Execute query and format results
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.paper),           # Paper URI for linking
                'title': str(row.title),          # Paper title
                'author': str(row.authorName) if row.authorName else 'Unknown',  # Author (may be multiple, take first)
                'year': str(row.year) if row.year else 'Unknown'  # Publication year
            })
        
        # Manual pagination (RDFlib's SPARQL doesn't support LIMIT and OFFSET well)
        return results[offset:offset+limit]
    
    def get_authors_list(self, limit=20, offset=0):
        """
        Get paginated list of authors
        
        Purpose: Used by authors list page
        Output: List of authors (URI, name)
        """
        query = """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT ?author ?name WHERE {
            ?author a foaf:Person .
            ?author foaf:name ?name .
        }
        """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.author),  # Author URI
                'name': str(row.name)     # Author name
            })
        
        return results[offset:offset+limit]
    
    def get_organizations_list(self, limit=20, offset=0):
        """
        Get paginated list of organizations
        
        Purpose: Used by organizations list page
        Output: List of organizations (URI, name)
        """
        query = """
        PREFIX schema: <http://schema.org/>
        
        SELECT ?org ?name WHERE {
            ?org a schema:Organization .
            ?org schema:name ?name .
        }
        """
        
        results = []
        for row in self.graph.query(query):
            results.append({
                'uri': str(row.org),   # Organization URI
                'name': str(row.name)   # Organization name
            })
        
        return results[offset:offset+limit]
    
    def get_papers_by_author(self, author_uri):
        """
        Get all papers by a specific author
        
        Purpose: Used by author detail page
        Input: Author URI (e.g., http://bupt.edu.cn/research/author/1234)
        Output: All papers by this author
        """
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        
        SELECT ?paper ?title ?year WHERE {{
            ?paper dcterms:creator <{author_uri}> .
            ?paper schema:name ?title .
            OPTIONAL {{ ?paper schema:datePublished ?year }}
        }}
        """
        return self.graph.query(query)
    
    def get_organization_members(self, org_uri):
        """
        Get all members of an organization
        
        Purpose: Used by organization detail page
        Input: Organization URI
        Output: All authors in this organization
        """
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT ?author ?name WHERE {{
            <{org_uri}> schema:member ?author .
            ?author foaf:name ?name .
        }}
        """
        return self.graph.query(query)
    
    def get_coauthors(self, author_uri):
        """
        Get all co-authors of a specific author
        
        Purpose: Analyze collaboration relationships
        Input: Author URI
        Output: Other authors who have collaborated with this author
        """
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        
        SELECT DISTINCT ?coauthor ?coauthorName WHERE {{
            ?paper dcterms:creator <{author_uri}> .
            ?paper dcterms:creator ?coauthor .
            ?coauthor foaf:name ?coauthorName .
            FILTER(?coauthor != <{author_uri}>)
        }}
        """
        return self.graph.query(query)
    
    def get_papers_by_year(self, year):
        """
        Filter papers by publication year
        
        Purpose: Year-based filtering
        Input: Year (e.g., 2025)
        Output: All papers from that year
        """
        query = f"""
        PREFIX schema: <http://schema.org/>
        
        SELECT ?paper ?title WHERE {{
            ?paper a schema:ScholarlyArticle .
            ?paper schema:name ?title .
            ?paper schema:datePublished {year} .
        }}
        """
        return self.graph.query(query)


# Test code - Run this file directly to test query functionality
if __name__ == '__main__':
    from config import Config
    from models import RDFDataModel
    
    print("Testing SPARQLQueries class...")
    
    # 1. Load data (reuse models.py)
    model = RDFDataModel(Config.TTL_PATH)
    model.load()
    
    # 2. Create query object
    queries = SPARQLQueries(model.graph)
    
    # 3. Test search function
    print("\n🔍 Searching for papers containing 'artificial intelligence':")
    results = queries.search_papers("artificial intelligence")
    for row in results:
        print(f"  - {row.title} (Author: {row.authorName})")
    
    # 4. Test papers list (pagination)
    print("\n📄 Papers list (first 5):")
    papers = queries.get_papers_list(limit=5, offset=0)
    for p in papers:
        print(f"  - {p['title']} - {p['author']} ({p['year']})")
    
    # 5. Test authors list
    print("\n👤 Authors list (first 5):")
    authors = queries.get_authors_list(limit=5, offset=0)
    for a in authors:
        print(f"  - {a['name']}")