## -------------------------------------------------------------------------------------------------------------------------------------------------
## Goal: Process description text of wines as unstructured data from the input files. Perform feature extraction and load to Neo4j database.
##       Allow user to run pre-set queries and/or upload new data from a file with a GUI (using tkinter).
## -------------------------------------------------------------------------------------------------------------------------------------------------
## General logic flow:
##    Earlier in pipeline:
##    Downloaded data from https://www.kaggle.com/zynicide/wine-reviews
##    Using only the description column, wrote each description to individual file to a folder called 'inData'.
## 1) Expects all the input files to be in folder called 'inData' with only .txt files.
## 2) If flag to reload to Neo4j is True, will first process the specified number of these files and extract the features into a json file.
##    This json file is saved to the folder 'outData'.
##    The number of input files processed depends on the value of the run time parameter.
##    Note: Before reloading, the entire Neo4j graph will first be cleared.
## 3) The saved json file is used for loading data to Neo4j graph.
## 4) Graphical user interface (using Tkinter) shown with option:
##    - extract features from a new input file and upload to Neo4j; and/ or
##    - run pre-set queries based on user input
## 5) Log file is saved to the folder 'tempDir'
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Feature extraction notes:
##       1) Processing of the raw description text: lowercase, remove stop words and punctuations, lemmatize
##       2) Name-Entity-Recognition (NER) with Spacy
##       3) Word count, sentence count
##       4) Flavor names using pre-defined list
##       5) Sentiment score with spacytextblob
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Versions of packages:
##       1) spacy:          3.1.1
##       1) py2neo:         2020.0.0
##       1) spacytextblob:  3.0.1
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Neo4j graph schema:
##   Nodes and Relationship schema:
##       1) (REVIEW node) - HAS_FLAVOR -> (FLAVOR node)
##       2) (REVIEW node) - RELATES_TO_ENTITY -> (ENTITY node)
##   Properties:
##       1) REVIEW node: filename, sentiment score, word count, sentence count, raw description text, processed description text
##       2) Entity node: text, label name, label code
##             e.g. name=2020, label=391, label_=DATE
##       3) Flavor node: name
##             e.g. name=cherry
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Notes on running this script:
##    1) Expects the input files to be in a folder called 'inData'. It should contain .txt files created earlier in the pipeline.
##       If the reload to Neo flag is set true, will try to process every file in this folder.
##    2) Will create a folder called 'outData' to store the intermediate json files.
##    3) Log file is saved to the folder 'tempDir'
## Command line arguments:
##    Compulsory:
##    1) None
##    Optional:
##    1) reloadNeo :: Flag to upload data to Neo4j first - will also clear out the graph before loading
##                    Valid values Y or N in lower or upper case
##    2) uploadLimit :: how many input files to process and load to Neo4j,
##                       valid values: 0 < uploadLimit < 129971
##                       default value=100
## Examples of running the script:   
##    python3 script-name -reloadNeo <<Y or N>> -uploadLimit <<limit_as_interger>>
##    e.g. python3 02_load_neo_show_gui_1.py -reloadNeo Y -uploadLimit 50
## -------------------------------------------------------------------------------------------------------------------------------------------------

## general
import pandas as pd
import glob
import os
import string
from copy import deepcopy
import json
import argparse
import logging
from tqdm import tqdm

## gui
import tkinter as tk
from functools import partial

##   imports for neo4j
import sys
from py2neo import Graph

## imports for data extraction for neo4j
from spacytextblob.spacytextblob import SpacyTextBlob
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.lang.en import English

## custom packages
from utils.util_functions_1 import my_print_and_log, make_neo4j_connection
#from utils.util_functions_1 import *

def load_neo4j_from_json(_data_file=None, _clear_graph=False):
    my_print_and_log(f"\nIn load_neo4j function, attempting to load file and make entries to database\n")

    neo_data = None
    if _data_file is None or not os.path.exists(_data_file):
        myStr = "\n".join([
            f"\nFATAL ERROR: None or invalid json data input file provided: {_data_file}",
            f"EXITING with error code 110",
            ])
        my_print_and_log(myStr, "error")
        exit(110)
    
    try:
        with open(_data_file, "r") as f:
            neo_data = json.load(f)
        my_print_and_log(f"\nSuccessfully loaded json data from file: {_data_file}\n", "info")
    except Exception as reload_neo_file_error:
        myStr = "\n".join([
            f"\nFATAL ERROR: Could not reload data from json file.",
            f"Error message :: {reload_neo_file_error}",
            f"EXITING with error code 114",
            ])
        my_print_and_log(myStr, "error")
        exit(114)
    
    ## setup the cypher queries for neo4j
    stmt0_clear_graph = r'MATCH (n) DETACH DELETE n'
    stmt1_rev_node = r'MERGE (:Review {name: $_in_rev_name, count_sent: $_in_cnt_sents, count_words: $_in_cnt_words, senti_score: $_in_senti_polarity, raw_text: $_in_raw_text, proc_text: $_in_proc_text})'
    stmt2_ent_node = r'MERGE (:Entity {name: $_in_ent_text, label: $_in_ent_label, label_: $_in_ent_label_})'
    stmt3_flav_node = r'MERGE (:Flavor {name: $_in_flav_name})'
    stmt10 = r'MATCH (rn1:Review{name: $_in_rev_name}) MATCH (e1:Entity{name: $_in_ent_text}) CREATE (rn1)-[:RELATES_TO_ENTITY]->(e1)'
    stmt11 = r'MATCH (rn1:Review{name: $_in_rev_name}) MATCH (f1:Flavor{name: $_in_flav_name}) CREATE (rn1)-[:HAS_FLAVOR]->(f1)'
    
    ## get graph object - but exit program if problem
    graph, _ = make_neo4j_connection(_on_fail_return=False)
    try:
        ## clear the entire graph if flag is set
        if _clear_graph:
            tx = graph.begin()
            tx.run(stmt0_clear_graph, parameters={})
            tx.commit()
            while not tx.finished():
                pass # tx.finished return True if the commit is complete
            my_print_and_log(f"\nCleared the graph...\n")

        ## load data
        len_neo_data = len(neo_data)
        my_print_and_log(f"\nTotal entries to process = {len_neo_data}\n")
        idx1, idx2, idx3 = 0,0,0
        for idx1, neo_entry in enumerate(tqdm(neo_data)):
            my_print_and_log(f"Attempting to update of entry {idx1+1} of {len_neo_data}....", _only_log=True)
            tx = graph.begin()
            # create Review node if not already existing
            tx.run(stmt1_rev_node, parameters={
                '_in_rev_name': neo_entry['Review']['name'],
                '_in_cnt_sents': neo_entry['Review']['cnt_sents'],
                '_in_cnt_words': neo_entry['Review']['cnt_words'],
                '_in_senti_polarity': neo_entry['Review']['sentiment']['polarity'],
                '_in_raw_text': neo_entry['RevText']['raw'],
                '_in_proc_text': neo_entry['RevText']['processed'],
                })
            # create Enttity node and relationship if not already existing
            for idx2, ent in enumerate(neo_entry['Entities']):
                tx.run(stmt2_ent_node, parameters={
                    '_in_ent_text': ent['text'],
                    '_in_ent_label': ent['label'],
                    '_in_ent_label_': ent['label_'],
                    })
                tx.run(stmt10, parameters={
                    '_in_rev_name': neo_entry['Review']['name'],
                    '_in_ent_text': ent['text'],
                    })
            # create flavor note and relationship if not already existing
            for idx3, flav in enumerate(neo_entry['Flavors']):
                tx.run(stmt3_flav_node, parameters={
                    '_in_flav_name': flav,
                    })
                tx.run(stmt11, parameters={
                    '_in_rev_name': neo_entry['Review']['name'],
                    '_in_flav_name': flav,
                    })
            tx.commit()
            while not tx.finished():
                pass # tx.finished return True if the commit is complete
            my_print_and_log(f"\nCompleted updating entry {idx1+1} of {len_neo_data}.", _only_log=True)
        my_print_and_log(f"\nUpdated Neo4j: Review nodes={idx1}, Entity nodes={idx2}, Flavor nodes={idx3}\n\n")
    except Exception as neo_update_error:
        myStr = "\n".join([
            f"\nFATAL ERROR: Problem updating neo4j.",
            f"Error message :: {neo_update_error}",
            f"EXITING with error code 120",
            ])
        my_print_and_log(myStr, "error")
        my_print_and_log(f"Attempting to process this neo entry data:\n{neo_entry}\n")
        exit(120)

def preprocess_text(_in_tokens, _in_punc, _in_stop_words):
    """
    Goal: Preprocess the raw text - lemmatize and remove stop words
    Accepts: input tokens, punctuation and stopwords
    Return: processed string
    """
    _in_tokens = [ word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in _in_tokens ]
    _in_tokens = [ word for word in _in_tokens if word not in _in_stop_words and word not in _in_punc ]
    _in_tokens = " ".join([i for i in _in_tokens])
    return _in_tokens

def get_features_set1(_fname, _text, _all_neo, _nlp, _punctuations, _stopwords, _do_ner=False, _do_topic=False, _do_sentiment=False):
    """
    Goal: Preprocess the raw text and extract features for neo4j
    Accepts: filename, review text, data structure for neo, and other required variables
    Return: text after preprocessing
    """
    # master list of flavor names that should be extracted
    flavor_names_master = 'wood,oak,spices,spice,pepper,blackberry,hicoky,cigar,menthol,smoky,forest,raspberry,berry,berries,currant,currants,licorice,coconut,leather,coconut,plum,chocolate,orange,honey,gooseberry,fruit,fruity,strawberry,cherry,oily,coffee,expresso,cranberry,pineapple,tangerine,testflavor1,testflavor2,testflavor3,testflavor4'
    flavor_names_master = flavor_names_master.split(',')
    # basic setup for one entry
    neo_entry = {
        'Review': {
            'name': None,
            'cnt_sents': None,
            'cnt_words': None,
            'sentiment': None,
        },
        'RevText': {
            'raw': None,
            'processed': None,
        },
        'Entities': list(),
        'Flavors': list(),
        'Varietals': list(),
    }
    
    # node name - same as file name
    node_name = _fname.split('.')[0]
    neo_entry['Review']['name'] = node_name
    neo_entry['RevText']['raw'] = _text
    
    doc = _nlp(_text)
    
    # count words
    tokens = [token.text for token in doc]
    neo_entry['Review']['cnt_words'] = len(tokens)
    
    # count sentences
    sentences = list(doc.sents)
    #print(sentences)
    neo_entry['Review']['cnt_sents'] = len(sentences)
    
    # preprocess text
    neo_entry['RevText']['processed'] = preprocess_text(doc, _punctuations, _stopwords)
    
    # sentiment analysis
    if _do_sentiment:
        neo_entry['Review']['sentiment'] = dict()
        neo_entry['Review']['sentiment']['polarity'] = doc._.polarity
        neo_entry['Review']['sentiment']['subjectivity'] = doc._.subjectivity
        neo_entry['Review']['sentiment']['assessments'] = doc._.assessments
    
    # topic modeling
    if _do_topic:
        pass
    
    # name entity
    if _do_ner:
        if doc.ents:
            for ent in doc.ents:
                one_entity = {
                    'text': None,
                    'label_': None,
                    'label': None,
                }
                #print(f"\ntext = {ent.text}\nlabel_ = {ent.label_} \
                #\nlabel = {ent.label} \
                #\nspacy.explain(label_) = {str(spacy.explain(ent.label_))} \
                #")
                one_entity['text'] = ent.text
                one_entity['label'] = ent.label
                one_entity['label_'] = ent.label_
                neo_entry['Entities'].append(one_entity)
    
    # check flavors
    #print(f"\nprocessed text=\n{neo_entry['RevText']['processed']}\n")
    for word in neo_entry['RevText']['processed'].split(" "):
        if word in flavor_names_master:
            neo_entry['Flavors'].append(word)
    
    # add entry built to the final data structure
    _all_neo.append(neo_entry)

    return neo_entry['RevText']['processed']

class c_wine_tool_window:
    def __init__(self, _nlp, _punctuations, _stopwords, _flag_ner, _flag_topic, _flag_sentiment, _op_dir):
        self.nlp = _nlp
        self.punctuations = _punctuations
        self.stopwords = _stopwords
        self.flag_ner = _flag_ner
        self.flag_topic = _flag_topic
        self.flag_sentiment = _flag_sentiment
        self.OP_DIR = _op_dir

        self.root = tk.Tk()
        self.root.title(f"Wine Reviews Interaction Tool - demo version")
        self.root.geometry("1200x900")
        
        self.status_msg = tk.StringVar()
        self.status_msg.set(f"Please enter a file to upload or run some query. Waiting for user input...")
        self.upload_to_neo_msg = f"Upload"
        self.upload_file_path = f"Path :"
        self.path_editable = f"--------"
        self.query_data_fixed = "Enter query data :"
        self.query_input_data = f"--------"
        self.queries_explained = "\n".join([
            f"Query 1: Count nodes of a particular type. Enter either Review OR Flavor OR Entity, e.g. <<Review>>",
            f"Query 2: Count Review nodes with minimum specified values for number of words and sentiment score. Enter values separated by comma e.g. <<20,0.15>>",       
            f"Query 3: Get a list of Review nodes with 'HAS_FLAVOR' relationship to specified flavors. e.g. <<pepper,strawberry>>",
        ])
        self.query_1_msg = f"Run Query 1"
        self.query_2_msg = f"Run Query 2"
        self.query_3_msg = f"Run Query 3"
        self.result_fixed_text = "Result :"
        self.result = "---------------"

        ## button upload to Neo
        self.but_upload_to_neo = tk.Button(
            master=self.root,
            text=self.upload_to_neo_msg,
            bg="green", fg="white",
            relief=tk.RAISED,
            width=(len(self.upload_to_neo_msg) + 4),
            height=1,
            borderwidth=7,
            command=partial(
                self.do_upload_file_neo_processing,
            )
            )
        ## label path for file
        self.lbl_upload_file_path = tk.Label(
            master=self.root,
            text=self.upload_file_path,
            bg="black", fg="white",
            width=(len(self.upload_file_path) + 4),
            height=1
            )
        ## text widget for editable upload file path
        self.txt_editable_file_path = tk.Text(
            master=self.root,
            width = 60,
            exportselection=0, ## otherwise only any accidentally selected text will be captured
            height=3,
            wrap=tk.WORD,
            state=tk.NORMAL
            )
        self.txt_editable_file_path.insert(tk.END, self.path_editable)
        ## label for query explanation
        self.lbl_query_explanation = tk.Label(
            master=self.root,
            text=self.queries_explained,
            bg="blue", fg="white",
            width=150,
            height=10,
            justify=tk.LEFT,
            )
        ## label for query data
        self.lbl_query_data_fixed = tk.Label(
            master=self.root,
            text=self.query_data_fixed,
            bg="black", fg="white",
            width=len(self.query_data_fixed) + 2,
            height=3
            )
        ## text widget for query data entry
        self.txt_editable_query_input = tk.Text(
            master=self.root,
            width = 60,
            exportselection=0, ## otherwise only any accidentally selected text will be captured
            height=3,
            wrap=tk.WORD,
            state=tk.NORMAL
            )
        self.txt_editable_file_path.insert(tk.END, self.query_input_data)
        ## button query 1
        self.but_query_1 = tk.Button(
            master=self.root,
            text=self.query_1_msg,
            bg="green", fg="white",
            relief=tk.RAISED,
            width=(len(self.query_1_msg) + 4),
            height=1,
            borderwidth=7,
            command=partial(
                self.do_query_1_processing,
            )
            )
        ## button query 2
        self.but_query_2 = tk.Button(
            master=self.root,
            text=self.query_2_msg,
            bg="green", fg="white",
            relief=tk.RAISED,
            width=(len(self.query_2_msg) + 4),
            height=1,
            borderwidth=7,
            command=partial(
                self.do_query_2_processing,
            )
            )
        ## button query 3
        self.but_query_3 = tk.Button(
            master=self.root,
            text=self.query_3_msg,
            bg="green", fg="white",
            relief=tk.RAISED,
            width=(len(self.query_3_msg) + 4),
            height=1,
            borderwidth=7,
            command=partial(
                self.do_query_3_processing,
            )
            )
        ## label for results fixed
        self.lbl_result_fixed = tk.Label(
            master=self.root,
            text=self.result_fixed_text,
            bg="black", fg="white",
            width=len(self.result_fixed_text) + 2,
            height=10
            )
        ## label for results variable
        self.lbl_results = tk.Label(
            master=self.root,
            text=self.result,
            bg="green", fg="white",
            width=60,
            height=25,
            wraplength=400,
            justify=tk.LEFT,
            )
        ## label for status
        self.lbl_status = tk.Label(
            master=self.root,
            textvariable=self.status_msg,
            bg="yellow", fg="black",
            width=60,
            height=1
            )

        ## setup the grid
        ## button upload to Neo
        self.but_upload_to_neo.grid(
            row=0, column=0,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label path for file
        self.lbl_upload_file_path.grid(
            row=0, column=1,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## text widget for editable upload file path
        self.txt_editable_file_path.grid(
            row=0, column=2,
            rowspan=1, columnspan=6,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label for query explanation
        self.lbl_query_explanation.grid(
            row=1, column=0,
            rowspan=1, columnspan=8,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label for query data
        self.lbl_query_data_fixed.grid(
            row=2, column=0,
            rowspan=1, columnspan=2,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## text widget for query data entry
        self.txt_editable_query_input.grid(
            row=2, column=2,
            rowspan=1, columnspan=6,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## button query 1
        self.but_query_1.grid(
            row=3, column=0,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## button query 2
        self.but_query_2.grid(
            row=3, column=2,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## button query 3
        self.but_query_3.grid(
            row=3, column=6,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label for results fixed
        self.lbl_result_fixed.grid(
            row=4, column=0,
            rowspan=1, columnspan=1,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label for results variable
        self.lbl_results.grid(
            row=4, column=1,
            rowspan=1, columnspan=7,
            sticky="nsew",
            padx=5, pady=5,
        )
        ## label for status
        self.lbl_status.grid(
            row=5, column=0,
            rowspan=1, columnspan=8,
            sticky="nsew",
            padx=5, pady=5,
        )
        return

    def do_query_1_processing(self, ):
        #print(f"\n\nQuery 1 processing started\n\n")
        my_print_and_log(f"\nQuery 1 processing started\n", _only_log=True)
        self.query_input_data = self.txt_editable_query_input.get('1.0','end-1c').strip()
        node_requested = self.query_input_data
        #print(f"\nNode requested: {node_requested}\n")
        my_print_and_log(f"\nNode requested: {node_requested}\n", _only_log=True)

        ## get graph object - but do not exit program if problem
        graph, gph_msg = make_neo4j_connection(_on_fail_return=True)
        if graph is None:
            myStr = "\n".join([
                f"\nERROR: For Query 1, could not eastablish connnection to neo4j.",
                f"Error message :: {gph_msg}",
                ])
            my_print_and_log(myStr)
            self.status_msg.set(f"Failed to connect to Neo4j for Query 1.")
            self.lbl_results.configure(
                text=self.result,
            )
            self.root.update_idletasks()
            return
        ## query neo4j
        stmt20_query_1 = r'MATCH (n1:xxxxxxx) WITH COUNT (DISTINCT n1) as node_count RETURN node_count'
        for possible_node in ['Review', 'Entity', 'Flavor']:
            if possible_node.lower() == node_requested.lower():
                stmt20_query_1 = stmt20_query_1.replace('xxxxxxx', possible_node)
                #my_print_and_log(f"\nstmt20_query_1 updated to: {stmt20_query_1}\n")
                try:
                    tx = graph.begin()
                    # run the query 1
                    res_q1 = tx.run(stmt20_query_1, parameters={
                        '_node_type_label': node_requested,
                        })
                    res_q1 = list(res_q1)
                    res_q1 = res_q1[0]['node_count']
                    self.result = f"Found {res_q1} nodes of Label={node_requested}"
                    #my_print_and_log(f"\nQuery 1 run successfully. Result =\n{type(res_q1)},\n{res_q1}\n")
                    self.status_msg.set(f"Query 1 run successfully. Ready for more input.")
                except Exception as neo_query_error:
                    myStr = "\n".join([
                        f"\nERROR: Problem running Query 1.",
                        f"Error message :: {neo_query_error}",
                        ])
                    my_print_and_log(myStr)
                    self.status_msg.set(f"Query 1 failed. Error:: {neo_query_error}.")
                    self.result = f"---------------"
                ## break to ensure the else of the for loop is not executed
                break
        else:
            ## will be executed only if all entries of the for loop are cyceld through without a break
            self.status_msg.set(f"Query 1 - invalid Label provided.")
            self.result = f"---------------"
        self.lbl_results.configure(
            text=self.result,
        )
        self.root.update_idletasks()
        return
    
    def do_query_2_processing(self, ):
        #print(f"\n\nQuery 2 processing started\n\n")
        my_print_and_log(f"\nQuery 2 processing started\n", _only_log=True)
        self.query_input_data = self.txt_editable_query_input.get('1.0','end-1c').strip()
        try:
            reqd_min_words, reqd_min_senti_score = self.query_input_data.split(',')
            reqd_min_words = int(reqd_min_words)
            reqd_min_senti_score = float(reqd_min_senti_score)
        except Exception as query2_invalid_data:
            self.status_msg.set(f"Query 2 - invalid data provided. Expected an interger followed by comma followed by float e.g. 20,0.1")
            self.result = f"---------------"
            self.lbl_results.configure(
                text=self.result,
            )
            self.root.update_idletasks()
            return
        
        ## get graph object - but do not exit program if problem
        graph, gph_msg = make_neo4j_connection(_on_fail_return=True)
        if graph is None:
            myStr = "\n".join([
                f"\nERROR: For Query 2, could not eastablish connnection to neo4j.",
                f"Error message :: {gph_msg}",
                ])
            my_print_and_log(myStr)
            self.status_msg.set(f"Failed to connect to Neo4j for Query 2.")
            self.result = f"---------------"
            self.lbl_results.configure(
                text=self.result,
            )
            self.root.update_idletasks()
            return
        
        ## query neo4j
        stmt21_query_2 = r"MATCH (rv1:Review) WHERE rv1['count_words'] > $_in_min_words AND rv1['senti_score'] > $_in_min_senti_score WITH COUNT (rv1) AS review_node_count RETURN review_node_count"
        try:
            tx = graph.begin()
            # run the query 2
            res_q2 = tx.run(stmt21_query_2, parameters={
                '_in_min_words': reqd_min_words,
                '_in_min_senti_score': reqd_min_senti_score,
            })
            #print(f"\nQuery 2 run successfully. Result =\n{type(res_q2)},\n{res_q2}\n\n")
            res_q2 = list(res_q2)
            res_q2 = res_q2[0]['review_node_count']
            self.result = f"Found {res_q2} Review nodes with mininum words={reqd_min_words} and minimum sentiment score={reqd_min_senti_score}"
            self.status_msg.set(f"Query 2 run successfully. Ready for more input.")
        except Exception as neo_query_error:
            myStr = "\n".join([
                f"\nERROR: Problem running Query 2.",
                f"Error message :: {neo_query_error}",
                ])
            my_print_and_log(myStr)
            self.status_msg.set(f"Query 2 failed. Error:: {neo_query_error}.")
            self.result = f"---------------"
        self.lbl_results.configure(
            text=self.result,
        )
        self.root.update_idletasks()
        return
    
    def do_query_3_processing(self, ):
        #print(f"\n\nQuery 3 processing started\n\n")
        my_print_and_log(f"\nQuery 3 processing started\n", _only_log=True)
        self.query_input_data = self.txt_editable_query_input.get('1.0','end-1c').strip()
        try:
            reqd_flavors_list = [flav.strip() for flav in self.query_input_data.split(',')]
            my_print_and_log(f"\nUser input required flavors=\n{reqd_flavors_list}\n")
        except Exception as query2_invalid_data:
            self.status_msg.set(f"Query 3 - invalid data provided. Expected names of flavors separated by comma e.g. cherry,coffee")
            self.result = f"---------------"
            self.lbl_results.configure(
                text=self.result,
            )
            self.root.update_idletasks()
            return
        
        ## get graph object - but do not exit program if problem
        graph, gph_msg = make_neo4j_connection(_on_fail_return=True)
        if graph is None:
            myStr = "\n".join([
                f"\nERROR: For Query 3, could not eastablish connnection to neo4j.",
                f"Error message :: {gph_msg}",
                ])
            my_print_and_log(myStr)
            self.status_msg.set(f"Failed to connect to Neo4j for Query 3.")
            self.result = f"---------------"
            self.lbl_results.configure(
                text=self.result,
            )
            self.root.update_idletasks()
            return
        
        ## query neo4j
        stmt22_query_3 = r"MATCH (rv1:Review)-[rel1:HAS_FLAVOR]-(f1:Flavor) WHERE f1['name'] in $_in_flav_list RETURN f1['name'], rv1['name']"
        try:
            tx = graph.begin()
            # run the query 3
            res_q3 = tx.run(stmt22_query_3, parameters={
                '_in_flav_list': reqd_flavors_list,
            })
            #print(f"\nQuery 3 run successfully. Result =\n{type(res_q3)},\n{res_q3}\n\n")
            res_q3 = list(res_q3)
            #final_res = ""
            #final_res = "\n".join([f'Review node {res[1]} -HAS_FLAVOR- {res[0]}' for res in res_q3])
            
            rev_nodes_set = set([res[1] for res in res_q3])
            rev_nodes_names = ", ".join(list(rev_nodes_set))
            final_res = "\n".join([
                f"Count of Review nodes found with one or more flavors of {self.query_input_data} = {len(rev_nodes_set)}",
                f"Name of the Review nodes: {rev_nodes_names}",
            ])

            my_print_and_log(f"final_res =\n{final_res}\n")
            self.result = final_res
            #print(f"\nQuery 3 run successfully. Result =\n{type(res_q3)},\n{res_q3}\n\n")
            my_print_and_log(f"\nQuery 3 run successfully.")
            self.status_msg.set(f"Query 3 run successfully. Ready for more input.")
        except Exception as neo_query_error:
            myStr = "\n".join([
                f"\nERROR: Problem running Query 3.",
                f"Error message :: {neo_query_error}",
                ])
            my_print_and_log(myStr)
            self.status_msg.set(f"Query 3 failed. Error:: {neo_query_error}.")
            self.result = f"---------------"
        self.lbl_results.configure(
            text=self.result,
        )
        self.root.update_idletasks()
        return
    
    def do_upload_file_neo_processing(self, ):
        self.path_editable = self.txt_editable_file_path.get('1.0','end-1c').strip()
        my_print_and_log(f"\nButton to upload file pressed\nFile to upload: {self.path_editable}\n")
        self.status_msg.set(f"Processing input file....")
        self.root.update_idletasks()
        ## check file exists
        if not os.path.isfile(self.path_editable):
            my_print_and_log(f"\nERROR: User specified file does not exist.\n")
            self.status_msg.set(f"Input file not found, re-enter please....")
            self.root.update_idletasks()
            return
        
        ## attempt loading
        try:
            with open(self.path_editable, 'r') as f:
                extracted_text = f.read()
        except Exception as upload_file_error:
            my_print_and_log(f"\nERROR: User specified file could not be opened\nError message: {upload_file_error}")
            self.status_msg.set(f"Error accessing the upload file, recheck.")
            self.root.update_idletasks()
            return
        
        ## get features into the data structure to populate for neo4j flat files
        data_neo_one_file = list()
        get_features_set1(
            os.path.basename(
                self.path_editable).split(".")[0], extracted_text, data_neo_one_file,
                self.nlp, self.punctuations, self.stopwords,
                self.flag_ner, self.flag_topic, self.flag_sentiment
                )
        my_print_and_log(f"\nUser input processed and data structure is:\n{data_neo_one_file}\n", _only_log=True)
        ## write as json file
        try:
            json_path = self.OP_DIR + 'user_input_temp_neo_data.json'
            with open(json_path, "w") as f:
                json.dump(data_neo_one_file, f)
            my_print_and_log(f"\nUser input processed data successfully dumped to json file: {json_path}\n")
        except Exception as neo_data_save_error:
            my_print_and_log(f"\n\nERROR: User data not saved to json file after feature extraction.\nError message: {neo_data_save_error}\n")
            self.status_msg = f"Error saving user input to json file."
        ## do actual upload to neo4j db
        load_neo4j_from_json(json_path, _clear_graph=False)
        self.status_msg.set(f"Processed input file and uploaded to Neo4j successfully.")
        self.root.update_idletasks()

def run_gui(_nlp, _punctuations, _stopwords, _flag_ner, _flag_topic, _flag_sentiment, _op_dir):
    o_wine_tool_window = c_wine_tool_window(_nlp, _punctuations, _stopwords, _flag_ner, _flag_topic, _flag_sentiment, _op_dir)
    o_wine_tool_window.root.mainloop()
    return

def main():
    HOME = os.getcwd()
    IP_DIR = os.path.join(HOME, 'inData') + r'/' ## where the individual files have already been saved
    OP_DIR = os.path.join(HOME, 'outData') + r'/' ## folder to store json
    TEMP_DIR = os.path.join(HOME, 'tempDir') + r'/' ## log files and any temporary files

    ## create temp folder if does not exist
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
        print(f"\nCreated temp folder:: {TEMP_DIR}\n")

    ## setup logging file -   levels are DEBUG , INFO , WARNING , ERROR , CRITICAL
    logging.basicConfig(level=logging.INFO, filename=TEMP_DIR + 'LOG_load_neo_show_gui.log',                       \
        filemode='w', format='LOG_LEVEL %(levelname)s : %(asctime)s :: %(message)s')
    
    # set flags to specify the feature creation
    flag_ner=True
    flag_topic=False
    flag_sentiment=True

    nlp = spacy.load("en_core_web_lg")
    nlp.add_pipe('spacytextblob')

    punctuations = string.punctuation
    stopwords = list(STOP_WORDS)

    ## create output directory if does not exist
    if not os.path.exists(OP_DIR):
        os.mkdir(OP_DIR)
    
    ## setup cla
    argparser = argparse.ArgumentParser(
        description='Parameters to run this program.')
    argparser.add_argument(
        '-reloadNeo',
        '--reload_and_clear_neo',
        default='N',
        choices=['Y', 'N', 'y', 'n'],
        help='Flag to first reload data to Neo4j from input files. Note: If yes, will also clear the graph first.')
    argparser.add_argument(
        '-uploadLimit',
        '--upload_neo_limit',
        type=int,
        default=100,
        help='Number of input files to process and upload data to Neo4j. Enter a number from 1 to the number of input files available.')
    args = argparser.parse_args()

    ## extract cla args
    RELOAD_TO_NEO = args.reload_and_clear_neo
    LIMIT_UPLOAD_TO_NEO = args.upload_neo_limit

    ## if reloading is required, then check input folder exists, number of files present, upload limit paramter value is valid
    if RELOAD_TO_NEO.lower() == 'y':
        ## check input files directory exists and count number of files is more than 0
        if not os.path.exists(IP_DIR):
            myStr = "\n".join([
                f"\nFATAL ERROR: Input folder not found:: {IP_DIR}",
                f"EXITING with error code 30\n",
                ])
            my_print_and_log(myStr, "error")
            exit(30)
        else:
            num_inp_files = len(os.listdir(IP_DIR))
            my_print_and_log(f"num_inp_files = {num_inp_files}")
            
            ## check files present
            if num_inp_files == 0:
                myStr = "\n".join([
                    f"\nFATAL ERROR: No files found in input folder:: {IP_DIR}",
                    f"EXITING with error code 35\n",
                    ])
                my_print_and_log(myStr, "error")
                exit(35)
            ## check upload limit paramter
            if not (0 < LIMIT_UPLOAD_TO_NEO <= num_inp_files):
                myStr = "\n".join([
                    f"\nFATAL ERROR: Invalid value for 'upload_neo_limit' parameter:: {LIMIT_UPLOAD_TO_NEO}",
                    f"Only {num_inp_files} files present in input folder {IP_DIR}",
                    f"enter a number from 1 to {num_inp_files}",
                    f"EXITING with error code 40\n",
                    ])
                my_print_and_log(myStr, "error")
                exit(40)
    ## show and log the cla
    myStr = "\n".join([
        f"\nCommand line arguments checked. Proceeding with these values:",
        f"reloadNeo: {RELOAD_TO_NEO}",
        f"uploadLimit: {LIMIT_UPLOAD_TO_NEO}",
        ])
    my_print_and_log(myStr, "info")
    
    ## load data to neo after clearing whole graph - only if flag is true
    if RELOAD_TO_NEO.lower() == 'y':
        my_print_and_log(f"\nProcessing only {LIMIT_UPLOAD_TO_NEO} files....\n")

        extracted_text = list() # list to hold the review text
        idx = 0
        for fname in glob.glob(IP_DIR + r'f*.txt'):
            idx += 1
            if idx > LIMIT_UPLOAD_TO_NEO:
                break
            with open(fname, 'r') as f:
                extracted_text.append([os.path.basename(fname), f.read()])
        my_print_and_log(f"\nExtracted data from {idx} input files....\n")
        
        df_ext = pd.DataFrame(extracted_text, columns=['fname', 'review'])
        df_ext['proc_review'] = ""
        my_print_and_log(f"\nLoaded files to pandas dataframe. Total rows = {len(df_ext)}\n")

        ## data structure to populate for neo4j flat files
        data_neo = list()
        ## get features
        for idx, row in df_ext.iterrows():
            fname, review_text = row[0], row[1]
            #print(f"{fname}\n{review_text}\n{'----------------'}")
            proc_text = get_features_set1(fname, review_text, data_neo, nlp, punctuations, stopwords, flag_ner, flag_topic, flag_sentiment)
            df_ext.at[idx, 'proc_review'] = proc_text
        
        ## write intermediate json file
        try:
            json_path = OP_DIR + 'temp_neo_data.json'
            with open(json_path, "w") as f:
                json.dump(data_neo, f)
            print(f"\nData successfully dumped to json file: {json_path}\n")
        except Exception as neo_data_save_error:
            myStr = "\n".join([
                f"\nFATAL ERROR: Problem saving data to file for Neo4j loading stage.",
                f"Error message :: {neo_data_save_error}",
                f"Tried saving here =\n{json_path}",
                f"EXITING with error code 50",
                ])
            my_print_and_log(myStr, "error")
            exit(50)
        
        # load the files to neo4j from intermediate json file just created
        load_neo4j_from_json(_data_file=json_path, _clear_graph=True)
    else:
        my_print_and_log(f"\nNo reloading to Neo required.\n\n")

    my_print_and_log(f"\nStarting GUI logic...\n")
    run_gui(nlp, punctuations, stopwords, flag_ner, flag_topic, flag_sentiment, OP_DIR)

    my_print_and_log(f"\n\n\tDone\n")

if __name__ == "__main__":
    main()




