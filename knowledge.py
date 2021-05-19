from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

class App:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def find_person(self, person_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_person, person_name)
            for row in result:
                print("Found person: {row}".format(row=row))

    @staticmethod
    def _find_and_return_person(tx, person_name):
        query = (
            "MATCH (p:Person) "
            "WHERE p.name = $person_name "
            "RETURN p.name AS name"
        )
        result = tx.run(query, person_name=person_name)
        return [row["name"] for row in result]

    def insert_topic(self, topic_name, super_topic_name):
        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
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
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

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
            "MATCH (t1: ns0__Topic)-[rel:ns0__superTopicOf]->(t2: ns0__Topic) CALL apoc.refactor.invert(rel) yield input, output RETURN input, output"
        )
        tx.run(inverse)

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

    def find_topic(self, topic_name):
        with self.driver.session() as session:
            result = session.read_transaction(self._find_and_return_topic_sim, topic_name)
            for row in result:
                print("Found topic: {row}".format(row=row))

    @staticmethod
    def _find_and_return_topic_exact(tx, topic_name):
        query = (
            "MATCH (t:ns0__Topic) WHERE t.rdfs__label = $topic_name RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]

    @staticmethod
    def _find_and_return_topic_sim(tx, topic_name):
        query = (
            "MATCH (t:ns0__Topic) WHERE apoc.text.levenshteinSimilarity(t.rdfs__label, $topic_name) > 0.9 RETURN t.rdfs__label AS name"
        )
        result = tx.run(query, topic_name=topic_name)
        return [row["name"] for row in result]


if __name__ == "__main__":
    # Aura queries use an encrypted connection using the "neo4j+s" URI scheme
    bolt_url = "bolt://localhost:7687"
    user = "neo4j"
    password = "1234"
    app = App(bolt_url, user, password)

    #app.find_relationship("internet","streaming")
    app.find_related_term("internet", "streaming")

    #app.find_topic("artificial intelligence")
    #app.insert_topic("convolutional_learning", "artificial intelligence")

    #with open("queries.txt") as f:
    #    queries = f.readlines()
    
    #queries = [x.strip() for x in queries]
    
    #for x in queries:
    #    app.find_topic(x)
    
    app.close()

    #app.delete_topic
    #MATCH (t:ns0__Topic) WHERE t.rdfs__label = "convolutional_learning" DETACH DELETE t
    