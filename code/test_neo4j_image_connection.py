from py2neo import Graph

def make_neo4j_connection_container_bolt_localhost_7687():
    print(f"\nFunc make_neo4j_connection_container_bolt_localhost_7687 called....\n")
    gph = None
    try:
        gph = Graph(uri="bolt://localhost:7687",auth=("neo4j","cba"))
    except Exception as error_msg_neo_connect:
        print(f"Error message bolt_localhost_7687: {error_msg_neo_connect}")
    return gph

def make_neo4j_connection_container_http_localhost_7687():
    print(f"\nFunc make_neo4j_connection_container_http_localhost_7687 called....\n")
    gph = None
    try:
        gph = Graph(uri="http://localhost:7687",auth=("neo4j","cba"))
    except Exception as error_msg_neo_connect:
        print(f"Error message http_localhost_7687: {error_msg_neo_connect}")
    return gph

def main():
    print(f"\nTesting neo4j image connection from within container script....\n")

    gph_obj_bolt_localhost_7687 = make_neo4j_connection_container_bolt_localhost_7687()
    print(f"\ngph_obj_bolt_localhost_7687 = {gph_obj_bolt_localhost_7687}\n")

    gph_obj_http_localhost_7687 = make_neo4j_connection_container_http_localhost_7687()
    print(f"\ngph_obj_http_localhost_7687 = {gph_obj_http_localhost_7687}\n")
    

if __name__ == "__main__":
    main()