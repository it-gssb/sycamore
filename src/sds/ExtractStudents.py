import argparse
from datetime import datetime
import os
import pandas
# import re
import logging
import sys

# append the path of the parent directory
sys.path.append("..")
sys.path.append(".")

from lib import Generators
from lib import SycamoreRest
from lib import SycamoreCache

class StudentCreator:

    def __init__(self, args):
        self.school_id = args.school_id
        self.cache_dir = args.cache_dir
        self.output_dir = args.output_dir

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        elif not os.path.isdir(self.output_dir):
            raise InvalidOutputDir('output_dir="{}" is not a directory'.format(self.output_dir))

        print('Initializing cache')
        rest = SycamoreRest.Extract(school_id=self.school_id, token=args.security_token)
        self.sycamore = SycamoreCache.Cache(rest=rest, cache_dir=self.cache_dir, reload=args.reload_data)

    def generate(self):
        print('Generating output')
        schools = self.generateAzureAdStudents()
        schools.to_csv(
            os.path.join(self.output_dir, 'azure-ad-students.csv'),
            index=False)

    def generateAzureAdStudents(self):
        sdsUsers = pandas.DataFrame(columns=[
            'EmailAddress',
            'SourceId',
            'LastName',
            'FirstName',
            ])

        # Add students
        for index, sycStudent in self.sycamore.get('students').iterrows():
            sycStudentDetails = self.sycamore.get('student_details').loc[index]

            if sycStudentDetails['Grade'] is None:
                print('Skipping student "{}" with empty grade'.format(index))
                continue

            emailAddress = Generators.createStudentEmailAddress(
                sycStudentDetails['FirstName'], sycStudentDetails['LastName'],
                include_domain=True)

            sdsUser = {}
            sdsUser['SourceId'] = sycStudent['StudentCode']
            sdsUser['EmailAddress'] = emailAddress
            sdsUser['LastName'] = sycStudentDetails['LastName']
            sdsUser['FirstName'] = sycStudentDetails['FirstName']

            sdsUsers.loc[index] = pandas.Series(data=sdsUser)

        return sdsUsers.drop_duplicates()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Extract Family and School Data')
    parser.add_argument('--school', dest='school_id', action='store',
                        type=int, required=True, help='Sycamore school ID')
    parser.add_argument('--token', dest='security_token', action='store',
                        required=True, help='Sycamore security token')
    parser.add_argument('--cache', dest='cache_dir', action='store',
                        required=True, help='Cache directory')
    parser.add_argument('--reload', dest='reload_data', action='store_true',
                        help='Whether to reload data')
    parser.add_argument('--out', dest='output_dir', action='store',
                        required=True, help='Output directory')
    parser.set_defaults(reload_data=False)
    return parser.parse_args()

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    creator = StudentCreator(args)
    creator.generate()
    print('Done')

