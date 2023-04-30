import argparse
from datetime import datetime
import os
import pandas
import logging
import sys
  
# append the path of the parent directory
sys.path.append('..')
sys.path.append('.')

from lib import Generators
from lib import SycamoreRest
from lib import SycamoreCache

DATE_FORMAT = '%m/%d/%Y'

class RegistrationCreator:

    def __init__(self, args):
        self.school_id = args.school_id
        self.cache_dir = args.cache_dir
        self.output_dir = args.output_dir

        rest = SycamoreRest.Extract(school_id=self.school_id, token=args.security_token)
        if args.reload_data:
            self.sycamore = SycamoreCache.Cache(rest=rest)
            self.sycamore.loadAll()
            self.sycamore.saveToFiles(self.cache_dir)

            # Check that saved data can be reloaded and compares clean
            self.sycamore2 = SycamoreCache.Cache(source_dir=self.cache_dir)
            self.sycamore2.compare(self.sycamore)
        else:
            self.sycamore = SycamoreCache.Cache(source_dir=self.cache_dir)

    def generate(self):
        registrations = self.generateRegistrations()
        registrations.to_csv(
            os.path.join(self.output_dir, 'registrations.csv'),
            index=False)

    def generateRegistrations(self):
        registrations = pandas.DataFrame(columns=[
            'StudentLastName',
            'StudentFirstName',
            'StudentName',
            'Class',
            'Room',
            'TeacherLastName',
            'TeacherFirstName',
            'TeacherName',
            'StudentGSSBEmail',
            'FamilyID',
            'StudentCode',
            'Parent1LastName',
            'Parent1FirstName',
            'Parent2LastName',
            'Parent2FirstName',
            'ParentNames',
            'StudentLastNameIfDifferent',
            'PrimaryParentEmail',
            'SecondaryParentEmail',
            'TertiaryParentEmail',
            'StreetAddress',
            'CityStateZip'
        ])

        sycClasses = self.sycamore.get('classes')
        sycClassesDetails = self.sycamore.get('class_details')
        sycEmployees = self.sycamore.get('employees')
        sycFamilies = self.sycamore.get('families')
        sycFamilyContacts = self.sycamore.get('family_contacts')

        for studentIndex, sycStudent in self.sycamore.get('students').iterrows():
            try:
                sycStudentClassesList = self.sycamore.get('student_classes')
                sycStudentClasses = sycStudentClassesList.loc[sycStudentClassesList['students_id'] == studentIndex]
            except KeyError:
                print('Skipping student "{} {}" with no classes'.format(_sycStudent['FirstName'], _sycStudent['LastName']))
                continue

            if sycStudentClasses is None:
                print('Skipping student "{} {}" with empty classes'.format(_sycStudent['FirstName'], _sycStudent['LastName']))
                continue

            for studentClassIndex, sycStudentClass in sycStudentClasses.iterrows():
                registration = {}
                studentLastName = sycStudent['LastName']
                registration['StudentLastName'] = studentLastName
                registration['StudentFirstName'] = sycStudent['FirstName']
                registration['StudentName'] = Generators.createStudentName(
                    first_name=sycStudent['FirstName'],
                    last_name=sycStudent['LastName'])
                sycClass = sycClasses.loc[studentClassIndex]
                sycClassDetails = sycClassesDetails.loc[studentClassIndex]
                sycPrimaryStaffID = sycClass['PrimaryStaffID']
                sycPrimaryStaff = sycEmployees.loc[sycPrimaryStaffID]
                registration['Class'] = Generators.createClassName(
                    class_name=sycStudentClass['Name'],
                    teacher_first=sycPrimaryStaff['FirstName'],
                    teacher_last=sycPrimaryStaff['LastName'])
                registration['Room'] = sycClassDetails['Facility.Name']
                registration['TeacherLastName'] = sycPrimaryStaff['LastName']
                registration['TeacherFirstName'] = sycPrimaryStaff['FirstName']
                registration['TeacherName'] = Generators.createTeacherName(
                    first_name=sycPrimaryStaff['FirstName'],
                    last_name=sycPrimaryStaff['LastName'])
                registration['StudentGSSBEmail'] = Generators.createStudentEmailAddress(
                    sycStudent['FirstName'], sycStudent['LastName'], include_domain=True)
                sycFamilyId = sycStudent['FamilyID']
                sycFamily = sycFamilies.loc[sycFamilyId]
                registration['FamilyID'] = sycFamily['Code']
                registration['StudentCode'] = sycStudent['StudentCode']
                sycStudentFamilyContacts = sycFamilyContacts.loc[sycFamilyContacts['families_id'] == sycFamilyId]
                sycStudentPrimaryParents = sycStudentFamilyContacts.loc[sycStudentFamilyContacts['PrimaryParent'] == 1]
                primaryParentLastName = None
                if len(sycStudentPrimaryParents) > 0:
                    primaryParentLastName = sycStudentPrimaryParents.iloc[0]['LastName']
                    registration['Parent1LastName'] = primaryParentLastName
                    registration['Parent1FirstName'] = sycStudentPrimaryParents.iloc[0]['FirstName']
                    registration['PrimaryParentEmail'] = sycStudentPrimaryParents.iloc[0]['Email']
                if len(sycStudentPrimaryParents) > 1:
                    registration['Parent2LastName'] = sycStudentPrimaryParents.iloc[1]['LastName']
                    registration['Parent2FirstName'] = sycStudentPrimaryParents.iloc[1]['FirstName']
                    registration['SecondaryParentEmail'] = sycStudentPrimaryParents.iloc[1]['Email']
                if len(sycStudentPrimaryParents) > 2:
                    # osk: Whatever other e-mail address is left over (likely non-primary).
                    registration['TertiaryParentEmail'] = sycStudentPrimaryParents.iloc[2]['Email']
                registration['ParentNames'] = sycFamily['Name']
                if primaryParentLastName != studentLastName:
                    # figure out what we actually want here
                    registration['StudentLastNameIfDifferent'] = studentLastName
                registration['StreetAddress'] = sycFamily['Address']
                registration['CityStateZip'] = Generators.createCityStateZip(sycFamily['City'], sycFamily['State'], sycFamily['ZIP'])

                registrations.loc[str(studentIndex) + '_' + str(studentClassIndex)] = pandas.Series(data=registration)

        return registrations

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

if __name__ == '__main__' :
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    creator = RegistrationCreator(args)
    creator.generate()

