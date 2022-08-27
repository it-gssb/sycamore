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

DATE_FORMAT = '%m/%d/%Y'

class CleverCreator:

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
        schools = self.generateSchools()
        schools.to_csv(
            os.path.join(self.output_dir, 'schools.csv'),
            index=False)

        students = self.generateStudents()
        students.sort_index(axis='index').to_csv(
            os.path.join(self.output_dir, 'students.csv'),
            index=False,
            date_format=DATE_FORMAT)

        sections = self.generateSections()
        sections.to_csv(
            os.path.join(self.output_dir, 'sections.csv'),
            index=False,
            date_format=DATE_FORMAT)

        teachers = self.generateTeachers()
        teachers.sort_index(axis='index').to_csv(
            os.path.join(self.output_dir, 'teachers.csv'),
            index=False)

        enrollments = self.generateEnrollments()
        enrollments.sort_values(by='Section_id').to_csv(
            os.path.join(self.output_dir, 'enrollments.csv'),
            index=False)

        users = self.generateUsers()
        users.sort_values(by=['SIS ID','Phone']).to_csv(
            os.path.join(self.output_dir, 'user.csv'),
            index=False)

        guardianRelationships = self.generateGuardianRelationships()
        guardianRelationships.sort_values(by='SIS ID').to_csv(
            os.path.join(self.output_dir, 'guardianrelationship.csv'),
            index=False)

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
            'Password',
            ])

        for index, _sycStudent in self.sycamore.get('students').iterrows():
            sycStudentDetails = self.sycamore.get('student_details').loc[index]

            if sycStudentDetails['Grade'] is None:
                print('Skipping student "{}" with empty grade'.format(index))
                continue

            cleverStudent = {}
            cleverStudent['Student_id'] = index
            cleverStudent['School_id'] = self.school_id
            cleverStudent['Username'] = Generators.createStudentEmailAddress(
                sycStudentDetails['FirstName'], sycStudentDetails['LastName'],
                include_domain=False)
            cleverStudent['Student_number'] = sycStudentDetails['ExtID']
            cleverStudent['Dob'] = self._strToDate(sycStudentDetails['DOB'])
            cleverStudent['Grade'] = Generators.createGrade(sycStudentDetails['Grade'])
            cleverStudent['State_id'] = sycStudentDetails['StateID']
            cleverStudent['Secondary_email'] = sycStudentDetails['Email']
            cleverStudent['First_name'] = sycStudentDetails['FirstName']
            cleverStudent['Last_name'] = sycStudentDetails['LastName']
            cleverStudent['Middle_name'] = ''  # TODO(osenft): Find data
            cleverStudent['Status'] = ''  # TODO(osenft): Find data
            cleverStudent['Password'] = sycStudentDetails['Code']

            cleverStudents.loc[index] = pandas.Series(data=cleverStudent)

        return cleverStudents

    def _getCurrentYear(self):
        for index, year in self.sycamore.get('years').iterrows():
            if year['Current'] == '1':
                return self.sycamore.get('years_details').loc[index]
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

        for index, sycClass in self.sycamore.get('classes').iterrows():
            cleverSection = {}
            cleverSection['Section_id'] = index
            cleverSection['School_id'] = self.school_id
            cleverSection['Teacher_id'] = Generators.createTeacherId(sycClass['PrimaryStaffID'])
            cleverSection['Name'] = Generators.createSectionName(
                sycClass['Name'], sycClass['Section'])

            cleverSection['Term_name'] = Generators.createTermName(sycClass['TermLength'])
            term_start_date = Generators.createTermStart(
                sycClass['TermLength'],
                self._strToDate(currentYear['Q1.StartDate']),
                self._strToDate(currentYear['Q3.StartDate']),
                self._strToDate(currentYear['EndDate']))
            cleverSection['Term_start'] = term_start_date.strftime(DATE_FORMAT) if term_start_date else ''
            term_start_end = Generators.createTermEnd(
                sycClass['TermLength'],
                self._strToDate(currentYear['Q1.StartDate']),
                self._strToDate(currentYear['Q3.StartDate']),
                self._strToDate(currentYear['EndDate']))
            cleverSection['Term_end'] = term_start_end.strftime(DATE_FORMAT) if term_start_end else ''

            cleverSection['Course_name'] = sycClass['Name']
            cleverSection['Subject'] = 'Language'
            cleverSection['Period'] = Generators.createPeriod(sycClass['Name'])
            cleverSection['Status'] = 'Active'

            cleverSections.loc[index] = pandas.Series(data=cleverSection)

        return cleverSections


    def generateTeachers(self):
        cleverTeachers = pandas.DataFrame(columns=[
            'Teacher_id',
            'School_id',
            'Teacher_email',
            'Username',
            'Title',
            'Last_name',
            'First_name',
            'Password',
            ])

        for index, sycEmployee in self.sycamore.get('employees').iterrows():
            if sycEmployee['Position'] != 'Teacher' and sycEmployee['Position'] != 'Substitute':
                continue
            if sycEmployee['Active'] != 1:
                continue
            if sycEmployee['Current'] != 1:
                continue

            cleverTeacher = {}
            cleverTeacher['Teacher_id'] = index
            cleverTeacher['School_id'] = self.school_id
            emailAddress = Generators.createTeacherEmailAddress(
                sycEmployee['FirstName'], sycEmployee['LastName'], sycEmployee['Email1'],
                include_domain=False)
            cleverTeacher['Teacher_email'] = emailAddress
            cleverTeacher['Username'] = emailAddress
            cleverTeacher['Title'] = sycEmployee['Position']
            cleverTeacher['Last_name'] = sycEmployee['LastName']
            cleverTeacher['First_name'] = sycEmployee['FirstName']
            cleverTeacher['Password'] = 'GS5Brul3s!'

            cleverTeachers.loc[index] = pandas.Series(data=cleverTeacher)

        return cleverTeachers

    def generateEnrollments(self):
        cleverEnrollments = pandas.DataFrame(columns=[
            'School_id',
            'Section_id',
            'Student_id',
            ])

        for index, _sycStudent in self.sycamore.get('students').iterrows():
            try:
                sycStudentClass = self.sycamore.get('student_classes').loc[index]
            except KeyError:
                print('Skipping student "{} {}" with no classes'.format(_sycStudent["FirstName"], _sycStudent["LastName"]))
                continue

            if sycStudentClass is None:
                print('Skipping student "{} {}" with no classes'.format(_sycStudent["FirstName"], _sycStudent["LastName"]))
                continue

            cleverEnrollment = {}
            cleverEnrollment['School_id'] = self.school_id
            cleverEnrollment['Section_id'] = sycStudentClass['ID']
            cleverEnrollment['Student_id'] = index

            cleverEnrollments.loc[index] = pandas.Series(data=cleverEnrollment)

        return cleverEnrollments

    def _appendUser(self, sdsUsers, contactId, sycFamilyContact, phoneField):
        if sycFamilyContact[phoneField]:
            sdsUser = {}
            sdsUser['Email'] = sycFamilyContact['Email']
            sdsUser['First Name'] = sycFamilyContact['FirstName'].strip()
            sdsUser['Last Name'] = sycFamilyContact['LastName'].strip()
            sdsUser['Phone'] = Generators.createPhoneNumber(sycFamilyContact[phoneField])
            sdsUser['SIS ID'] = contactId

            sdsUsers.loc[str(contactId)+"_"+phoneField] = pandas.Series(data=sdsUser)

        return sdsUsers


    def generateUsers(self):
        sdsUsers = pandas.DataFrame(columns=[
            'Email',
            'First Name',
            'Last Name',
            'Phone',
            'SIS ID',
            ])

        for index, sycFamilyContact in self.sycamore.get('family_contacts').iterrows():
            # Email, First Name and Last Name are required in SDS, so skip contacts without it
            if (sycFamilyContact['PrimaryParent'] != 1
                or not sycFamilyContact['Email']
                or not sycFamilyContact['FirstName']
                or not sycFamilyContact['LastName']):
                continue

            sdsUsers = self._appendUser(sdsUsers, index, sycFamilyContact, 'WorkPhone')
            sdsUsers = self._appendUser(sdsUsers, index, sycFamilyContact, 'HomePhone')
            sdsUsers = self._appendUser(sdsUsers, index, sycFamilyContact, 'CellPhone')

        return sdsUsers.drop_duplicates()

    def generateGuardianRelationships(self):
        sdsGuardianRelationships = pandas.DataFrame(columns=[
            'SIS ID', # student ID
            'Email', # contact e-mail
            'Role', # contact role
            ])

        sycFamilyContacts = self.sycamore.get('family_contacts')
        sycFamilyStudents = self.sycamore.get('family_students')

        for familyIndex, sycFamily in self.sycamore.get('families').iterrows():
            for contactIndex, sycFamilyContact in sycFamilyContacts.loc[sycFamilyContacts['families_id'] == familyIndex].iterrows():
                # Email is the lookup key, so skip contacts without it
                if not sycFamilyContact['Email'] or sycFamilyContact['PrimaryParent'] != 1:
                    continue

                for studentIndex in sycFamilyStudents.loc[sycFamilyStudents['families_id'] == familyIndex].index.values:
                    sdsGuardianRelationship = {}
                    sdsGuardianRelationship['Email'] = sycFamilyContact['Email']
                    sdsGuardianRelationship['Role'] = Generators.createRole(sycFamilyContact['Relation'])
                    sdsGuardianRelationship['SIS ID'] = studentIndex

                    sdsGuardianRelationships.loc[str(studentIndex)+"_"+str(contactIndex)] = (
                        pandas.Series(data=sdsGuardianRelationship))

        return sdsGuardianRelationships.drop_duplicates()

    def _getSchool(self) -> pandas.core.series.Series:
        sycSchools = self.sycamore.get('school')
        if len(sycSchools.index) != 1:
            raise KeyError('Should have 1 school, but found {}'.format(len(sycSchools.index)))
        return sycSchools.iloc[0]

    def _getPrincipal(self) -> pandas.core.series.Series:
        # We expect there to only be ONE employee who has themselves as a manager, which is the principal
        sycEmployees = self.sycamore.get('employees')

        sycPrincipals = sycEmployees.loc[lambda emp: emp['ManagerID'] == emp.index]
        if len(sycPrincipals.index) != 1:
            raise KeyError('Should have 1 principal, but found {}'.format(len(sycPrincipals.index)))
        return sycPrincipals.iloc[0]

    def generateSchools(self):
        sdsSchools = pandas.DataFrame(columns=[
            'School_id',
            'School_name',
            'School_number',
            'Low_grade',
            'High_grade',
            'Principal',
            'Principal_email',
            ])

        sycSchool = self._getSchool()
        sycEmployeePrincipal = self._getPrincipal()

        sdsSchool = {}
        sdsSchool['School_id'] = self.school_id
        sdsSchool['School_name'] = sycSchool['Name']
        sdsSchool['School_number'] = self.school_id
        sdsSchool['Low_grade'] = 'Prekindergarten' # The API doesn't include this field
        sdsSchool['High_grade'] = '12' # The API doesn't include this field
        sdsSchool['Principal'] = '{} {}'.format(sycEmployeePrincipal['FirstName'], sycEmployeePrincipal['LastName'])
        sdsSchool['Principal_email'] = sycEmployeePrincipal['Email1']

        sdsSchools.loc[self.school_id] = pandas.Series(data=sdsSchool)

        return sdsSchools


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
    creator = CleverCreator(args)
    creator.generate()

