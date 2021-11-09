import argparse
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

        rest = SycamoreRest.Extract(schoolId=self.schoolId, token=args.securityToken)
        self.sycamore = SycamoreCache.Cache(rest=rest)


    def generate(self):
        #print(self.generateStudents())
        self.sycamore.saveToFiles(self.cacheDir)

        self.sycamore2 = SycamoreCache.Cache(sourceDir=self.cacheDir)
        self.sycamore2.compare(self.sycamore)


    def generateStudents(self):
        cleverStudents = pandas.DataFrame(columns=[
            'Student_id',
            'School_id',
            'Username',
            'Student_number',
            'Dob',
            'Grade',
            'State_id',
            'Student_email',
            'First_name',
            'Last_name',
            'Middle_name',
            'Status',
            ])

        for index, sycStudent in self.sycamore.getStudents().iterrows():
            sycStudentDetails = self.sycamore.getStudent(sycStudent['ID'])

            cleverStudent = {}
            cleverStudent['Student_id'] = sycStudent['ID']
            cleverStudent['School_id'] = self.schoolId
            cleverStudent['Username'] = Generators.createStudentEmailAddress(
                sycStudent['FirstName'], sycStudent['LastName'])
            cleverStudent['Student_number'] = sycStudent['ExternalID']
            cleverStudent['Dob'] = sycStudentDetails['DOB']
            cleverStudent['Grade'] = sycStudentDetails['Grade']
            cleverStudent['State_id'] = sycStudentDetails['StateID']
            cleverStudent['Student_email'] = sycStudentDetails['Email']
            cleverStudent['First_name'] = sycStudent['FirstName']
            cleverStudent['Last_name'] = sycStudent['LastName']
            cleverStudent['Middle_name'] = ''  # TODO(osenft): Find data
            cleverStudent['Status'] = ''  # TODO(osenft): Find data
            
            cleverStudents.append(cleverStudent, ignore_index=True)

        return cleverStudents


def parseArguments():
    parser = argparse.ArgumentParser(description='Extract Family and School Data')
    parser.add_argument('--school', dest='schoolId', action='store',
                        type=int, required=True, help='Sycamore school ID')
    parser.add_argument('--token', dest='securityToken', action='store',
                        required=True, help='Sycamore security token')
    parser.add_argument('--cache', dest='cacheDir', action='store',
                        required=True, help='Cache directory')
    return parser.parse_args()

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    creator = CleverCreator(args)
    creator.generate()

