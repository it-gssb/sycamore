import argparse
import logging
import pandas
# import openpyxl # needed for Excel spreadsheet export

def merge(file1, file2, output, join, keys1, keys2):
    df1 = pandas.read_csv(file1)
    df2 = pandas.read_csv(file2)
     
    result = df1.merge(df2, left_on=keys1, right_on=keys2, how=join)
#                 .sort_values(by=['Class', 'StudentLastName', 'StudentFirstName'])
    
    result.to_csv(output)
#     result.to_excel('result.xlsx', sheet_name='Sheet1')

def parseArguments():
    parser = argparse.ArgumentParser(description='Join')
    parser.add_argument('-j', '--join', dest='joinType', action='store',
                        type=str, default='inner', help='join type: inner or leftOuter')
    parser.add_argument('-f', '--files', dest='files', action='append',
                        type=str, required=True, help='join two files')
    parser.add_argument('-o', '--output', dest='output', action='store',
                        type=str, default='out.csv', help='merged file name')
    parser.add_argument('-lk', '--leftKeys', dest='leftKeys', action='append',
                        type=str, required=True, help='keys in first source file')
    parser.add_argument('-rk', '--rightKeys', dest='rightKeys', action='append',
                        type=str, required=True, help='keys in second source file')
    args = parser.parse_args()

    assert len(args.files) == 2, "mismatched number of files"
    assert len(args.leftKeys) == len(args.rightKeys), "mismatched number of keys"
    return args

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    joinType = 'inner' if args.joinType == 'inner' else 'left'
    merge(args.files[0], args.files[1], args.output, joinType,
          args.leftKeys, args.rightKeys)
