from py2neo import Graph
import time

## for container which was started as below
## docker run --env NEO4J_AUTH=neo4j/cba -p 8901:7474 rbewoor/myneo4j410:1.0
def make_neo4j_connection_container_bolt_localhost_7687():
    """
    Establish connection to Neo4j and return graph object
    """
    print(f"\nFunc make_neo4j_connection_container_bolt_localhost_7687 called....\n")
    gph = None
    try:
        gph = Graph(uri="bolt://localhost:7687",auth=("neo4j","cba"))
    except Exception as error_msg_neo_connect:
        print(f"Error message bolt_localhost_7687: {error_msg_neo_connect}")
    return gph
def make_neo4j_connection_container_bolt_localhost_7474():
    """
    Establish connection to Neo4j and return graph object
    """
    print(f"\nFunc make_neo4j_connection_container_bolt_localhost_7474 called....\n")
    gph = None
    try:
        gph = Graph(uri="bolt://localhost:7474",auth=("neo4j","cba"))
    except Exception as error_msg_neo_connect:
        print(f"Error message bolt_localhost_7474: {error_msg_neo_connect}")
    return gph

def main():
    print(f"\nTesting neo4j image connection from within container script....\n")

    #SLEEP_TIME = 0 #seconds

    #print(f"Sleeping for {SLEEP_TIME} started....")
    #time.sleep(SLEEP_TIME)
    #print(f"Sleeping for {SLEEP_TIME} ended....")

    gph_obj_bolt_localhost_7687 = make_neo4j_connection_container_bolt_localhost_7687()
    print(f"\ngph_obj_bolt_localhost_7687 = {gph_obj_bolt_localhost_7687}\n")
    
    gph_obj_bolt_localhost_7474 = make_neo4j_connection_container_bolt_localhost_7474()
    print(f"\ngph_obj_bolt_localhost_7474 = {gph_obj_bolt_localhost_7474}\n")
    
if __name__ == "__main__":
    main()