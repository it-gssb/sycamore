import enum
import argparse
import os
import pathlib
import logging
import re
import pandas as pd

class FileFormat(enum.Enum):
    raw=1
    final=2

# Column Names of Result
FIRST_NAME = 'StudentFirstName'
LAST_NAME  = 'StudentLastName'
READING    = 'Reading'
LISTENING  = 'Listening_and_Viewing'
TOTAL      = 'Points_out_of_100'
PERCENTILE = 'Percentile'
LEVEL      = 'Level'
AWARD      = 'Award'
SCHOOL     = 'Schule'

RAW_RECORD_IDX   = 7
FINAL_RECORD_IDX = 2

LEVEL_REG_EXPR = "\d{4} Level (\d) \w+"


MAP_FINAL = {'First Name' : FIRST_NAME, 'Last Name' : LAST_NAME, 
             'ReadingRaw %ile' : READING,
             'Listening and ViewingRaw %ile' : LISTENING,
             'Total RawScore' : TOTAL, 
             'Percentile Total Group' : PERCENTILE}

def findHtmlFiles(dirName):
    return map(lambda p: p, pathlib.Path(dirName).rglob('*.html'))

def addFilledColumn(df, name, value):
    levelColumn = [value] * len(df.index)
    df[name] = levelColumn

#
# Methods to process data frames that contain the initial, raw data
# of the ATTG test that were included in the saved AATG HTML report.
#

def extractLevel(columns):
    level = 0
    for column in columns:
        l = re.match(LEVEL_REG_EXPR, column[1])
        if (l):
            level = l.groups()[0]
            break

    return level

def createFirstAndLastNameRows(df, sourceColumnName):
    firstNames = []
    lastNames = []
    rows = df[sourceColumnName]
    for row in rows:
        splitByComma = row.split(', ')
        firstNames.append(splitByComma[1].strip())
        lastNames.append(splitByComma[0].strip())
    return (firstNames, lastNames)

def stripByFifty(rows):
    newValues = []
    for row in rows:
        splitBySlash = row.split('/')
        value = 0
        if len(splitBySlash) == 2:
            value = splitBySlash[0]
        newValues.append(value)

    return newValues

def renameRawColumnName(name):
    newName = name
    if name.startswith('Points'):
        newName='Points_out_of_100'
    elif 'Reading' in name:
        newName = READING
    elif 'Listen' in name:
        newName = LISTENING

    return newName

def renameRawColumnNames(columns):
    return map(lambda c: renameRawColumnName(c[1]), columns)

def loadRawHtml(html_file):
    df1 = pd.read_html(html_file)
    df = df1[RAW_RECORD_IDX]

    # extract level reference before modifying column names
    level = extractLevel(df.columns)
    
    # modify column names to standard names
    df.columns = renameRawColumnNames(df.columns)

    # strip '/50' from the reading and listing scores
    newReadingRows   = stripByFifty(df[READING])
    df[READING] = newReadingRows
    newListeningRows = stripByFifty(df[LISTENING])
    df[LISTENING] = newListeningRows

    # Split Student name into first and last names
    nameLists = createFirstAndLastNameRows(df, 'Student')
    df.insert(0, FIRST_NAME, nameLists[0], True)
    df.insert(1, LAST_NAME , nameLists[1], True)

    # add level column with determined level value
    addFilledColumn(df, LEVEL, level)
    addFilledColumn(df, PERCENTILE, 'na')
    addFilledColumn(df, AWARD, ' ')
    addFilledColumn(df, SCHOOL, 'German Saturday School Boston')

    return df

#
# Methods to process data frames that contain the final, enriched data
# of the ATTG test that were included in the saved AATG HTML report.
# The data contains percentile information that will be included in the 
# final report that is sent to parents.
#

def renameFinalColumnName(name, renameMap):
    newName = name
    lookup = renameMap.get(name)
    if lookup:
        newName = lookup

    return newName

def renameFinalColumnNames(columns, renameMap):
    return map(lambda c: renameFinalColumnName(c, renameMap), columns)

def loadFinalHtml(html_file):
    df1 = pd.read_html(html_file)
    df  = df1[FINAL_RECORD_IDX]
    
    # modify column names to standard names
    df.columns = renameFinalColumnNames(df.columns, MAP_FINAL)

    # # add level column with determined level value
    addFilledColumn(df, SCHOOL, 'German Saturday School Boston')

    return df

#
# Command line processing
#

def parseArguments():
    parser = argparse.ArgumentParser(description='convert quia AATG HTML reports into CSV file')
    parser.add_argument('-r', '--raw', dest='type', action='store_const',
                        const=FileFormat.raw, default=FileFormat.final, 
                        help='Indicates that HTML document defines the raw or final report format')
    parser.add_argument('-f', '--files', dest='files', action='append',
                        type=str, required=True,
                        help='Quia ATTG HTML report file location or directory with HTML reports.')
    parser.add_argument('-o', '--output', dest='output', action='store',
                        type=str, default='out.csv', 
                        help='CSV file containing reformatted data of HTML reports.')
    args = parser.parse_args()

    assert len(args.files) == 1, "mismatched number of files"
    return args


if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    
    process = loadFinalHtml
    if args.type == FileFormat.raw:
        process = loadRawHtml

    if not os.path.isdir(args.files[0]):
        df = process(pathlib.Path(args.files[0]))
    else:
        paths = findHtmlFiles(args.files[0])
        dataFrames = []
        for path in paths:
            dataFrames.append(process(path))

        df = pd.concat(dataFrames, ignore_index=True)

    # save relevant data frames into CSV files
    df.to_csv(args.output, index=False,
              columns = [FIRST_NAME, LAST_NAME, LISTENING, READING,
                         TOTAL, PERCENTILE, AWARD, LEVEL, SCHOOL])
