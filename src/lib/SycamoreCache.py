from lib import SycamoreRest
import pandas
import os

##           

class Cache:
    def __init__(self, rest: SycamoreRest.Extract = None, sourceDir: str = None):
        self.rest = rest

        self.families = None
        self.families_details = None
        self.students = None
        self.students_details = None
        self.contacts = None
        self.classes = None
        self.employees = None

        if sourceDir is not None:
            self._loadFromFiles(sourceDir)

    def _loadFromFiles(self, sourceDir: str):
        self.families = pandas.read_csv(os.path.join(sourceDir, 'families.csv'), index_col='ID')
        self.families_details = pandas.read_csv(os.path.join(sourceDir, 'families_details.csv'), index_col='Code')
        self.students = pandas.read_csv(os.path.join(sourceDir, 'students.csv'), index_col='ID')
        self.students_details = pandas.read_csv(os.path.join(sourceDir, 'students_details.csv'), index_col='Code')
        self.contacts = pandas.read_csv(os.path.join(sourceDir, 'contacts.csv'), index_col='ID')
        self.classes = pandas.read_csv(os.path.join(sourceDir, 'classes.csv'), index_col='ID')
        self.employees = pandas.read_csv(os.path.join(sourceDir, 'employees.csv'), index_col='ID')

    def saveToFiles(self, targetDir: str):
        self.getFamilies().to_csv(os.path.join(targetDir, 'families.csv'))
        self.getFamiliesDetails().to_csv(os.path.join(targetDir, 'families_details.csv'))
        self.getStudents().to_csv(os.path.join(targetDir, 'students.csv'))
        self.getStudentsDetails().to_csv(os.path.join(targetDir, 'students_details.csv'))
        self.getContacts().to_csv(os.path.join(targetDir, 'contacts.csv'))
        self.getClasses().to_csv(os.path.join(targetDir, 'classes.csv'))
        self.getEmployees().to_csv(os.path.join(targetDir, 'employees.csv'))

    def compare(self, other):
        print(self.getFamilies().compare(other.getFamilies()))
        print(self.getFamiliesDetails().compare(other.getFamiliesDetails()))
        print(self.getStudents().compare(other.getStudents()))
        print(self.getStudentsDetails().compare(other.getStudentsDetails()))
        print(self.getContacts().compare(other.getContacts()))
        print(self.getClasses().compare(other.getClasses()))
        print(self.getEmployees().compare(other.getEmployees()))

    def getFamilies(self):
        if self.families is None:
            self.families = self.rest.getFamilies()
        return self.families

    def getFamiliesDetails(self):
        if self.families_details is None:
            families_details = []
            count = 0
            for familyId, family in self.getFamilies().iterrows():
                count = count + 1
                details = self.rest.getFamily(familyId)
                families_details.append(details)
                if count > 5: break
            self.families_details = pandas.concat(families_details)

        return self.families_details

    def getStudents(self):
        if self.students is None:
            self.students = self.rest.getStudents()
        return self.students

    def getStudentsDetails(self):
        if self.students_details is None:
            students_details = []
            count = 0
            for studentId, student in self.getStudents().iterrows():
                count = count + 1
                details = self.rest.getStudent(studentId)
                students_details.append(details)
                if count > 5: break
            self.students_details = pandas.concat(students_details)

        return self.students_details

    def getContacts(self):
        if self.contacts is None:
            self.contacts = self.rest.getContacts()
        return self.contacts

    def getClasses(self):
        if self.classes is None:
            self.classes = self.rest.getClasses()
        return self.classes

    def getEmployees(self):
        if self.employees is None:
            self.employees = self.rest.getEmployees()
        return self.employees

