import enum
import argparse
import logging
import pandas

class FileFormat(enum.Enum):
    csv=1
    excel=2

def merge(file1, file2, output, join, keys1, keys2, sortColumns, fileType):
    df1 = pandas.read_csv(file1)
    df2 = pandas.read_csv(file2)
     
    result = df1.merge(df2, left_on=keys1, right_on=keys2, how=join)
    
    if (sortColumns):
        result = result.sort_values(by=sortColumns)
    
    if (fileType == FileFormat.csv):    
        result.to_csv(output, index=False)
    else:
        result.to_excel(output, sheet_name='Sheet1', index=False)

def parseArguments():
    parser = argparse.ArgumentParser(description='Join')
    parser.add_argument('-j', '--join', dest='joinType', action='store',
                        type=str, default='leftOuter', help='join type: inner or leftOuter')
    parser.add_argument('-f', '--files', dest='files', action='append',
                        type=str, required=True, help='join two files')
    parser.add_argument('-o', '--output', dest='output', action='store',
                        type=str, default='out.csv', help='merged file name')
    parser.add_argument('-l', '--leftKeys', dest='leftKeys', action='append',
                        type=str, required=True, help='keys in first source file')
    parser.add_argument('-r', '--rightKeys', dest='rightKeys', action='append',
                        type=str, required=True, help='keys in second source file')
    parser.add_argument('-s', '--sort', dest='sortColumns', action='append',
                        type=str, help='columns used for sorting')
    parser.add_argument('-x', '--excel', dest='fileType', action='store_const',
                        const=FileFormat.excel, default=FileFormat.csv, 
                        help='file type: csv or excel')
    args = parser.parse_args()

    assert len(args.files) == 2, "mismatched number of files"
    assert len(args.leftKeys) == len(args.rightKeys), "mismatched number of keys"
    return args

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    joinType = 'inner' if args.joinType == 'inner' else 'left'
    merge(args.files[0], args.files[1], args.output, joinType,
          args.leftKeys, args.rightKeys, args.sortColumns,
          args.fileType)
