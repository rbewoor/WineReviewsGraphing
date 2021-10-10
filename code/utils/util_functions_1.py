import logging
from py2neo import Graph

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
        #gph = Graph(uri="bolt://localhost:7687",auth=("neo4j","abc"))
        gph = Graph(uri="http://localhost:7474",auth=("neo4j","abc"))
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