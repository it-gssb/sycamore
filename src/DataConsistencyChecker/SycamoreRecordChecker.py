class ConsistencyRules:
    def checkNoWhitespaceAtEndings(self, name):
        if (name):
            if (name.startswith(' ') or name.endswith(' ')):
                print('Rule {0} violated, Name={1}'.format(list(self.rulesMap)[0], name))
                return False
        return True
    
    def _OnlyOneSpaceBetweenPartsOfName(self, name):
        if (name.strip().find('  ') > 0):
            print('Rule {0} violated, Name={1}'.format(list(self.rulesMap)[1], name))
            return False
        return True

        
    def check_NoLeadingOrTrailingSpaceStaff(self, personRecord):
        teacherFullName = personRecord["PrimaryTeacher"]
        nameComponents = teacherFullName.split()
        firstName = nameComponents[0]
        self.checkNoWhitespaceAtEndings(firstName)
        lastName = nameComponents[1]
        self.checkNoWhitespaceAtEndings(lastName)
        
    def check_NoLeadingOrTrailingSpaceInNames(self, studentRecord):
        self.check_NoLeadingOrTrailingSpaceStaff(studentRecord)
        firstName = studentRecord["FirstName"]
        self.checkNoWhitespaceAtEndings(firstName)
        lastName = studentRecord["LastName"]
        self.checkNoWhitespaceAtEndings(lastName)
        parent1LastName = studentRecord["parent1LastName"]
        self.checkNoWhitespaceAtEndings(parent1LastName)
        parent1FirstName = studentRecord["parent1FirstName"]
        self.checkNoWhitespaceAtEndings(parent1FirstName)
        parent2LastName = studentRecord["parent2LastName"]
        self.checkNoWhitespaceAtEndings(parent2LastName)
        parent2FirstName = studentRecord["parent2FirstName"]
        self.checkNoWhitespaceAtEndings(parent2FirstName)
        primaryEmail = studentRecord["primaryEmail"]
        self.checkNoWhitespaceAtEndings(primaryEmail)
        secondaryEmail = studentRecord["secondaryEmail"]
        self.checkNoWhitespaceAtEndings(secondaryEmail)
        tertiaryEmail = studentRecord["tertiaryEmail"]
        self.checkNoWhitespaceAtEndings(tertiaryEmail)
    
    def check_OnlyOneSpaceBetweenPartsOfName(self, studentRecord):
        #Extract first name, middle name and last name from studentRecord
        self._OnlyOneSpaceBetweenPartsOfName(studentRecord["FirstName"])
        self._OnlyOneSpaceBetweenPartsOfName(studentRecord["parent1FirstName"])
        self._OnlyOneSpaceBetweenPartsOfName(studentRecord["parent2FirstName"])
        
    def check_HomeroomTeacherSameAsClassTeacher(self, studentRecord):
        #Extract homeRoomTeacher and classTeacher from studentRecord
        homeRoomTeacher = studentRecord["HomeroomTeacher"]
        classTeacher = studentRecord["PrimaryTeacher"]
        if (homeRoomTeacher != classTeacher):
            print('Rule {0} violated, Home room teacher={1}, class teacher={2}, student={3}'.format(list(self.rulesMap)[7], homeRoomTeacher, classTeacher, studentRecord["LastName"]))
            return False
        return True
            
    
    rulesMap = {'NoLeadingOrTrailingSpaceInNames' : check_NoLeadingOrTrailingSpaceInNames, 
                'OnlyOneSpaceBetweenPartsOfName' : check_OnlyOneSpaceBetweenPartsOfName, 
                'HomeroomTeacherSameAsClassTeacher' : check_HomeroomTeacherSameAsClassTeacher,
                'NoNicknameInName' : False, 
                'DoubleNamesSeparatedByHyphen' : False, 
                'StaffEmailEndingWithGSSB' : False, 
                'ActiveStudentsMappedToAClass' : False, 
                'ActiveFamiliesHaveActiveChild' : False, 
                }
             
    def checkConsistency(self, studentRecord):
        for name, aRule in self.rulesMap.items():
            if (aRule != False):
                status = aRule(self, studentRecord)

class SycamoreRecordChecker:

    def __init__(self):
        self.consistencyRules = ConsistencyRules()
        
    def checkNamingConvention(self, studentInfo):
        self.consistencyRules.checkConsistency(studentInfo)
        
if __name__ == '__main__':
    checker = SycamoreRecordChecker()
    #checker.populateFamilyRecords()
    #checker.checkNamingConvention()