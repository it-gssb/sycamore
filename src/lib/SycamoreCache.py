from lib import SycamoreRest
import pandas
import os

##           

class Cache:
    # Maximum number of families to load. Set to -1 for unbounded.
    MAX_FAMILIES_COUNT = -1

    # Maximum number of students to load. Set to -1 for unbounded.
    MAX_STUDENTS_COUNT = -1

    def __init__(self, rest: SycamoreRest.Extract = None, sourceDir: str = None):
        self.rest = rest

        self.families = None
        self.families_details = None
        self.students = None
        self.students_details = None
        self.contacts = None
        self.classes = None
        self.employees = None
        self.years = None
        self.years_details = None

        if sourceDir is not None:
            self._loadFromFiles(sourceDir)

    def _loadFromFiles(self, sourceDir: str):
        self.families = pandas.read_pickle(os.path.join(sourceDir, 'families.pkl'))
        self.families_details = pandas.read_pickle(os.path.join(sourceDir, 'families_details.pkl'))
        self.students = pandas.read_pickle(os.path.join(sourceDir, 'students.pkl'))
        self.students_details = pandas.read_pickle(os.path.join(sourceDir, 'students_details.pkl'))
        self.contacts = pandas.read_pickle(os.path.join(sourceDir, 'contacts.pkl'))
        self.classes = pandas.read_pickle(os.path.join(sourceDir, 'classes.pkl'))
        self.employees = pandas.read_pickle(os.path.join(sourceDir, 'employees.pkl'))
        self.years = pandas.read_pickle(os.path.join(sourceDir, 'years.pkl'))
        self.years_details = pandas.read_pickle(os.path.join(sourceDir, 'years_details.pkl'))

    def saveToFiles(self, targetDir: str):
        self.getFamilies().to_pickle(os.path.join(targetDir, 'families.pkl'))
        self._getFamiliesDetails().to_pickle(os.path.join(targetDir, 'families_details.pkl'))
        self.getStudents().to_pickle(os.path.join(targetDir, 'students.pkl'))
        self._getStudentsDetails().to_pickle(os.path.join(targetDir, 'students_details.pkl'))
        self.getContacts().to_pickle(os.path.join(targetDir, 'contacts.pkl'))
        self.getClasses().to_pickle(os.path.join(targetDir, 'classes.pkl'))
        self.getEmployees().to_pickle(os.path.join(targetDir, 'employees.pkl'))
        self.getYears().to_pickle(os.path.join(targetDir, 'years.pkl'))
        self._getYearsDetails().to_pickle(os.path.join(targetDir, 'years_details.pkl'))

    def compare(self, other):
        print(self.getFamilies().equals(other.getFamilies()))
        print(self.getFamilies().compare(other.getFamilies()))
        print(self._getFamiliesDetails().equals(other._getFamiliesDetails()))
        print(self._getFamiliesDetails().compare(other._getFamiliesDetails()))
        print(self.getStudents().equals(other.getStudents()))
        print(self.getStudents().compare(other.getStudents()))
        print(self._getStudentsDetails().equals(other._getStudentsDetails()))
        print(self._getStudentsDetails().compare(other._getStudentsDetails()))
        print(self.getContacts().equals(other.getContacts()))
        print(self.getContacts().compare(other.getContacts()))
        print(self.getClasses().equals(other.getClasses()))
        print(self.getClasses().compare(other.getClasses()))
        print(self.getEmployees().equals(other.getEmployees()))
        print(self.getEmployees().compare(other.getEmployees()))
        print(self.getYears().equals(other.getYears()))
        print(self.getYears().compare(other.getYears()))
        print(self._getYearsDetails().equals(other._getYearsDetails()))
        print(self._getYearsDetails().compare(other._getYearsDetails()))

    def getFamilies(self):
        if self.families is None:
            self.families = self.rest.getFamilies()
        return self.families

    def _getFamiliesDetails(self):
        if self.families_details is None:
            families_details = []
            count = 0
            for familyId, family in self.getFamilies().iterrows():
                count = count + 1
                details = self.rest.getFamily(familyId)
                families_details.append(details)
                if (self.MAX_FAMILIES_COUNT >= 0 and 
                    count > self.MAX_FAMILIES_COUNT): break
            self.families_details = pandas.concat(families_details)

        return self.families_details

    def getFamily(self, familyId: int):
        return self._getFamiliesDetails().loc[familyId]

    def getStudents(self):
        if self.students is None:
            self.students = self.rest.getStudents()
        return self.students

    def _getStudentsDetails(self):
        if self.students_details is None:
            students_details = []
            count = 0
            for studentId, student in self.getStudents().iterrows():
                count = count + 1
                details = self.rest.getStudent(studentId)
                students_details.append(details)
                if (self.MAX_STUDENTS_COUNT >= 0 and
                    count > self.MAX_STUDENTS_COUNT): break
            self.students_details = pandas.concat(students_details)

        return self.students_details

    def getStudent(self, studentId: int):
        return self._getStudentsDetails().loc[studentId]

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

    def getYears(self):
        if self.years is None:
            self.years = self.rest.getYears()
        return self.years

    def _getYearsDetails(self):
        if self.years_details is None:
            years_details = []
            for yearId, year in self.getYears().iterrows():
                details = self.rest.getYear(yearId)
                years_details.append(details)
            self.years_details = pandas.concat(years_details)

        return self.years_details

    def getYear(self, yearId: int):
        return self._getYearsDetails().loc[yearId]
