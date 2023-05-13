import argparse
import logging
import sys
import inspect
  
# append the path of the parent directory
sys.path.append('..')
sys.path.append('.')

from lib import SycamoreRest
from lib import SycamoreCache

DATE_FORMAT = '%m/%d/%Y'

class RegistrationCreator:
    
    _RULE_VIOLATION_MSG      = 'Rule Violation: {0} in "{1}"; in: {2}'
    _SPECIAL_NAME_COMPONENTS = {'zu ', 'von ', 'van ', 'de '}
    _NOT_ALLEWED_CHARS       = {'(', ')', ' - ', ',', '/'}

    def __init__(self, args):
        self.school_id = args.school_id
        self.cache_dir = args.cache_dir

        print('Initializing cache')
        rest = SycamoreRest.Extract(school_id=self.school_id, token=args.security_token)
        self.sycamore = SycamoreCache.Cache(rest=rest, cache_dir=self.cache_dir, reload=args.reload_data)

    # 
    # Basic Validation Logic
    #

    def _NoWhitespaceAtEndings(self, name, context):
        if (name):
            if (name.strip() is not name):
                ruleName = inspect.stack()[1][3]
                print(self._RULE_VIOLATION_MSG.format(ruleName, name, context))
                return False
        return True
    
    def _OnlyOneSpaceBetweenPartsOfName(self, name, context):
        if (name.strip().find('  ') > 0):
            ruleName = inspect.stack()[1][3]
            print(self._RULE_VIOLATION_MSG.format(ruleName, name, context))
            return False
        return True
    
    def _containsSpecialNameComponent(self, name, matches):
        for component in matches:
            if (component in name.lower()):
                return True
        return False
    
    def _NoSpaceBetweenPartsOfName(self, name, context):
        if (not self._containsSpecialNameComponent(name, self._SPECIAL_NAME_COMPONENTS) and 
            name.strip().find(' ') > 0):
            ruleName = inspect.stack()[1][3]
            print(self._RULE_VIOLATION_MSG.format(ruleName, name, context))
            return False
        return True
    
    def _NotAllowedCharactersInName(self, name, context):
        if (self._containsSpecialNameComponent(name, self._NOT_ALLEWED_CHARS)):
            ruleName = inspect.stack()[1][3]
            print(self._RULE_VIOLATION_MSG.format(ruleName, name, context))
            return False
        return True
    
    def _EmailInGssbDomain(self, email, context):
        if (email and not email.lower().strip().endswith('@gssb.org')):
            ruleName = inspect.stack()[1][3]
            print(self._RULE_VIOLATION_MSG.format(ruleName, email, context))
            return False
        return True
    
    def _NoRecords(self, id, record, existing, context):
        if (not id in existing):
            ruleName = inspect.stack()[1][3]
            print(self._RULE_VIOLATION_MSG.format(ruleName, record['Name'], context))
            return False
        return True

    # 
    # Validation Logic
    #

    def check_NoLeadingOrTrailingSpacesInStudent(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._NoWhitespaceAtEndings(record["FirstName"], context + ' (FirstName)')
        self._NoWhitespaceAtEndings(record["LastName"], context + ' (LastName)')
        
    def check_UnexpectedCharactersInStudentName(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._NotAllowedCharactersInName(record["FirstName"], context + ' (FirstName)')
        self._NotAllowedCharactersInName(record["LastName"], context + ' (LastName)')
        
    def check_NoDoubleSpacesInStudentFirstName(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._OnlyOneSpaceBetweenPartsOfName(record["FirstName"], context)
    
    # TODO: extend to require '-' between names
    def check_NoSpacesInStudentLastName(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._NoSpaceBetweenPartsOfName(record["LastName"], context)
        
    def check_NoLeadingOrTrailingSpacesInEmployee(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._NoWhitespaceAtEndings(record["FirstName"], context + ' (FirstName)')
        self._NoWhitespaceAtEndings(record["LastName"], context + ' (LastName)')
        self._NoWhitespaceAtEndings(record["Email1"], context + ' (Email)')
        
    def check_EmailMustBeGssbForEmployee(self, record):
        context = record["FirstName"] + ' ' +  record["LastName"]
        self._EmailInGssbDomain(record["Email1"], context)
        
    def check_NoLeadingOrTrailingSpacesInContact(self, record, family):
        context = record["FirstName"] + ' ' +  record["LastName"] + \
                  ' of family ' + family['Name']
        self._NoWhitespaceAtEndings(record["FirstName"], context + ' (FirstName)')
        self._NoWhitespaceAtEndings(record["LastName"], context + ' (LastName)')
        self._NoWhitespaceAtEndings(record["Email"], context + ' (Email)')

    def check_ClassWithoutStudents(self, id, record, existing):
        context = record["Name"]
        self._NoRecords(id, record, existing, context)
        
    def check_FamilyWithoutStudents(self, id, record, existing):
        context = record["Name"]
        self._NoRecords(id, record, existing, context)

    #
    # main validation routine
    #

    def validate(self):
        print('Validating data')
        studentFamilies = set()
        classesWithStudents = set()
        studentClassesList = self.sycamore.get('student_classes')
        students = self.sycamore.get('students')
        for id, student in students.iterrows():
            # keep note of student family
            studentFamilies.add(student['FamilyID'])
            self.check_NoLeadingOrTrailingSpacesInStudent(student)
            self.check_NoDoubleSpacesInStudentFirstName(student)
            self.check_NoSpacesInStudentLastName(student)
            self.check_UnexpectedCharactersInStudentName(student)
            
            try:
                studentClasses = studentClassesList.loc[studentClassesList['students_id'] == id]
            except KeyError:
                print('Skipping student "{} {}" with no classes'.format(student['FirstName'], student['LastName']))
                continue

            if studentClasses is None:
                print('Skipping student "{} {}" with empty classes'.format(student['FirstName'], student['LastName']))
                continue
            elif (len(studentClasses.index)==1):
                classesWithStudents.add(studentClasses.index[0])
                
                        
        employees = self.sycamore.get('employees')
        for id, employee in employees.iterrows():
            if (not employee['Active']):
                continue
            self.check_NoLeadingOrTrailingSpacesInEmployee(employee)
            self.check_EmailMustBeGssbForEmployee(employee)
            
        families = self.sycamore.get('families')
        for id, family in families.iterrows():
            self.check_FamilyWithoutStudents(id, family, studentFamilies)
            
                    
        familyContacts = self.sycamore.get('family_contacts')
        for id, contact in familyContacts.iterrows():
            familyID = contact['families_id']
            family = families.xs(familyID)
            self.check_NoLeadingOrTrailingSpacesInContact(contact, family)
                
        classes = self.sycamore.get('classes')
        for id, aClass in classes.iterrows():
            self.check_ClassWithoutStudents(id, aClass, classesWithStudents)

        return True

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
    parser.set_defaults(reload_data=False)
    return parser.parse_args()

if __name__ == '__main__' :
    logging.basicConfig(level=logging.INFO)
    args = parse_arguments()
    creator = RegistrationCreator(args)
    creator.validate()
    print('Done')

