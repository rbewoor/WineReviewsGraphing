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

## custom packages
from utils.util_functions_1 import my_print_and_log

def main():
    HOME = os.getcwd()
    OP_DIR = os.path.join(HOME, 'inData') + r'/' ## where the individual files will be saved
    TEMP_DIR = os.path.join(HOME, 'tempDir') + r'/' ## log files and any temporary files

    ## create temp folder if does not exist
    if not os.path.exists(TEMP_DIR):
        os.mkdir(TEMP_DIR)
    print(f"\nCreated temp folder:: {TEMP_DIR}\n")

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
        help='Number of csv file rows to process and create the individual files. Enter a number less than 129970.')
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
    if CSV_FILES_LIMIT < 1 or CSV_FILES_LIMIT > 129970:
        myStr = "\n".join([
            f"\nFATAL ERROR: Invalid input for csvRowsLimit, enter a number from 1 to 129970",
            f"EXITING with error code 55\n",
            ])
        my_print_and_log(myStr, "error")
        exit(55)
    ## create output directory if does not exist else error out
    if not os.path.exists(OP_DIR):
        os.mkdir(OP_DIR)
    else:
        myStr = "\n".join([
            f"\nFATAL ERROR: Output directory already exists, please manually delete it and re-run: {OP_DIR}",
            f"EXITING with error code 60\n",
            ])
        my_print_and_log(myStr, "error")
        exit(60)
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
        for idx, row in df.iterrows():
            if cnt_files_out > CSV_FILES_LIMIT:
                break
            else:
                with open(OP_DIR + 'f' + str(cnt_files_out).zfill(4) + '.txt', 'w') as f:
                    f.write(row[0])
                cnt_files_out += 1
        my_print_and_log(f"\nCreated ** {cnt_files_out -1} ** files here: {OP_DIR}\n")
    except Exception as load_or_process_error:
        myStr = "\n".join([
            f"\nFATAL ERROR: Problem loading CSV data to dataframe or later writing to files.",
            f"Error message: {load_or_process_error}",
            ])
        my_print_and_log(myStr, "error")

    print(f"\n\t\tDone.\n")

if __name__ == "__main__":
    main()