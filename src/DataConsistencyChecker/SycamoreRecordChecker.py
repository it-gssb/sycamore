import requests
from ast import literal_eval

mainurl = 'https://app.sycamoreschool.com/api/v1'
url1 = mainurl + '/Me'
listClasses = mainurl + '/School/2132/Classes'
listFamiliesUrl = mainurl + '/School/2132/Families'
listFamiliesUrl2 = mainurl + '/School/2132/Directory/'
url4 = mainurl + '/Family/1000648'
url4b = mainurl + '/Family/1000648/ServiceLogs'
#url5 = mainurl + '/Class/180608/Directory';
url5 = mainurl + '/Class/336207/Directory';
superusertoken = 'f70e45a939fde7997a23d09220cd4f30'
sidstudenid = '1101710'

class ConsistencyRules:
    def checkNoWhitespaceAtEndings(self, name):
        if (name):
            if (name.startswith(' ') or name.endswith(' ')):
                print('Rule {0} violated, Name={1}'.format(list(self.rulesMap)[0], name)) # will need to give more context here.
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
    
    def _OnlyOneSpaceBetweenPartsOfName(self, name):
        tokens = name.split(' ')
        for atoken in tokens:
            self.checkNoWhitespaceAtEndings(atoken)
            
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
                'NoNicknameInName' : False, 
                'OnlyOneSpaceBetweenPartsOfName' : check_OnlyOneSpaceBetweenPartsOfName, 
                'DoubleNamesSeparatedByHyphen' : False, 
                'StaffEmailEndingWithGSSB' : False, 
                'ActiveStudentsMappedToAClass' : False, 
                'ActiveFamiliesHaveActiveChild' : False, 
                'HomeroomTeacherSameAsClassTeacher' : check_HomeroomTeacherSameAsClassTeacher}
             
    def checkConsistency(self, studentRecord):
        for aRule in self.rulesMap:
            if (self.rulesMap[aRule] != False):
                status = self.rulesMap[aRule](self, studentRecord)

class SycamoreRecordChecker:

    def __init__(self):
        self.token = "ea065be8f629b8f4db37566ea8752b3a"
        self.mainurl = 'https://app.sycamoreschool.com/api/v1'
        self.url = self.mainurl + '/Me'
        self.listFamiliesUrl = self.mainurl + '/School/2132/Families'
        self.consistencyRules = ConsistencyRules()
        
    def populateFamilyRecords(self):
        response = requests.get(listFamiliesUrl, headers={'Authorization': 'Bearer ' + self.token })
        print ("*******populate family records ***********")
        print ("code:"+ str(response.status_code))
        print ("******************")
        listFamiliesInfo = response.text
        self.listFamilies = literal_eval(listFamiliesInfo)
        
    def getIndividualFamilyRecord(self, familyID):
        familyURL = 'https://app.sycamoreschool.com/api/v1/School/2132/Directory/1348309'
        print("family URL={0}".format(familyURL))
        response = requests.get(familyURL, headers={'Authorization': 'Bearer ' + self.token })
        print ("******** get individual family record **********")
        print ("code:"+ str(response.status_code))
        print ("******************")
        familyInfo = response.text
        return familyInfo
        
    
        
    def checkNamingConvention(self, studentInfo):
        #k = 0
        #familyInfo = self.getIndividualFamilyRecord('1348309')
        self.consistencyRules.checkConsistency(studentInfo)
        #while (k < len(self.listFamilies)):
            #print(self.listFamilies[k]['ID'], self.listFamilies[k]['Name'])
            #familyInfo = getIndividualFamilyRecord(self.listFamilies[k]['ID'])
        #    familyInfo = self.getIndividualFamilyRecord('1348309')
        #    print("familyInfo={0}".format(familyInfo))
        #    k = k+1
        # Dynamic family contact report will give primary and secondary names individually.
        # https://app.sycamoreeducation.com/api/v1/School/:schoolid/Directory/:id this should be usable as well
        # The id here is a family id which I can get from self.listFamilies['ID]
        

if __name__ == '__main__':
    checker = SycamoreRecordChecker()
    #checker.populateFamilyRecords()
    #checker.checkNamingConvention()