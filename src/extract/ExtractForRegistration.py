import argparse
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

SCOPE_GENERAL    = 'Local.General'
CUSTOM_PHOTO     = 'PhotoRelease'
CUSTOM_NIKOLAUS  = 'Permission for Nikolaus'
CUSTOM_ALLERGIES = 'Allergies'
CUSTOM_IEP       = 'IEP or 504 in regular school'

class InvalidOutputDir(Exception):
    pass


class RegistrationCreator:

    def __init__(self, args):
        self.school_id = args.school_id
        self.cache_dir = args.cache_dir
        self.output_dir = args.output_dir
        self.xlsx_output = args.xlsx_output

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        elif not os.path.isdir(self.output_dir):
            raise InvalidOutputDir('output_dir="{}" is not a directory'.format(self.output_dir))

        print('Initializing cache')
        rest = SycamoreRest.Extract(school_id=self.school_id, token=args.security_token)
        self.sycamore = SycamoreCache.Cache(rest=rest, cache_dir=self.cache_dir, reload=args.reload_data)

    def generate(self):
        print('Generating output')
        registrations = self.generateRegistrations()
        if self.xlsx_output:
            registrations.to_excel(
                os.path.join(self.output_dir, 'registrations.xlsx'),
                sheet_name='Student_Parent_and_Teacher', index=False)
        else:
            registrations.to_csv(
            os.path.join(self.output_dir, 'registrations.csv'), index=False)
        
    def incrChar(self, char):
        n = chr(ord(char) + 1)
        
        if (ord(char) == ord('z')):
            n = ord('a')
        elif (ord(char) == ord('Z')):
            n = ord('A')
        elif (ord(char) == ord('9')):
            n = ord('0')
        elif (ord(char) == ord('-')):
            n = ord('~')
        else:
            n = ord(char) + 1
            
        return chr(n)

    def incrString(self, string):
        return "".join(self.incrChar(a) for a in string)

    def generateRegistrations(self):
        registrations = pandas.DataFrame(columns=[
            'StudentLastName',
            'StudentFirstName',
            'StudentName',
            'Allergies',
            'IEPor504',
            'Nikolaus',
            'PhotoRelease',
            'Class',
            'Room',
            'TeacherLastName',
            'TeacherFirstName',
            'TeacherName',
            'StudentGSSBEmail',
            'FamilyID',
            'StudentCode',
            'LingcoPwd',
            'Parent1LastName',
            'Parent1FirstName',
            'Parent2LastName',
            'Parent2FirstName',
            'ParentNames',
            'StudentLastNameIfDifferent1',
            'StudentLastNameIfDifferent2',
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
            #retrieve custom fields for student and final custom values in Local.General area
            sycCustomFieldList = self.sycamore.get('student_custom_fields')
            customFields = sycCustomFieldList.loc[sycCustomFieldList['students_id'] == studentIndex]
            general = customFields[SCOPE_GENERAL].get(studentIndex)
            photoRelease = next((x['Value'] for i, x in enumerate(general) if x['Name'] == CUSTOM_PHOTO), 'N')
            nikolaus     = next((x['Value'] for i, x in enumerate(general) if x['Name'] == CUSTOM_NIKOLAUS), 'None')
            iep          = next((x['Value'] for i, x in enumerate(general) if x['Name'] == CUSTOM_IEP), '')
            allergies    = next((x['Value'] for i, x in enumerate(general) if x['Name'] == CUSTOM_ALLERGIES), '')
            
            try:
                sycStudentClassesList = self.sycamore.get('student_classes')
                sycStudentClasses = sycStudentClassesList.loc[sycStudentClassesList['students_id'] == studentIndex]
            except KeyError:
                print('Skipping student "{} {}" with no classes'.format(sycStudent['FirstName'], sycStudent['LastName']))
                continue

            if sycStudentClasses is None:
                print('Skipping student "{} {}" with empty classes'.format(sycStudent['FirstName'], sycStudent['LastName']))
                continue

            for studentClassIndex, sycStudentClass in sycStudentClasses.iterrows():
                registration = {}
                studentLastName = sycStudent['LastName']
                registration['StudentLastName'] = studentLastName
                registration['StudentFirstName'] = sycStudent['FirstName']
                registration['StudentName'] = Generators.createStudentName(
                    first_name=sycStudent['FirstName'],
                    last_name=sycStudent['LastName'])
                registration['Allergies'] = allergies
                registration['IEPor504'] = iep
                registration['Nikolaus'] = nikolaus
                registration['PhotoRelease'] = photoRelease
                
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
                registration['LingcoPwd'] = self.incrString(sycStudent['StudentCode'])
                sycStudentFamilyContacts = sycFamilyContacts.loc[sycFamilyContacts['families_id'] == sycFamilyId]
                sycStudentPrimaryParents = sycStudentFamilyContacts.loc[sycStudentFamilyContacts['PrimaryParent'] == 1]
                if len(sycStudentPrimaryParents) > 0:
                    primaryParentLastName = sycStudentPrimaryParents.iloc[0]['LastName']
                    registration['Parent1LastName'] = primaryParentLastName
                    registration['Parent1FirstName'] = sycStudentPrimaryParents.iloc[0]['FirstName']
                    registration['PrimaryParentEmail'] = sycStudentPrimaryParents.iloc[0]['Email']
                    if primaryParentLastName != studentLastName:
                        registration['StudentLastNameIfDifferent1'] = studentLastName
                if len(sycStudentPrimaryParents) > 1:
                    secondaryParentLastName = sycStudentPrimaryParents.iloc[1]['LastName']
                    registration['Parent2LastName'] = secondaryParentLastName
                    registration['Parent2FirstName'] = sycStudentPrimaryParents.iloc[1]['FirstName']
                    registration['SecondaryParentEmail'] = sycStudentPrimaryParents.iloc[1]['Email']
                    if secondaryParentLastName != studentLastName:
                        registration['StudentLastNameIfDifferent2'] = studentLastName
                if len(sycStudentPrimaryParents) > 2:
                    # osk: Whatever other e-mail address is left over (likely non-primary).
                    registration['TertiaryParentEmail'] = sycStudentPrimaryParents.iloc[2]['Email']
                registration['ParentNames'] = sycFamily['Name']
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
    parser.add_argument('--xlsx', dest='xlsx_output', action='store_true',
                        help='use XLS format as output')
    parser.add_argument('--out', dest='output_dir', action='store',
                        required=True, help='Output directory')
    parser.set_defaults(reload_data=False)
    parser.set_defaults(xlsx_output=False)
    return parser.parse_args()

if __name__ == '__main__' :
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    creator = RegistrationCreator(args)
    creator.generate()
    print('Done')

