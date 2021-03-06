Bachelor's thesis - Learning based on user interaction
The main goal of this project is to design and implement a Knowledge-Based System capable of learning through continuous interaction with the user. The central component of the system is a Knowledge Graph that manages system knowledge at all times. The Knowledge Graph is initialized with the analysis of the documents in the domain, and then the system learns new concepts and relationships through interaction with the user, expanding the representation with new experiences.

Files:
classifier.cc - NLP Processing
knowledge.py - Graph Driver
app.js - Visualization Backend

Requirements:
neo4j desktop or cli
nodejs
python3
gcc

python3 packages:
neo4j

c++ libraries:
pugixml.hpp
rapper (only for c++ prototype)

nodejs packages:
expressjs
express-handlebars
handlebars
eol
jquery
body-parser

neo4j plugins:
APOC
Neosemnatics
Graph Data Science Library

Compiling and set up:
1. Change path inside classifier.cc (line 408) for your FreeLing analyze location
2. Compile with the included makefile

Classifier first initialization:
1. Create a Neo4j database and start it up
2. Execute the following cypher commands on the database (replace paths with the correct ones)

CALL n10s.graphconfig.init();
CREATE CONSTRAINT n10s_unique_uri ON (r:Resource) ASSERT r.uri IS UNIQUE;
CALL n10s.rdf.import.fetch("file:///Users/arnau/Desktop/classifier/topics.ttl","Turtle");
CALL n10s.rdf.import.fetch("file:///Users/arnau/Desktop/classifier/cso.ttl","Turtle");

3. Execute "python3 knowledge.py 8" to initialize the reasoning module values (takes a little time)

Classifier normal startup:
1. Open Neo4j and start the database
2. Execute "node app.js"
3. Open localhost:8080
