from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable

class App:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def create_friendship(self, person1_name, person2_name):
        with self.driver.session() as session:
            # Write transactions allow the driver to handle retries and transient errors
            result = session.write_transaction(
                self._create_and_return_friendship, person1_name, person2_name)
            for row in result:
                print("Created friendship between: {p1}, {p2}".format(p1=row['p1'], p2=row['p2']))

    @staticmethod
    def _create_and_return_friendship(tx, person1_name, person2_name):
        # To learn more about the Cypher syntax, see https://neo4j.com/docs/cypher-manual/current/
        # The Reference Card is also a good resource for keywords https://neo4j.com/docs/cypher-refcard/current/
        query = (
            "CREATE (p1:Person { name: $person1_name }) "
            "CREATE (p2:Person { name: $person2_name }) "
            "CREATE (p1)-[:KNOWS]->(p2) "
            "RETURN p1, p2"
        )
        result = tx.run(query, person1_name=person1_name, person2_name=person2_name)
        try:
            return [{"p1": row["p1"]["name"], "p2": row["p2"]["name"]}
                    for row in result]
        # Capture any errors along with the query and data for traceability
        except ServiceUnavailable as exception:
            logging.error("{query} raised an error: \n {exception}".format(
                query=query, exception=exception))
            raise

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
            result = session.read_transaction(self._find_and_return_topic_exact, topic_name)
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
    #app.create_friendship("Alice", "David")
    #app.find_person("Alice")
    #app.find_topic("artificial intelligence")
    #app.insert_super_topic("artificial_intelligence")
    app.insert_topic("convolutional_learning", "artificial intelligence")
    app.find_topic("convolutional_learning")
    app.close()

    #app.delete_topic
    #MATCH (t:ns0__Topic) WHERE t.rdfs__label = "convolutional_learning" DETACH DELETE t
    