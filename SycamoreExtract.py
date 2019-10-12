import requests
from ast import literal_eval

mainUrl = 'https://app.sycamoreschool.com/api/v1';
schoolId = 2132;
token="<define here>";

def retrieve(url):
    response = requests.get(url, headers={'Authorization': 'Bearer ' + token });
    if not response.status_code == 200:
        print('Request ' + url + ' failed.')
    return response;
    
def formatStateName(state):
    newState = state.strip();
    if ("massachusetts" in state.strip().lower()):
        newState = "MA";
    elif ("new hampshire" in state.strip().lower()):
        newState = "NH";
    elif ("rhode island" in state.strip().lower()):
        newState = "RI";
    return newState.upper();

def getFamilyEmails(familyId):
    familyContactsURL = mainUrl + '/Family/' + str(familyId) + '/Contacts'
    response = retrieve(familyContactsURL)
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
        email = familyMemberRecord["Email"].strip();
        if (not email or not "@" in email):
            i += 1;
            continue;
        
        relation = familyMemberRecord["Relation"]
        if ("Father" == relation):
            if (email and "@" in email):
                primaryEmail = email
        elif ("Mother" == relation):    
            if (email and "@" in email):
                if (primaryEmail):
                    secondaryEmail = email
                else:
                    primaryEmail = email
        elif ("Grandmother" == relation or "Grandfather" == relation):
            if (email and "@" in email):
                if (primaryEmail):
                    if (secondaryEmail):
                        tertiaryEmail = email
                    else:
                        secondaryEmail = email
                else:
                    primaryEmail = email
        elif (1 == familyMemberRecord["PrimaryParent"]):
            if (email and "@" in email):
                if (primaryEmail):
                    secondaryEmail = email
                else:
                    primaryEmail = email
        i += 1
    #print(fatherEmail, motherEmail, tertiaryEmail)
    return [primaryEmail, secondaryEmail, tertiaryEmail]


# Want LastName, FirstName, Class, Room, Teacher LastName, Teacher FirstName, FamilyId, ParentName
# Primary Parent Name, VolunteerAssignment, Address, 
#From Classes record, get Room(Section), Class(Description), TeacherName(PrimaryTeacher), ClassID
#For each ClassID

# In /Family/<Id>/Contacts I will get email addresses of both mother and father
# Use token here.
listFamiliesUrl = mainUrl + '/School/' + str(schoolId) + '/Families'
response = retrieve(listFamiliesUrl)
print ("******************")
print ("code:"+ str(response.status_code))
print ("******************")
#print ("content:"+ str(response.text))
listFamiliesInfo = response.text
#print(listFamiliesInfo)
listFamilies = literal_eval(listFamiliesInfo)
print('found ' + str(len(listFamilies)) + ' family records')

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

listClassesUrl = mainUrl + '/School/' + str(schoolId) + '/Classes'
response = retrieve(listClassesUrl)
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
    classInfoUrl = mainUrl + '/Class/' + str(aClassRecord["ID"]) + '/Directory'    
    response = retrieve(classInfoUrl)
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
            state = formatStateName(familyDict.get(familyCode)["State"])
            familyDict.get(familyCode)["State"] = state;
            
            #aClassRecord["Name"] = aClassRecord["Name"].translate({ord(i):None for i in "\""})
            aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
            CityStateZip = '"' + \
                           familyDict.get(familyCode)["City"] + ", " + \
                           familyDict.get(familyCode)["State"] + " " + \
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
