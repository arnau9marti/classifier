from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable
import sys

topic_list = []
found_cat = []
buss_categories = []
tech_categories = []

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
            for row in result:
                print("Created super topic relationship between: {t} and {st}".format(t=row['t'], st=row['st']))

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
                print("Found topic: {row}".format(row=row))

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
            "WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $topic_name) > 0.8 "
            "RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]
    
    # FRIST SEMANTIC REASONING
    def find_relationship(self, topic_name1, topic_name2):
        with self.driver.session() as session:
            session.read_transaction(self._inverse_super)
            result1 = session.read_transaction(self._find_and_return_categories, topic_name1)
            result2 = session.read_transaction(self._find_and_return_categories, topic_name2)
            session.read_transaction(self._inverse_super)
            result = set.intersection(set(result1), set(result2))
        
            for row in result:
                print("Found topic: {row}".format(row=row))
                
    @staticmethod
    def _find_and_return_categories(tx, topic_name):
        query = (
            "MATCH (c:ns0__Topic {rdfs__label: $topic_name}) "
            "CALL n10s.inference.nodesInCategory(c, { "
            "  inCatRel: 'ns0__preferentialEquivalent', "
            #"  inCatRel: 'ns0__relatedEquivalent', "
            "  subCatRel: 'ns0__superTopicOf' "
            "}) "
            "YIELD node "
            "RETURN node.rdfs__label"
        )
        intersect = (
            "RETURN apoc.coll.intersection($result1, $result2)" 
        )
        result = tx.run(query, topic_name=topic_name)
        #intersection = tx.run(intersect, result1=result1, result2=result2)

        return [row["node.rdfs__label"] for row in result]

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
        
        if result != None:
            print("RELATED")

    @staticmethod
    def _find_and_return_related_term(tx, broad_term, concrete_term):
        query = (
            "MATCH path = (c:ns0__Topic)-[:ns0__relatedEquivalent]->(category)-[:ns0__superTopicOf*]->(:ns0__Topic {rdfs__label: $broad_term}) "
            "WHERE c.rdfs__label contains $concrete_term "
            "RETURN path"
        )
        result = tx.run(query, broad_term=broad_term, concrete_term=concrete_term)
        return [row["path"] for row in result]

    # FRIST SIMILARITY REASONING WIP
    def find_suggestion_similarity(self, resource_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_similar_resources, resource_name)
        
        if result != None:
            print("SUGGESTED")

    def _find_and_return_similar_resources(tx, resource_name):
        query = (
            #"MATCH (c:AI_RESOURCE {rdfs__label: $resource_name}), "
            "MATCH (c:AI_RESOURCE {rdfs__label: 'MACHINE LOGISTICS SYSTEM'}), "
            "path = (c)<-[:HAS_TOPIC]-(topic), "
            "otherPath = (topic)-[:HAS_TOPIC]->(res) "
            "RETURN path, otherPath"
        )
        result = tx.run(query, resource_name=resource_name)
        return [row["path"] for row in result]

    # SECOND SIMILARITY REASONING WIP
    def find_parent_similarity(self, topic_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_outcat_path, topic_name)
        
        if result != None:
            print("SUGGESTED")

    @staticmethod
    def _find_and_return_incat_path(tx, topic_name):
        query = (
            #"MATCH (c:ns0__Topic {rdfs__label: $topic_name}), "
            "MATCH (c:ns0__Topic {rdfs__label: 'mobile operators'}), "
            "path = (c)-[:HAS_TOPIC]->(res)-[:HAS_CATEGORY]->(cat), "
            "otherPath = (other)-[:HAS_CATEGORY]->(cat) "
            "return path, otherPath"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["path"] for row in result]

    @staticmethod
    def _find_and_return_outcat_path(tx, topic_name):
        query = (
            #"MATCH (c:ns0__Topic {rdfs__label: $topic_name}), "
            "MATCH (c:ns0__Topic {rdfs__label: 'mobile operators'}), "
                "entityPath = (c)-[:HAS_TOPIC]->(res)-[:HAS_CATEGORY]->(cat), "
                "path = (cat)-[:skos__topConceptOf]->(parent)<-[:skos__topConceptOf]-(otherCat), "
                "otherEntityPath = (otherCat)<-[:HAS_CATEGORY]-(otherWiki)<-[:HAS_TOPIC]-(other) "
            "RETURN other.rdfs__label, "
                "[(other)-[:HAS_TOPIC]->()-[:HAS_CATEGORY]->(entity) | entity.rdfs__label] AS otherCategories, "
                "collect([node in nodes(path) | node.rdfs__label]) AS pathToOther "
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["path"] for row in result]

    # CATEGORY MATCHING
    def match_categories(self):
        with self.driver.session() as session:
            aux_topic_list = []

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
                
            for topic in aux_topic_list:
                topic_list.append(topic)

            for topic_name in topic_list:
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
            "MATCH (t:skos__Concept) WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $category_name) > 0.8 RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
    
    @staticmethod
    def _find_and_return_category_parent_sim(tx, category_name):
        query = (
            "MATCH (t:skos__Concept) WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $category_name) > 0.8 RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_name=category_name)
        return [row["name"] for row in result]
        
    # CATEGORY SEARCH BY TYPE
    def find_categories(self, category_type):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_categories, category_type)
            for row in result:
                buss_categories.append(row)
                #print("Found category: {row}".format(row=row))
    
    @staticmethod
    def _find_and_return_categories(tx, category_type):
        query = (
            "MATCH (t:skos__Concept)-[:skos__topConceptOf]->(t2:skos__ConceptScheme {rdfs__label: $category_type}) RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, category_type=category_type)
        return [row["name"] for row in result]
        
if __name__ == "__main__":
    # Aura queries use an encrypted connection using the "neo4j+s" URI scheme
    bolt_url = "bolt://localhost:7687"
    user = "neo4j"
    password = "1234"
    app = App(bolt_url, user, password)
    
    args = sys.argv
    
    print(args[1])
    print("HELLO")
    #print(args[2])

    # FRIST SEMANTIC REASONING
    #app.find_relationship("internet","streaming")
    
    # SECOND SEMANTIC REASONING
    #app.find_related_term("internet", "streaming")

    # FRIST SIMILARITY REASONING
    #app.find_suggestion_similarity()

    # SECOND SIMILARITY REASONING
    #app.find_parent_similarity()

    # CENTRALITY REASONING

    # AI4EU MATCHING

    #REMOVE TOO SIMILAR
    topic_list = ['cyber security', 'machine-learning', 'machine learning', 'artificial intelligence', 'logistic', 'logistic', 'sensor', 'sensor data', 'sensor data']
    topic_list = list(dict.fromkeys(topic_list))
    
    tech_categories = topic_list.copy()
    app.find_categories("Business Categories")

    for topic in topic_list:
        buss_categories.append("AI for " + topic)

    for topic in buss_categories:
        topic_list.append(topic)

    app.match_categories()

    found_cat = list(dict.fromkeys(found_cat))
    result_cat = []
    result_cat.append(buss_categories)
    result_cat.append(tech_categories)
    result_cat.append(found_cat)
    print(buss_categories)
    # TOPICS MATCHING

    # with open("queries.txt") as f:
    #     queries = f.readlines()
    
    # queries = [x.strip() for x in queries]
    #queries = list(dict.fromkeys(queries))

    # for x in queries:
    #     app.find_topic(x)
    
    app.close()

    # INSERT AND DELETE TOPICS

    #app.insert_topic("convolutional_learning", "artificial intelligence")

    #app.delete_topic
    #MATCH (t:ns0__Topic) WHERE t.rdfs__label = "convolutional_learning" DETACH DELETE t
    