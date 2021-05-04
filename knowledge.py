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

    #app.find_topic("artificial intelligence")
    #app.insert_topic("convolutional_learning", "artificial intelligence")

    with open("queries.txt") as f:
        queries = f.readlines()
    queries = [x.strip() for x in queries]
    
    for x in queries:
        app.find_topic(x)
    
    app.close()

    #app.delete_topic
    #MATCH (t:ns0__Topic) WHERE t.rdfs__label = "convolutional_learning" DETACH DELETE t
    