import requests
from ast import literal_eval

mainurl = 'https://app.sycamoreschool.com/api/v1'
listClasses = mainurl + '/School/2132/Classes'
listFamiliesUrl = mainurl + '/School/2132/Families'
token="<define here>";

def formatStateName(familyDict, familyCode):
    state = familyDict.get(familyCode)["State"]
    if ("massachusetts" == state.lower()):
        familyDict.get(familyCode)["State"] = "MA";
    elif ("new hampshire" == state.lower()):
        familyDict.get(familyCode)["State"] = "NH";
    elif ("rhode island" == state.lower()):
        familyDict.get(familyCode)["State"] = "RI";

def getFamilyEmails(familyId):
    familyContactsURL = mainurl + '/Family/' + str(familyId) + '/Contacts'
    response = requests.get(familyContactsURL,
                            headers={'Authorization': 'Bearer ' + token })
    familyContacts = response.text    
    #print(familyContacts)    
    familyContactsDict = literal_eval(familyContacts)
    #print(familyContactsDict)
    primaryEmail = ""
    secondaryEmail = ""
    tertiaryEmail = ""
    i = 0
    while (i < len(familyContactsDict)):
        familyMemberRecord = familyContactsDict[i]
        if ("Father" == familyMemberRecord["Relation"]):
            if (familyMemberRecord["Email"].strip() and
                "@" in familyMemberRecord["Email"]):
                primaryEmail = familyMemberRecord["Email"]
        elif ("Mother" == familyMemberRecord["Relation"]):    
            if (familyMemberRecord["Email"].strip() and
                "@" in familyMemberRecord["Email"]):
                if (primaryEmail.strip()):
                    secondaryEmail = familyMemberRecord["Email"]
                else:
                    primaryEmail = familyMemberRecord["Email"]
        elif ("Grandmother" == familyMemberRecord["Relation"] or
              "Grandfather" == familyMemberRecord["Relation"]):
            if (familyMemberRecord["Email"].strip() and
                "@" in familyMemberRecord["Email"]):
                if (primaryEmail.strip()):
                    if (secondaryEmail.strip()):
                        tertiaryEmail = familyMemberRecord["Email"]
                    else:
                        secondaryEmail = familyMemberRecord["Email"]
                else:
                    primaryEmail = familyMemberRecord["Email"]
        elif (1 == familyMemberRecord["PrimaryParent"]):
            if (familyMemberRecord["Email"].strip() and
                "@" in familyMemberRecord["Email"]):
                if (primaryEmail.strip()):
                    secondaryEmail = familyMemberRecord["Email"]
                else:
                    primaryEmail = familyMemberRecord["Email"]
        i += 1
    #print(fatherEmail, motherEmail, tertiaryEmail)
    return [primaryEmail, secondaryEmail, tertiaryEmail]


# Want LastName, FirstName, Class, Room, Teacher LastName, Teacher FirstName, FamilyId, ParentName
# Primary Parent Name, VolunteerAssignment, Address, 
#From Classes record, get Room(Section), Class(Description), TeacherName(PrimaryTeacher), ClassID
#For each ClassID

# In /Family/<Id>/Contacts I will get email addresses of both mother and father
# Use token here.

# response = requests.get(url4b, headers={'Authorization': 'Bearer ' + token })
# print ("code:"+ str(response.status_code))
#print(response.text)

response = requests.get(listFamiliesUrl, headers={'Authorization': 'Bearer ' + token })
print ("******************")
print ("code:"+ str(response.status_code))
print ("******************")
#print ("content:"+ str(response.text))
listFamiliesInfo = response.text
#print(listFamiliesInfo)
listFamilies = literal_eval(listFamiliesInfo)
familyDict = {}
k = 0
while (k < len(listFamilies)):
    [primaryEmail, secondaryEmail, tertiaryEmail] = getFamilyEmails(listFamilies[k]["ID"])
    listFamilies[k]['primaryEmail'] = primaryEmail
    listFamilies[k]['secondaryEmail'] = secondaryEmail
    listFamilies[k]['tertiaryEmail'] = tertiaryEmail
    #print(listFamilies[k])
    familyDict[listFamilies[k]["Code"]] = listFamilies[k]
    k += 1

response = requests.get(listClasses, headers={'Authorization': 'Bearer ' + token })
print ("code:"+ str(response.status_code))
classesInfo = response.text
#print(classesInfo)


classesDict = literal_eval(classesInfo);
#print(type(classesDict["Period"]))
i = 0
while (i < len(classesDict["Period"])):
    aClassRecord = classesDict["Period"][i]
    
    teacherFullName = aClassRecord["PrimaryTeacher"]
    teacherFirstName = ""
    teacherLastName    = ""
    if (teacherFullName.strip()):
        #print(teacherFullName)
        teacherNameTokens = teacherFullName.split()
        teacherFirstName =     teacherNameTokens[0]
        teacherLastName = " ".join(teacherNameTokens[1:])
            
    #print("Class Name = {}, Class Room = {}, Class ID = {}".format(aClassRecord["Name"], aClassRecord["Section"], aClassRecord["ID"]))        
    i += 1
    classInfoUrl = mainurl + '/Class/' + str(aClassRecord["ID"]) + '/Directory'    
    response = requests.get(classInfoUrl,
                             headers={'Authorization': 'Bearer ' + token })
    classStudentsInfo = response.text
    #print((classStudentsInfo))
    if len(classStudentsInfo) > 0:    
        classStudentsInfoDict = literal_eval(classStudentsInfo)
        #print(classStudentsInfoDict)
        j = 0
        while(j < len(classStudentsInfoDict)):
            #print(classStudentsInfoDict[j]["Code"])
            # family code is 7 characters long
            familyCode = classStudentsInfoDict[j]["Code"][:7]
            formatStateName(familyDict, familyCode)
            
            #aClassRecord["Name"] = aClassRecord["Name"].translate({ord(i):None for i in "\""})
            aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
            CityStateZip = '"' + \
                           familyDict.get(familyCode)["City"] + ", " + \
                           familyDict.get(familyCode)["State"].upper() + " " + \
                           familyDict.get(familyCode)["ZIP"] + '"';
                           
            print("{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}"
                  .format(classStudentsInfoDict[j]["LastName"].strip(), ",",
                          classStudentsInfoDict[j]["FirstName"].strip(), ",",
                          aClassRecord["Name"], ",",
                          aClassRecord["Section"], ",",
                          teacherLastName, ",",
                          teacherFirstName, ",",
                          familyCode, ",",
                          '"', familyDict.get(familyCode)["Name"], '"', ",",
                          familyDict.get(familyCode)["primaryEmail"], ",",
                          familyDict.get(familyCode)["secondaryEmail"], ",",
                          familyDict.get(familyCode)["tertiaryEmail"], ",",
                          '"', familyDict.get(familyCode)["Address"], '"', ",",
                          CityStateZip))
            
            #print(familyCode)            
            #print(familyDict.get(familyCode))
            j += 1        
