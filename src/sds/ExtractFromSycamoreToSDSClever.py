import argparse
from datetime import datetime
import os
import pandas
import re
import logging
import sys
  
# append the path of the parent directory
sys.path.append("..")
sys.path.append(".")

from lib import Generators
from lib import SycamoreRest
from lib import SycamoreCache

class CleverCreator:

    def __init__(self, args):
        self.schoolId = args.schoolId
        self.cacheDir = args.cacheDir
        self.outputDir = args.outputDir

        rest = SycamoreRest.Extract(schoolId=self.schoolId, token=args.securityToken)
        if args.reloadData:
            self.sycamore = SycamoreCache.Cache(rest=rest)
            self.sycamore.saveToFiles(self.cacheDir)

            # Check that saved data can be reloaded and compares clean
            self.sycamore2 = SycamoreCache.Cache(sourceDir=self.cacheDir)
            self.sycamore2.compare(self.sycamore)
        else:
            self.sycamore = SycamoreCache.Cache(sourceDir=self.cacheDir)

    def generate(self):
        students = self.generateStudents()
        students.sort_index(axis='index').to_csv(
            os.path.join(self.outputDir, 'students.csv'),
            index=False,
            date_format='%m/%d/%Y')   

    def generateStudents(self):
        cleverStudents = pandas.DataFrame(columns=[
            'Student_id',
            'School_id',
            'Username',
            'Student_number',
            'Dob',
            'Grade',
            'State_id',
            'Secondary_email',
            'First_name',
            'Last_name',
            'Middle_name',
            'Status',
            ])

        for index, _sycStudent in self.sycamore.getStudents().iterrows():
            sycStudentDetails = self.sycamore.getStudent(index)

            cleverStudent = {}
            cleverStudent['Student_id'] = index
            cleverStudent['School_id'] = self.schoolId
            cleverStudent['Username'] = Generators.createStudentEmailAddress(
                sycStudentDetails['FirstName'], sycStudentDetails['LastName'])
            cleverStudent['Student_number'] = sycStudentDetails['ExtID']
            print(sycStudentDetails['Code'], sycStudentDetails['DOB'])
            cleverStudent['Dob'] = datetime.strptime(sycStudentDetails['DOB'], '%Y-%m-%d') if sycStudentDetails['DOB'] else None
            cleverStudent['Grade'] = sycStudentDetails['Grade']
            cleverStudent['State_id'] = sycStudentDetails['StateID']
            cleverStudent['Secondary_email'] = sycStudentDetails['Email']
            cleverStudent['First_name'] = sycStudentDetails['FirstName']
            cleverStudent['Last_name'] = sycStudentDetails['LastName']
            cleverStudent['Middle_name'] = ''  # TODO(osenft): Find data
            cleverStudent['Status'] = ''  # TODO(osenft): Find data

            cleverStudents = cleverStudents.append(pandas.Series(data=cleverStudent, name=index))

        return cleverStudents


def parseArguments():
    parser = argparse.ArgumentParser(description='Extract Family and School Data')
    parser.add_argument('--school', dest='schoolId', action='store',
                        type=int, required=True, help='Sycamore school ID')
    parser.add_argument('--token', dest='securityToken', action='store',
                        required=True, help='Sycamore security token')
    parser.add_argument('--cache', dest='cacheDir', action='store',
                        required=True, help='Cache directory')
    parser.add_argument('--reload', dest='reloadData', action='store_true',
                        help='Whether to reload data')
    parser.add_argument('--out', dest='outputDir', action='store',
                        required=True, help='Output directory')
    parser.set_defaults(reloadData=False)
    return parser.parse_args()

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    creator = CleverCreator(args)
    creator.generate()

