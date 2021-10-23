from lib import SycamoreRest

##           

class Cache:
    def __init__(self, rest: SycamoreRest.Extract):
        self.rest = rest

        self.families = None
        self.students = None
        self.contacts = None
        self.classes = None
        self.employees = None
        self.studentMap = {}

    def getFamilies(self):
        if self.families is None:
            self.families = self.rest.getFamilies()
        return self.families

    def getStudents(self):
        if self.students is None:
            self.students = self.rest.getStudents()
        return self.students

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

    def getStudent(self, studentId: int):
        if not studentId in self.studentMap:
            self.studentMap[studentId] = self.rest.getStudent(studentId)
        return self.studentMap[studentId]
