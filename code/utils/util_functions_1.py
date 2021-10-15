import logging
from py2neo import Graph
import os

def my_print_and_log(_in_fstring_msg, _log_level="info", _only_log=False):
    """
    Print and log the input message,
    By default will also print to console.
    """
    if not _only_log:
        print(f"\nLOG_LEVEL {_log_level.upper()} :: {_in_fstring_msg}")
    if _log_level == "debug":
        logging.debug(f"{_in_fstring_msg}")
    elif _log_level == "warning":
        logging.warning(f"{_in_fstring_msg}")
    elif _log_level == "info":
        logging.info(f"{_in_fstring_msg}")
    elif _log_level == "error":
        logging.error(f"{_in_fstring_msg}")
    elif _log_level == "critical":
        logging.critical(f"{_in_fstring_msg}")
    else:
        print(f"\n\n\nFATAL ERROR - wrong parameters passed to print_and_log function\n\n\nExiting with RC=9000\n")
        exit(9000)
    return

def make_neo4j_connection(_on_fail_return=False):
    """
    Establish connection to Neo4j and return graph object.
    Call function with flag set to True to return None even on failure.
    Returns:
        Graph object, Error message
    """
    try:
        in_docker_flag = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', "no")
        neo_cont_name = os.environ.get('NEO4J_CONTAINER_NAME', None)
        if in_docker_flag == "yes":
            ## seen from here: https://towardsdatascience.com/get-going-with-neo4j-and-jupyter-lab-through-docker-a1994e0e95c6 and https://github.com/cj2001/data_science_neo4j_docker/blob/main/notebooks/test_db_connection.ipynb
            #gph = Graph("bolt://neo4j:7687", name="neo4j", password="1234")
            
            #gph_uri_cont = "".join(["bolt://", neo_cont_name, ":7687"])
            #print(f"\ngph_uri_cont = {gph_uri_cont}\n")
            #gph = Graph(uri=gph_uri_cont, auth=("neo4j","cba"))

            print(f"\nIn container, using env variable, neo_cont_name={neo_cont_name}\n")
            gph = Graph(scheme='bolt', host=neo_cont_name, port=7687, user="neo4j", password="cba", verify=False, secure=False)

            #gph_uri_cont = "".join(["bolt://neo4j:cba@", neo_cont_name, ":7687"])  ## someone did this: NEO4J_BOLT_URL=bolt://neo4j:foobar@neo4j_db:7687
            #print(f"\ngph_uri_cont = {gph_uri_cont}\n")
            #gph = Graph(uri=gph_uri_cont)
            #gph = Graph(uri=gph_uri_cont, name="neo4j",password="cba")
            
        else:
            gph = Graph(uri="bolt://localhost:7687",auth=("neo4j","abc"))
            #gph = Graph(uri="http://localhost:7474",auth=("neo4j","abc"))
            #gph = Graph(uri="http://127.0.0.1:7474",auth=("neo4j","abc"))
    except Exception as error_msg_neo_connect:
        if _on_fail_return:
            ## return graph object as None, error message
            return None, error_msg_neo_connect
        else:
            myStr = "\n".join([
                f"\nFATAL ERROR: Could not establish connnection to neo4j.",
                f"Error message :: {error_msg_neo_connect}",
                f"EXITING with error code 9050",
                ])
            my_print_and_log(myStr, "error")
            exit(9050)
    ## all good - return graph object, error message as None
    return gph, None

def new_func():
    pass