BUPT Research Data Linked Data System
bupt.xls - Original research data in Excel format

step1_convert_toRDF/step1.py - Python script that converts Excel data to RDF triples

output/complete_bupt_research.ttl - Complete RDF data file in Turtle format

output/conversion_report.txt - Conversion statistics report (paper count, triple count, etc.)

unified_store/complete_store.ttl - Clean RDF data file used by Sprint 2

step2_linked_data/config.py - Configuration file (TTL path, server port, namespaces)

step2_linked_data/models.py - Data model that loads TTL file into memory and provides basic query methods

step2_linked_data/queries.py - SPARQL query module (search, lists, pagination)

step2_linked_data/app.py - Main Flask application (server, routes, content negotiation)

step2_linked_data/templates/base.html - Base HTML template (navigation bar, footer)

step2_linked_data/templates/home.html - Home page template (displays statistics)

step2_linked_data/templates/papers.html - Papers list page template with pagination

step2_linked_data/templates/authors.html - Authors list page template

step2_linked_data/templates/organizations.html - Organizations list page template

step2_linked_data/templates/resource.html - Individual resource detail page template

step2_linked_data/templates/search.html - Search page template

README.md - Project documentation
