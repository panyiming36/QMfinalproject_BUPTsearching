from flask import Flask, request, jsonify,render_template
import rdflib
from rdflib import Graph
import urllib.parse
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

g = Graph()
g.parse("unified_store\complete_store.ttl", format="turtle")

@app.route('/')
def home():
    
    return render_template('test.html')

@app.route('/search')
def search():
    keyword = request.args.get('q', '').strip()
    
    if not keyword:
        return jsonify({"error": "需要搜索关键词"})
    
    query = f"""
    SELECT DISTINCT ?resource ?label ?type WHERE {{
        {{
            ?resource <http://schema.org/name> ?label .
            FILTER(CONTAINS(LCASE(?label), LCASE("{keyword}")))
            BIND("organization" AS ?type)
        }}
        UNION
        {{
            ?resource <http://xmlns.com/foaf/0.1/name> ?label .
            FILTER(CONTAINS(LCASE(?label), LCASE("{keyword}")))
            BIND("author" AS ?type)
        }}
        UNION
        {{
            ?resource <http://schema.org/name> ?label .
            ?resource a <http://schema.org/ScholarlyArticle> .
            FILTER(CONTAINS(LCASE(?label), LCASE("{keyword}")))
            BIND("paper" AS ?type)
        }}
        UNION
        {{
            ?resource <http://purl.org/dc/terms/title> ?label .
            FILTER(CONTAINS(LCASE(?label), LCASE("{keyword}")))
            BIND("paper" AS ?type)
        }}
    }}
    LIMIT 50
    """
    
    results = []
    for row in g.query(query):
        results.append({
            "uri": str(row.resource),
            "label": str(row.label),
            "type": str(row.type)
        })
    
    return jsonify({
        "query": keyword,
        "count": len(results),
        "results": results
    })

@app.route('/resource')
def get_resource():
    uri = request.args.get('uri', '').strip()
    
    if not uri:
        return jsonify({"error": "需要资源URI"})
    
    decoded_uri = urllib.parse.unquote(uri)
    
    query = f"""
    SELECT ?p ?o WHERE {{
        <{decoded_uri}> ?p ?o .
    }}
    """
    
    properties = []
    for row in g.query(query):
        properties.append({
            "property": str(row.p),
            "value": str(row.o),
            "is_uri": isinstance(row.o, rdflib.URIRef)
        })
    
    type_query = f"""
    SELECT ?type WHERE {{
        <{decoded_uri}> a ?type .
    }}
    """
    
    types = []
    for row in g.query(type_query):
        types.append(str(row.type))
    
    return jsonify({
        "uri": decoded_uri,
        "types": types,
        "properties": properties,
        "property_count": len(properties)
    })

@app.route('/stats')
def get_stats():
    queries = {
        "papers": """
        SELECT (COUNT(DISTINCT ?paper) as ?count) WHERE {
            ?paper a <http://schema.org/ScholarlyArticle> .
        }
        """,
        "authors": """
        SELECT (COUNT(DISTINCT ?author) as ?count) WHERE {
            ?author a <http://xmlns.com/foaf/0.1/Person> .
        }
        """,
        "organizations": """
        SELECT (COUNT(DISTINCT ?org) as ?count) WHERE {
            ?org a <http://schema.org/Organization> .
        }
        """
    }
    
    stats = {}
    for key, query_str in queries.items():
        result = list(g.query(query_str))
        if result:
            stats[key] = int(result[0][0])
    
    stats["total_triples"] = len(g)
    
    return jsonify(stats)

@app.route('/sparql', methods=['POST'])
def sparql_query():
    query = request.form.get('query', '')
    
    if not query:
        return jsonify({"error": "需要SPARQL查询语句"})
    
    try:
        results = []
        for row in g.query(query):
            row_dict = {}
            for i, value in enumerate(row):
                if value:
                    row_dict[f"var{i}"] = str(value)
            results.append(row_dict)
        
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("数据加载完成，共", len(g), "条三元组")
    print("API已启动: http://localhost:5000")
    app.run(debug=True, port=5000)