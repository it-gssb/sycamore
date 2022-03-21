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

        sections = self.generateSections()
        sections.sort_index(axis='index').to_csv(
            os.path.join(self.outputDir, 'sections.csv'),
            index=False,
            date_format='%m/%d/%Y')

    def _strToDate(self, dateStr: str) -> datetime.date:
        return datetime.strptime(dateStr, '%Y-%m-%d') if dateStr else None

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
            cleverStudent['Dob'] = self._strToDate(sycStudentDetails['DOB'])
            cleverStudent['Grade'] = Generators.createGrade(sycStudentDetails['Grade'])
            cleverStudent['State_id'] = sycStudentDetails['StateID']
            cleverStudent['Secondary_email'] = sycStudentDetails['Email']
            cleverStudent['First_name'] = sycStudentDetails['FirstName']
            cleverStudent['Last_name'] = sycStudentDetails['LastName']
            cleverStudent['Middle_name'] = ''  # TODO(osenft): Find data
            cleverStudent['Status'] = ''  # TODO(osenft): Find data

            cleverStudents = cleverStudents.append(pandas.Series(data=cleverStudent, name=index))

        return cleverStudents

    def _getCurrentYear(self):
        for index, year in self.sycamore.getYears().iterrows():
            if year['Current'] == '1':
                return self.sycamore.getYear(index)
        return None

    def generateSections(self):
        currentYear = self._getCurrentYear()

        cleverSections = pandas.DataFrame(columns=[
            'Section_id',
            'School_id',
            'Teacher_id',
            'Name',
            'Term_name',
            'Term_start',
            'Term_end',
            'Course_name',
            'Subject',
            'Period',
            'Status',
            ])

        for index, sycClass in self.sycamore.getClasses().iterrows():
            cleverSection = {}
            cleverSection['Section_id'] = index
            cleverSection['School_id'] = self.schoolId
            cleverSection['Teacher_id'] = sycClass['PrimaryStaffID']
            cleverSection['Name'] = Generators.createSectionName(
                sycClass['Name'], sycClass['Section'])

            cleverSection['Term_name'] = Generators.createTermName(sycClass['TermLength'])
            cleverSection['Term_start'] = Generators.createTermStart(
                sycClass['TermLength'],
                self._strToDate(currentYear['Q1.StartDate']),
                self._strToDate(currentYear['Q3.StartDate']),
                self._strToDate(currentYear['EndDate']))
            cleverSection['Term_end'] = Generators.createTermEnd(
                sycClass['TermLength'],
                self._strToDate(currentYear['Q1.StartDate']),
                self._strToDate(currentYear['Q3.StartDate']),
                self._strToDate(currentYear['EndDate']))

            cleverSection['Course_name'] = sycClass['Name']
            cleverSection['Subject'] = 'Language'
            cleverSection['Period'] = 'GP' # Adlt, GP
            cleverSection['Status'] = 'Active'

            cleverSections = cleverSections.append(pandas.Series(data=cleverSection, name=index))

        return cleverSections

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

