## -------------------------------------------------------------------------------------------------------------------------------------------------
## Goal: Create individual text files containing the reviews of wines.
## Dataset is a CSV file from here: https://www.kaggle.com/zynicide/wine-reviews
##   It has 129971 rows, only the required number of rows will be loaded and processed as per input parameter.
## -------------------------------------------------------------------------------------------------------------------------------------------------
## General logic flow:
## 1) Taking description column from CSV file, each description written to individual text file.
##    Automatically creates output directory called 'inData' if it does not exist. If folder already exists then throws error.
##    Files numbered from 0 onwards automatically.
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Notes on running this script:
##    1) Expects the input CSV file named 'winemag-data-130k-v2.csv' to be in the same folder. The description column of this file will be extracted.
##       If the reload to Neo flag is set true, will try to process every file in this folder.
##    2) Will create a folder called 'inData' to store the .txt files that are created with each description.
##    3) Log file is saved to the folder 'tempDir'
## -------------------------------------------------------------------------------------------------------------------------------------------------
## Command line arguments:
##    Compulsory:
##    1) wineFileLoc :: input file
##    Optional:
##    2) csvRowsLimit :: how many rows to process and create that many output files,
##                       valid values: 0 < csvRowsLimit < 129971
##                       default value=20
## Examples of running the script:   
##    python3 script-name -wineFileLoc <<'/path/to/input/csv/raw/file.csv'>> -csvRowsLimit <<limit_as_interger>>
##    e.g. python3 01_create_data_1.py -wineFileLoc '/home/rohit/PyWDUbuntu/generic/dockerUseCase2/code/winemag-data-130k-v2.csv' -csvRowsLimit 10
## -------------------------------------------------------------------------------------------------------------------------------------------------

import pandas as pd
import os
import argparse
import logging
import shutil

## custom packages
from utils.util_functions_1 import my_print_and_log

def main():
    HOME = os.getcwd()
    OP_DIR = os.path.join(HOME, 'inData') + r'/' ## where the all the individual files will be saved - except the last 5!
    OP_DIR_EXTRA = os.path.join(HOME, 'extraUserInput') + r'/' ## where 5 individual files will be saved
    TEMP_DIR = os.path.join(HOME, 'tempDir') + r'/' ## log files and any temporary files

    ## create temp folder if does not exist
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
        print(f"\nCreated temp folder:: {TEMP_DIR}\n")
    else:
        print(f"\nTemp folder already existed here: {TEMP_DIR}\n")

    ## setup logging file -   levels are DEBUG , INFO , WARNING , ERROR , CRITICAL
    logging.basicConfig(level=logging.INFO, filename=TEMP_DIR + 'LOG_create_data.log',                               \
        filemode='w', format='LOG_LEVEL %(levelname)s : %(asctime)s :: %(message)s')
    
    ## setup cla
    argparser = argparse.ArgumentParser(
        description='Parameters to run this program.')
    argparser.add_argument(
        '-wineFileLoc',
        '--wine_file_location',
        required=True,
        help='Path to raw data CSV file containing the wine reviews.')
    argparser.add_argument(
        '-csvRowsLimit',
        '--csv_rows_limit_processing',
        type=int,
        default=20,
        help='Number of csv file rows to process and create the individual files. Valid values: integer in the range 9 < value < 129970.')
    args = argparser.parse_args()

    ## extract cla args
    wineFileLoc = args.wine_file_location               ## -wineFileLoc      parameter
    CSV_FILES_LIMIT = args.csv_rows_limit_processing    ## -csvRowsLimit     parameter

    ## check input file exists else throw error
    if not os.path.exists(wineFileLoc):
        myStr = "\n".join([
            f"\nFATAL ERROR: Did not find input CSV file for processing here: {wineFileLoc}",
            f"EXITING with error code 50\n",
            ])
        my_print_and_log(myStr, "error")
        exit(50)
    ## check value for csv file limit
    if not isinstance(CSV_FILES_LIMIT, int) or CSV_FILES_LIMIT < 10 or CSV_FILES_LIMIT > 129969:
        myStr = "\n".join([
            f"\nFATAL ERROR: Invalid input for csvRowsLimit, enter an integer in the range 9 < value < 129970.",
            f"EXITING with error code 55\n",
            ])
        my_print_and_log(myStr, "error")
        exit(55)
    ## create output directory if does not exist else delete all files in the directory
    if not os.path.exists(OP_DIR):
        os.mkdir(OP_DIR)
    else:
        for existing_f in os.listdir(OP_DIR):
            f_path = os.path.join(OP_DIR, existing_f)
            try:
                os.remove(f_path)
            except Exception as op_dir_clearing_error:
                myStr = "\n".join([
                    f"\nFATAL ERROR: Output directory = {OP_DIR} already existed.\n",
                    f"Problem while attempting to clear exisiting files, please manually delete them and re-run.\n",
                    f"Error message: {op_dir_clearing_error}\n"
                    f"EXITING with error code 60\n",
                    ])
                my_print_and_log(myStr, "error")
                exit(60)
        my_print_and_log(f"\nCleared any existing files in Output directory = {OP_DIR}")
    ## create output directory EXTRA if does not exist else delete all files in the directory
    if not os.path.exists(OP_DIR_EXTRA):
        os.mkdir(OP_DIR_EXTRA)
    else:
        for existing_f in os.listdir(OP_DIR_EXTRA):
            f_path = os.path.join(OP_DIR_EXTRA, existing_f)
            try:
                os.remove(f_path)
            except Exception as op_dir_extra_clearing_error:
                myStr = "\n".join([
                    f"\nFATAL ERROR: Output directory = {OP_DIR_EXTRA} already existed.\n",
                    f"Problem while attempting to clear exisiting files, please manually delete them and re-run.\n",
                    f"Error message: {op_dir_extra_clearing_error}\n"
                    f"EXITING with error code 65\n",
                    ])
                my_print_and_log(myStr, "error")
                exit(65)
        my_print_and_log(f"\nCleared any existing files in Output directory Extra = {OP_DIR_EXTRA}")
    
    ## show and log the cla
    myStr = "\n".join([
        f"\nCommand line arguments checked. Proceeding with these values:",
        f"wineFileLoc: {wineFileLoc}",
        f"CSV_FILES_LIMIT: {CSV_FILES_LIMIT}",
        ])
    my_print_and_log(myStr, "info")

    ## load the csv to dataframe and process
    try:
        df = pd.read_csv(wineFileLoc, usecols=['description'], nrows=CSV_FILES_LIMIT)
        my_print_and_log(f"\nLoaded dataframe from file: {wineFileLoc}\nTotal rows in dataframe = {len(df)}\n")

        cnt_files_out = 1
        limit_op_dir = CSV_FILES_LIMIT - 5 # all except last 5 files to the op_dir, last 5 files to op_dir_extra
        for idx, row in df.iterrows():
            if cnt_files_out > CSV_FILES_LIMIT:
                break
            elif cnt_files_out <= limit_op_dir:
                with open(OP_DIR + 'f' + str(cnt_files_out).zfill(4) + '.txt', 'w') as f:
                    f.write(row[0])
            else:
                with open(OP_DIR_EXTRA + 'f' + str(cnt_files_out).zfill(4) + '.txt', 'w') as f:
                    f.write(row[0])
            cnt_files_out += 1
        myStr = "\n".join([
            f"\nCreated ** {cnt_files_out -1 - 5} ** files here: {OP_DIR}",
            f"Created ** {5} ** files here: {OP_DIR_EXTRA}",
            ])
        my_print_and_log(myStr, "info")
    except Exception as load_or_process_error:
        myStr = "\n".join([
            f"\nFATAL ERROR: Problem loading CSV data to dataframe or later writing to files.",
            f"Error message: {load_or_process_error}",
            f"EXITING with error code 100\n",
            ])
        my_print_and_log(myStr, "error")
        exit(100)

    print(f"\n\t\tDone.\n")

if __name__ == "__main__":
    main()