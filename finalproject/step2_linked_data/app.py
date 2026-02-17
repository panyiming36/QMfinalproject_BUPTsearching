# app.py
from flask import Flask, render_template, request, Response, jsonify
from rdflib import URIRef
from config import Config
from models import RDFDataModel
from queries import SPARQLQueries
import os

# ==================== 1. Create Flask Application ====================
app = Flask(__name__)
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False  # Support Chinese characters in JSON

# ==================== 2. Load Data ====================
print(f"Loading data from: {Config.TTL_PATH}")
model = RDFDataModel(Config.TTL_PATH)
model.load()
queries = SPARQLQueries(model.graph)
stats = model.get_statistics()
print(f"✅ Loaded: {stats['papers']} papers, {stats['authors']} authors")

# ==================== 3. Content Negotiation Functions ====================
def get_preferred_format():
    """
    Determine which format to return
    Priority: 1. URL parameter _format  2. HTTP Accept header  3. Default HTML
    """
    # Check URL parameter (e.g., ?_format=ttl or ?_format=json)
    format_param = request.args.get('_format')
    if format_param == 'ttl':
        return 'turtle'
    elif format_param == 'json':
        return 'json-ld'
    
    # Check HTTP Accept header (sent automatically by browsers)
    accept = request.headers.get('Accept', '')
    if 'application/ld+json' in accept or 'application/json' in accept:
        return 'json-ld'      # Machine wants JSON
    elif 'text/turtle' in accept:
        return 'turtle'       # Machine wants Turtle
    else:
        return 'html'         # Default to human-readable HTML

def serialize_graph(graph, format_type):
    """Convert RDF graph to specified format"""
    if format_type == 'turtle':
        return graph.serialize(format='turtle')
    elif format_type == 'json-ld':
        return graph.serialize(format='json-ld')
    return None

# ==================== 4. Routes ====================

@app.route('/')
def home():
    """Home page - display system statistics"""
    fmt = get_preferred_format()
    
    # If not HTML, return RDF data
    if fmt != 'html':
        return Response(serialize_graph(model.graph, fmt), 
                       mimetype='text/turtle' if fmt=='turtle' else 'application/ld+json')
    
    # Return HTML page
    return render_template('home.html', stats=stats)

@app.route('/research/<entity_type>/<entity_id>')
def get_resource(entity_type, entity_id):
    """
    Get individual resource (Linked Data core)
    Example: /research/paper/0001 or /research/author/1234
    """
    # Construct URI based on type
    if entity_type == 'paper':
        uri = f"http://bupt.edu.cn/research/paper_{entity_id}"
    else:
        uri = f"http://bupt.edu.cn/research/{entity_type}/{entity_id}"
    
    # Check if resource exists
    if not model.resource_exists(uri):
        return "Resource not found", 404
    
    fmt = get_preferred_format()
    
    # If RDF format requested, return serialized data
    if fmt != 'html':
        result_graph = model.get_resource_graph(uri)
        return Response(serialize_graph(result_graph, fmt),
                       mimetype='text/turtle' if fmt=='turtle' else 'application/ld+json')
    
    # For HTML, organize properties for display
    properties = []
    for s, p, o in model.graph.triples((URIRef(uri), None, None)):
        # Simplify predicate display (convert long URIs to prefix form)
        pred = str(p)
        for prefix, ns in Config.NAMESPACES.items():
            if pred.startswith(ns):
                pred = f"{prefix}:{pred[len(ns):]}"
                break
        properties.append({'predicate': pred, 'object': str(o)})
    
    return render_template('resource.html', 
                         title=f"{entity_type}: {entity_id}",
                         uri=uri, 
                         properties=properties)

@app.route('/papers')
def papers_list():
    """Papers list page (with pagination)"""
    # Get page number, default to 1
    page = int(request.args.get('page', 1))
    per_page = Config.ITEMS_PER_PAGE
    offset = (page - 1) * per_page
    
    # Query papers for this page
    papers = queries.get_papers_list(limit=per_page, offset=offset)
    
    # Calculate total pages
    total = stats['papers']
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('papers.html', 
                         papers=papers,
                         page=page,
                         total_pages=total_pages)

@app.route('/authors')
def authors_list():
    """Authors list page (with pagination)"""
    page = int(request.args.get('page', 1))
    per_page = Config.ITEMS_PER_PAGE
    offset = (page - 1) * per_page
    
    authors = queries.get_authors_list(limit=per_page, offset=offset)
    
    total = stats['authors']
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('authors.html', 
                         authors=authors,
                         page=page,
                         total_pages=total_pages)

@app.route('/organizations')
def organizations_list():
    """Organizations list page (with pagination)"""
    page = int(request.args.get('page', 1))
    per_page = Config.ITEMS_PER_PAGE
    offset = (page - 1) * per_page
    
    orgs = queries.get_organizations_list(limit=per_page, offset=offset)
    
    total = stats['organizations']
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('organizations.html', 
                         organizations=orgs,
                         page=page,
                         total_pages=total_pages)

@app.route('/search')
def search():
    """Search page - search papers by keyword"""
    keyword = request.args.get('q', '').strip()
    fmt = get_preferred_format()
    
    # If no keyword, show empty search page
    if not keyword:
        return render_template('search.html', query='', results=[], total=0)
    
    # Execute search
    results = []
    for row in queries.search_papers(keyword):
        results.append({
            'uri': str(row.paper),
            'title': str(row.title),
            'author': str(row.authorName) if row.authorName else 'Unknown',
            'year': str(row.year) if row.year else 'Unknown'
        })
    
    # If JSON format requested, return JSON directly
    if fmt == 'json-ld':
        return jsonify(results)
    
    # Otherwise return HTML page
    return render_template('search.html', 
                         query=keyword,
                         results=results,
                         total=len(results))

@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """SPARQL query endpoint - advanced users can write SPARQL directly"""
    if request.method == 'GET':
        query = request.args.get('query', '')
    else:
        query = request.form.get('query', '')
    
    # If no query, show input form
    if not query:
        return '''
        <html>
        <head>
            <title>SPARQL Endpoint</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                textarea { width: 100%; height: 200px; font-family: monospace; }
                input[type=submit] { padding: 10px 20px; background: #0066cc; color: white; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <h1>SPARQL Query Endpoint</h1>
            <form method="post">
                <textarea name="query" placeholder="Enter your SPARQL query here..."></textarea><br>
                <input type="submit" value="Execute Query">
            </form>
        </body>
        </html>
        '''
    
    # Execute query
    try:
        results = model.execute_query(query)
        
        # Display results as HTML table
        html = '<html><head><title>SPARQL Results</title>'
        html += '<style>table { border-collapse: collapse; } td, th { border: 1px solid #ddd; padding: 8px; }</style>'
        html += '</head><body>'
        html += '<h2>Query Results</h2>'
        html += '<table><tr>'
        
        if results.vars:
            for var in results.vars:
                html += f'<th>{var}</th>'
            html += '</tr>'
            
            for row in results:
                html += '<tr>'
                for var in results.vars:
                    val = row[var]
                    html += f'<td>{val}</td>'
                html += '</tr>'
            html += '</table>'
        else:
            html += '<p>No results</p>'
        
        html += '<p><a href="/sparql">New Query</a></p>'
        html += '</body></html>'
        return html
        
    except Exception as e:
        return f'<p>Error: {e}</p>', 400

# ==================== 5. Start Server ====================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 BUPT Linked Data System Starting...")
    print("="*60)
    print(f"\n📊 Data Statistics:")
    print(f"   - Papers: {stats['papers']}")
    print(f"   - Authors: {stats['authors']}")
    print(f"   - Organizations: {stats['organizations']}")
    print(f"   - Triples: {stats['triples']}")
    
    print(f"\n🌐 Available URLs:")
    print(f"   http://{Config.HOST}:{Config.PORT}/              # Home page")
    print(f"   http://{Config.HOST}:{Config.PORT}/papers        # Papers list")
    print(f"   http://{Config.HOST}:{Config.PORT}/authors       # Authors list")
    print(f"   http://{Config.HOST}:{Config.PORT}/organizations # Organizations list")
    print(f"   http://{Config.HOST}:{Config.PORT}/search        # Search")
    print(f"   http://{Config.HOST}:{Config.PORT}/sparql        # SPARQL endpoint")
    
    print(f"\n🔍 Example Resource:")
    if stats['papers'] > 0:
        print(f"   http://{Config.HOST}:{Config.PORT}/research/paper/0001")
    
    print(f"\n📡 Content Negotiation Test:")
    print(f"   curl http://{Config.HOST}:{Config.PORT}/research/paper/0001?_format=ttl")
    print(f"   curl -H 'Accept: application/ld+json' http://{Config.HOST}:{Config.PORT}/")
    
    print("\n" + "="*60)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)