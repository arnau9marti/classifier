import Levenshtein
from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable
import sys
from Levenshtein import distance as levenshtein_distance
import pprint, pickle

topic_list = []
buss_categories = []
tech_categories = []
buss_categories_sug = []
tech_categories_sug = []
found_cat = []

centrality = dict()
community = dict()
similarity = dict()

suggestions = dict()

class App:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # TOPIC CREATION
    def insert_topic(self, topic_name, super_topic_name):
        with self.driver.session() as session:
            result = session.write_transaction(
                self._insert_and_return_topic, topic_name, super_topic_name)
            # for row in result:
            #     print("Created super topic relationship between: {t} and {st}".format(t=row['t'], st=row['st']))

    @staticmethod
    def _insert_and_return_topic(tx, topic_name, super_topic_name):
        query = (
            "MATCH (st:ns0__Topic) WHERE st.rdfs__label = $super_topic_name "
            "MERGE (t:ns0__Topic { rdfs__label: $topic_name }) "
            "CREATE (st)-[:ns0__superTopicOf]->(t) "
            "RETURN t, st"
        )
        result = tx.run(query, topic_name=topic_name, super_topic_name=super_topic_name)
        try:
            return [{"t": row["t"]["rdfs__label"], "st": row["st"]["rdfs__label"]}
                    for row in result]
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise
    
    # TOPIC SEARCH
    def find_topic(self, topic_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_topic_sim, topic_name)
            for row in result:
                topic_list.append(row)
                # print("Found topic: {row}".format(row=row))

    @staticmethod
    def _find_and_return_topic_exact(tx, topic_name):
        query = (
            "MATCH (t:ns0__Topic) "
            "WHERE t.rdfs__label = $topic_name "
            "RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]

    @staticmethod
    def _find_and_return_topic_sim(tx, topic_name):
        query = (
            "MATCH (t:ns0__Topic) "
            "WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $topic_name) > 0.92 "
            "RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]
    
    # FRIST SEMANTIC REASONING
    def find_relationship(self, topic_name):
        with self.driver.session() as session:
            #session.read_transaction(self._inverse_super)
            result = session.read_transaction(self._find_and_return_relationships, topic_name)
            #result1 = session.read_transaction(self._find_and_return_categories, topic_name1)
            #result2 = session.read_transaction(self._find_and_return_categories, topic_name2)
            #session.read_transaction(self._inverse_super)
            #result = set.intersection(set(result1), set(result2))

            rels = []
            for nodes in result:
                rels.append(nodes)
                #print("Found relationships: {nodes}".format(nodes=nodes))
            return rels

    @staticmethod
    def _find_and_return_relationships(tx, topic_name):
        query = (
            "MATCH (c:ns0__Topic {rdfs__label: $topic_name}) "
            "CALL n10s.inference.nodesInCategory(c, { "
            "  inCatRel: 'ns0__preferentialEquivalent', "
            #"  inCatRel: 'ns0__relatedEquivalent', "
            "  subCatRel: 'ns0__superTopicOf' "
            "}) "
            "YIELD node "
            "WITH node.rdfs__label as nodes "
            "RETURN nodes"
        )
        # intersect = (
        #     "RETURN apoc.coll.intersection($result1, $result2)" 
        # )
        result = tx.run(query, topic_name=topic_name)
        return [row["nodes"] for row in result]

    def inverse_super(self):
        with self.driver.session() as session:
            session.read_transaction(self._inverse_super)

    @staticmethod
    def _inverse_super(tx):
        inverse = (
            "MATCH (t1: ns0__Topic)-[rel:ns0__superTopicOf]->(t2: ns0__Topic) "
            "CALL apoc.refactor.invert(rel) yield input, output "
            "RETURN input, output"
        )
        tx.run(inverse)

    # SECOND SEMANTIC REASONING
    def find_related_term(self, first_term, second_term):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_related_term, first_term, second_term)
            return result

    @staticmethod
    def _find_and_return_related_term(tx, broad_term, concrete_term):
        query = (
            "MATCH path = (c:ns0__Topic)-[:ns0__relatedEquivalent]->(category)-[:ns0__superTopicOf*]->(:ns0__Topic {rdfs__label: $broad_term}) "
            "WHERE c.rdfs__label contains $concrete_term "
            "RETURN c.rdfs__label as name"
        )
        result = tx.run(query, broad_term=broad_term, concrete_term=concrete_term)
        return [row["name"] for row in result]

    # FRIST SIMILARITY REASONING
    def find_suggestion_similarity(self, resource_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_similar_resources, resource_name)
            
            similars = []
            for name in result:
                similars.append(name)
            #     print("Found similar: {name}".format(name=name))

            return similars

    @staticmethod
    def _find_and_return_similar_resources(tx, resource_name):
        query = (
            "MATCH (c:AI_RESOURCE {rdfs__label: $resource_name}), "
                "path = (c)<-[:HAS_TOPIC]-(topic), "
                "otherPath = (topic)-[:HAS_TOPIC]->(res) "
            "MATCH (res)<-[:HAS_TOPIC]-(newtopic) "
            "WHERE newtopic <> topic "
            "RETURN newtopic.rdfs__label AS name "
        )
        result = tx.run(query, resource_name=resource_name)
        return [row["name"] for row in result]

    # SECOND SIMILARITY REASONING WIP
    def find_parent_similarity(self, topic_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_outcat_path, topic_name)
        
            similars = []
            for name in result:
                similars.append(name)
            #     print("Found similar: {name}".format(name=name))

            return similars

    @staticmethod
    def _find_and_return_incat_path(tx, topic_name):
        query = (
            "MATCH (c:ns0__Topic {rdfs__label: $topic_name}), "
            "path = (c)-[:HAS_TOPIC]->(res)-[:HAS_CATEGORY]->(cat), "
            "otherPath = (other)-[:HAS_CATEGORY]->(cat) "
            "return path, otherPath"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]

    @staticmethod
    def _find_and_return_outcat_path(tx, topic_name):
        query = (
            "MATCH (c:ns0__Topic {rdfs__label: $topic_name}), "
                "entityPath = (c)-[:HAS_TOPIC]->(res)-[:HAS_CATEGORY]->(cat), "
                "path = (cat)-[:skos__topConceptOf]->(parent)<-[:skos__topConceptOf]-(otherCat), "
                "otherEntityPath = (otherCat)<-[:HAS_CATEGORY]-(otherWiki)<-[:HAS_TOPIC]-(other) "
            "RETURN other.rdfs__label as name, "
                "[(other)-[:HAS_TOPIC]->()-[:HAS_CATEGORY]->(entity) | entity.rdfs__label] AS otherCategories, "
                "collect([node in nodes(path) | node.rdfs__label]) AS pathToOther "
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]

    # CATEGORY MATCHING
    def match_categories(self):
        with self.driver.session() as session:
            aux_topic_list = topic_list.copy()

            for topic_name in topic_list:
                result = session.read_transaction(self._find_and_return_same_as, topic_name)
                for row in result:
                    aux_topic_list.append(row)
                
                result = session.read_transaction(self._find_and_return_equivalent, topic_name)
                for row in result:
                    aux_topic_list.append(row)
                
                result = session.read_transaction(self._find_and_return_parent, topic_name)
                for row in result:
                    aux_topic_list.append(row)

            for topic_name in aux_topic_list:
                result = session.read_transaction(self._find_and_return_category_sim, topic_name)
                for row in result:
                    found_cat.append(row)
                    #print("Found category: {row}".format(row=row))

    @staticmethod
    def _find_and_return_same_as(tx, category_name):
        query = (
            "MATCH (t:ns0__Topic {rdfs__label: $category_name})-[:owl__sameAs]->(t2:ns0__Topic) RETURN t2.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
    
    @staticmethod
    def _find_and_return_equivalent(tx, category_name):
        query = (
            "MATCH (t:ns0__Topic {rdfs__label: $category_name})-[:ns0__relatedEquivalent]->(t2:ns0__Topic) RETURN t2.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
    
    @staticmethod
    def _find_and_return_parent(tx, category_name):
        query = (
            "MATCH (t:ns0__Topic {rdfs__label: $category_name})<-[:ns0__superTopicOf]-(t2:ns0__Topic) RETURN t2.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]

    @staticmethod
    def _find_and_return_category_sim(tx, category_name):
        query = (
            "MATCH (t:skos__Concept) WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $category_name) > 0.92 RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
    
    @staticmethod
    def _find_and_return_category_parent_sim(tx, category_name):
        query = (
            "MATCH (t:skos__Concept) WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $category_name) > 0.92 RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
        
    # CATEGORY SEARCH BY TYPE
    def find_categories(self, category_type):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_categories, category_type)
            return result
            # for row in result:
            #     buss_categories.append(row)
            #     #print("Found category: {row}".format(row=row))
    
    @staticmethod
    def _find_and_return_categories(tx, category_type):
        query = (
            "MATCH (t:skos__Concept)-[:skos__topConceptOf]->(t2:skos__ConceptScheme {rdfs__label: $category_type}) RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_type=category_type)
        return [row["name"] for row in result]
    
    # FIND NODE BY ID
    def find_node_id(self, node_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_node_id, node_name)
            for nodeId in result:
                return nodeId
                #print("Node id: {nodeId}".format(nodeId=nodeId))

    @staticmethod
    def _find_and_return_node_id(tx, node_name):
        query = (
            "MATCH (t) WHERE t.rdfs__label = $node_name RETURN id(t) AS id"
        )
        result = tx.run(query, node_name=node_name)
        return [row["id"] for row in result]


    # FIND NODE LABEL BY ID
    def find_node_label(self, node_id):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_node_label, node_id)
            for node_name in result:
                return node_name
                #print("Node label: {node_name}".format(node_name=node_name))

    @staticmethod
    def _find_and_return_node_label(tx, node_id):
        query = (
            "MATCH (t) WHERE id(t) = $node_id RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, node_id=node_id)
        return [row["name"] for row in result]
    
    # CENTRALITY INFERENCE
    def find_centrality(self):
        with self.driver.session() as session:
            session.read_transaction(self._find_and_return_centrality)
        
            # for nodeId in result:                               
            #     print("Found similar: {node_name}".format(node_name=node_name))

    @staticmethod
    def _find_and_return_centrality(tx):
        query = (
            "CALL gds.pageRank.stream( "
            #"CALL gds.betweenness.stream( "
                "'graph' "
            ") "
            "YIELD "
                "nodeId, "
                "score "
        )
        result = tx.run(query)

        for row in result:
            node_name = app.find_node_label(row["nodeId"])
            centrality[node_name] = row["score"]
            
    
    # COMMUNITY INFERENCE
    def find_community(self):
        with self.driver.session() as session:
            session.read_transaction(self._find_and_return_community)

            # for nodeId in result:
            #     print("Found similar: {node_name}".format(node_name=node_name))

    @staticmethod
    def _find_and_return_community(tx):
        query = (
            "CALL gds.louvain.stream( "
                "'graph', { includeIntermediateCommunities: true } "
            ") "
            "YIELD "
                "nodeId, "
                "communityId, "
                "intermediateCommunityIds"
        )
        result = tx.run(query)
        
        for row in result:
            node_name = app.find_node_label(row["nodeId"])
            community[node_name] = row["communityId"]
    
    # JACCARD INFERENCE
    def find_jaccard_similarity(self):
        with self.driver.session() as session:
            session.read_transaction(self._find_and_return_jaccard_similarity)
        
            # for similarity in result:
            #     print("Found similarity: {similarity}".format(similarity=similarity))

    @staticmethod
    def _find_and_return_jaccard_similarity(tx):
        query = (
            "CALL gds.nodeSimilarity.stream( "
                "'graph' "
            ") YIELD "
                "node1, "
                "node2, "
                "similarity"
        )
        result = tx.run(query)

        for row in result:
            node_1 = app.find_node_label(row["node1"])
            node_2 = app.find_node_label(row["node2"])
            similarity[node_1, node_2] = row["similarity"]

    # LINK PREDICTION INFERENCE
    def find_link_prediction(self, first_term, second_term):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_link_prediction, first_term, second_term)
             
            for score in result:
                return score
                #print("Found similar: {score}".format(score=score))

    @staticmethod
    def _find_and_return_link_prediction(tx, first_term, second_term):
        query = (
            "MATCH (t1:ns0__Topic {rdfs__label: $first_term}) "
            "MATCH (t2:ns0__Topic {rdfs__label: $second_term}) "
            #RETURN gds.alpha.linkprediction.commonNeighbors(t1, t2) as score
            "RETURN gds.alpha.linkprediction.adamicAdar(t1, t2) as score"
        )
        result = tx.run(query, first_term=first_term, second_term=second_term)
        return [row["score"] for row in result]
    
    def create_graph_catalog(self):
        with self.driver.session() as session:
            session.read_transaction(self._create_graph_catalog)

    @staticmethod
    def _create_graph_catalog(tx):
        query = (
            "CALL gds.graph.create( "
                "'graph', "
                "['ns0__Topic', 'AI_RESOURCE', 'skos__Concept'], "
                "['ns0__superTopicOf', 'ns0__preferentialEquivalent', 'ns0__relatedEquivalent', 'owl__sameAs', 'HAS_TOPIC', 'HAS_CATEGORY'] "
            ")"
        )
        tx.run(query)

    def create_graph_catalog_simple(self):
        with self.driver.session() as session:
            session.read_transaction(self._create_graph_catalog_simple)

    @staticmethod
    def _create_graph_catalog_simple(tx):
        query = (
            "CALL gds.graph.create( "
                "'graph_topics', "
                "'ns0__Topic', "
                "['ns0__superTopicOf', 'ns0__preferentialEquivalent', 'ns0__relatedEquivalent', 'owl__sameAs'] "
            ")"
        )
        tx.run(query)
    
    def create_resource(self, res_name):
        with self.driver.session() as session:
            session.read_transaction(self._create_resource, res_name)

    @staticmethod
    def _create_resource(tx, res_name):
        query = (
            "CREATE (n:AI_RESOURCE {rdfs__label: $res_name})"
        )
        tx.run(query, res_name=res_name)

    def add_topic(self, topic_name, res_name):
        with self.driver.session() as session:
            session.read_transaction(self._add_topic, topic_name, res_name)

    @staticmethod
    def _add_topic(tx, topic_name, res_name):
        query = (
            "MATCH (n1:ns0__Topic {rdfs__label: $topic_name}) "
            "MATCH (n2:AI_RESOURCE {rdfs__label: $res_name}) "
            "MERGE (n1)-[:HAS_TOPIC]->(n2)"
        )
        tx.run(query, topic_name=topic_name, res_name=res_name)
    
    def return_topics(self):
        with self.driver.session() as session:
            result = session.read_transaction(self._return_topics)
            for name in result:
                print("{name}".format(name=name))

    @staticmethod
    def _return_topics(tx):
        query = (
            "MATCH (n:ns0__Topic) RETURN n.rdfs__label as name"
        )
        result = tx.run(query)
        return [row["name"] for row in result]

    def add_category(self, category_name):
        with self.driver.session() as session:
            session.read_transaction(self._add_category, category_name, res_name)

    @staticmethod
    def _add_category(tx, category_name, res_name):
        query = (
            "MATCH (n1:skos__Concept {rdfs__label: $category_name}) "
            "MATCH (n2:AI_RESOURCE {rdfs__label: $res_name}) "
            "MERGE (n2)-[:HAS_CATEGORY]->(n1)"
        )
        tx.run(query, category_name=category_name, res_name=res_name)
    
    def check_centrality(self, topic_name):
        try: 
            return centrality[topic_name]
        except KeyError:
            return 0.0
            

    def check_community(self, topic1_name, topic2_name):
        try:
            com1 = community[topic1_name]
        except KeyError:
            return -1

        try:
            com2 = community[topic2_name]
        except KeyError:
            return -1
        
        if (com1==com2):
             return 1
        else:
            return 0


    def check_similarity(self, topic1_name, topic2_name):
        try:
            return similarity[topic1_name, topic2_name]
        except KeyError:
            return 0.0

if __name__ == "__main__":
    # Aura queries use an encrypted connection using the "neo4j+s" URI scheme
    bolt_url = "bolt://localhost:7687"
    user = "neo4j"
    password = "1234"
    app = App(bolt_url, user, password)
    
    args = sys.argv
    
    mode = args[1]
    
    # PREPROCESS INFERENCE
    # app.find_centrality()
    # app.find_community()
    # app.find_jaccard_similarity()

    # PICKLE DUMP
    # output = open('infer_data.pkl', 'wb')
    # pickle.dump(centrality, output)
    # pickle.dump(community, output)
    # pickle.dump(similarity, output)
    # output.close()

    # PICKLE LOAD
    pkl_file = open('infer_data.pkl', 'rb')
    centrality = pickle.load(pkl_file)
    #pprint.pprint(centrality)
    community = pickle.load(pkl_file)
    #pprint.pprint(community)
    similarity = pickle.load(pkl_file)
    #pprint.pprint(similarity)
    pkl_file.close()

    # GRAPH CREATION GRAPH ALGORITHMS PLUGIN
    #app.create_graph_catalog()
    #app.create_graph_catalog_simple()

    # RESOURCE NAME OBTENTION
    res_name = ''
    for x in range(2, len(args)):
        if(x==2):
            res_name=res_name+args[x]
        else:
            res_name=res_name + " " + args[x]

    # TOPICS MATCHING
    with open("queries.txt") as f:
        queries = [x.rstrip("\n") for x in f.readlines()]

    queries = [x.strip() for x in queries]
    queries = list(dict.fromkeys(queries))

    for x in queries:
        app.find_topic(x)

    # for topic in topic_list:
    #     print(topic)
    # print("---------")

    # RESOURCE CREATION
    # #app.create_resource(res_name)
    # for topic in topic_list:
    #     app.add_topic(topic)
    
    # AI4EU MATCHING
    topic_list = list(dict.fromkeys(topic_list))
    
    cat = app.find_categories("Business Categories")
    for row in cat:
        buss_categories.append(row)
    
    cat = app.find_categories("Technical Categories")
    for row in cat:
        tech_categories.append(row)

    for topic in topic_list:
        buss_categories_sug.append("AI for " + topic)

    tech_categories_sug = topic_list.copy()

    app.match_categories()

    found_cat = list(dict.fromkeys(found_cat))
    result_cat = []
    result_cat.append(buss_categories)
    result_cat.append(tech_categories)
    result_cat.append(found_cat)
    # for cat in buss_categories:
    #     print(cat)
    # print("---------")
    # for cat in tech_categories:
    #     print(cat)
    # print("---------")
    # for cat in found_cat:
    #     print(cat)
    # print("---------")

    # LOAD SIMPLE QUERIES
    simple_queries = []
    with open("simple queries.txt") as f:
        simple_queries = [x.rstrip("\n") for x in f.readlines()]

    # FRIST SEMANTIC REASONING (WITH MATCHES) -> CENTRALITY AND COMMUNITY
    first_sem_sug = []
    app.inverse_super()
    for topic in topic_list:
        rels = app.find_relationship(topic)
        for rel in rels:
            cent = app.check_centrality(rel)
            if (cent > 0.0):
                first_sem_sug.append(rel)
    
    app.inverse_super()

    # SECOND SEMANTIC REASONING (WITH INPUT AND SIMPLE_QUERIES) -> COMMUNITY???
    second_sem_sug = []

    rels_term = app.find_related_term("internet", "streaming")
    print(rels_term)

    # CHANGE FOR CLICK WORD INPUT
    rang = 5
    for input in simple_queries:
        ind = simple_queries.index(input)
        for x in range(-rang,rang):
            try:
                query = simple_queries[ind+x]
            except:
                query = simple_queries[ind-rang-x]
            #print(query)
            rels_term = app.find_related_term(input, query)
            for term in rels_term:
                second_sem_sug.append(term)

    # FRIST SIMILARITY REASONING (WITH RES_NAME) -> LINK PREDICTION
    first_sim_sug = []
    similars_sug = app.find_suggestion_similarity(res_name)
    similars_sug = list(dict.fromkeys(similars_sug))
    for similar in similars_sug:
        for topic in topic_list:
            pred = app.find_link_prediction(topic, similar) # CHECK NODE CLOSENESS
            if (pred>0.0):
                first_sim_sug.append(similar)

    # SECOND SIMILARITY REASONING (WITH MATCHES???) -> NODE SIMILARITY
    second_sim_sug = []
    for topic in topic_list:
        similars_par = app.find_parent_similarity(topic)
        similars_par = list(dict.fromkeys(similars_par))
        for similar in similars_par:
            print(similar)
            sim = app.check_similarity(query, similar) # CHECK IF NODE SIM
            if (sim>0.0):
                second_sim_sug.append(similar)
        
    print(first_sem_sug)
    second_sem_sug = list(dict.fromkeys(second_sem_sug))
    #print(second_sem_sug)
    print(first_sim_sug)
    print(second_sim_sug)

    # COLLECT SUGGESTIONS
    #print(suggestions)

    # app.return_topics()
    # print("---------")

    # INSERT TOPIC
    #app.insert_topic("convolutional_learning", "artificial intelligence")

    # RELATE CATEGORY
    #app.add_category(cat_name)

    #app.delete_topic
    #MATCH (t:ns0__Topic) WHERE t.rdfs__label = "convolutional_learning" DETACH DELETE t

    app.close()

    # TEST REFINEMENT REASONING TEST
    # topic1_name = "machine learning"
    # topic2_name = "artificial intelligence"

    # cent = app.check_centrality(topic1_name) # PAGE RANK
    # print("cent")
    # print(cent)

    # comm = app.check_community(topic1_name, topic2_name) # CHECK IF SAME COMM
    # print("comm")
    # print(comm)

    # sim = app.check_similarity(topic1_name, topic2_name) # CHECK IF NODE SIM
    # print("sim")
    # print(sim)

    # pred = app.find_link_prediction(topic1_name, topic2_name) # CHECK IF NODE CLOSENESS
    # print("link")
    # print(pred)