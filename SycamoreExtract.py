import requests
from ast import literal_eval

mainUrl = 'https://app.sycamoreschool.com/api/v1';
schoolId = 2132;

relationships = {'Parents' : 1, 'Mother' : 2, 'Father' : 3,
                 'Grandmother' : 4, 'Grandfather' : 5,
                 'Stepmother' : 6, 'Stepfather' : 7,
                 'Aunt' : 8, 'Uncle' : 9, 'Relative' : 10};
                 
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

def sortCriteria(familyMemberRecord):
    code = relationships.get(familyMemberRecord["Relation"], 100);
    if (familyMemberRecord["PrimaryParent"] == 1):
        code = 1;
    return code;

def containsEmail(familyMemberRecord):
    email = familyMemberRecord["Email"].strip();
    return email and "@" in email;

def includeEmail(familyMemberRecord):
    return (sortCriteria(familyMemberRecord) < 100 and
            containsEmail(familyMemberRecord));

def getFamilyEmails(familyId):
    familyContactsURL = mainUrl + '/Family/' + str(familyId) + '/Contacts'
    response = retrieve(familyContactsURL)
    familyContacts = response.text    
    #print(familyContacts)    
    familyContactsDict = literal_eval(familyContacts)
    #print(familyContactsDict)

    # Sort family based on relationships
    familyContactsDict = sorted(familyContactsDict, 
                                key=lambda family: sortCriteria(family));
    # pick up to three first family contacts with emails
    firstThree = list(filter(lambda r: includeEmail(r), familyContactsDict))[:3];
    result = ["", "", ""];
    for i in range(0, len(firstThree)):
        result[i] = firstThree[i]["Email"].strip();
    return result;
    

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
for family in listFamilies:
    [primaryEmail, secondaryEmail, tertiaryEmail] = getFamilyEmails(family["ID"])
    family['primaryEmail'] = primaryEmail
    family['secondaryEmail'] = secondaryEmail
    family['tertiaryEmail'] = tertiaryEmail
    #print(listFamilies[k])
    familyDict[family["Code"]] = family

listClassesUrl = mainUrl + '/School/' + str(schoolId) + '/Classes'
response = retrieve(listClassesUrl)
print ("code:"+ str(response.status_code))
classesInfo = response.text
#print(classesInfo)


classesDict = literal_eval(classesInfo);
#print(type(classesDict["Period"]))
for aClassRecord in classesDict["Period"]:
    teacherFullName = aClassRecord["PrimaryTeacher"]
    teacherFirstName = ""
    teacherLastName  = ""
    if (teacherFullName.strip()):
        #print(teacherFullName)
        teacherNameTokens = teacherFullName.split()
        teacherFirstName = teacherNameTokens[0]
        teacherLastName = " ".join(teacherNameTokens[1:])
            
    #print("Class Name = {}, Class Room = {}, Class ID = {}".format(aClassRecord["Name"], aClassRecord["Section"], aClassRecord["ID"]))        
    classInfoUrl = mainUrl + '/Class/' + str(aClassRecord["ID"]) + '/Directory'    
    response = retrieve(classInfoUrl)
    classStudentsInfo = response.text
    #print((classStudentsInfo))
    if len(classStudentsInfo) == 0:  
        continue;
      
    classStudentsInfoDict = literal_eval(classStudentsInfo)
    #print(classStudentsInfoDict)
    for classStudent in classStudentsInfoDict:
        #print(classStudentsInfoDict[j]["Code"])
        # family code is 7 characters long
        familyCode = classStudent["Code"][:7]
        family = familyDict.get(familyCode);
        
        family["State"] = formatStateName(family["State"]);
        
        #aClassRecord["Name"] = aClassRecord["Name"].translate({ord(i):None for i in "\""})
        aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
        cityStateZip = '"' + \
                       family["City"] + ", " + \
                       family["State"] + " " + \
                       family["ZIP"] + '"';
                       
        print("{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}"
              .format(classStudent["LastName"].strip(), ",",
                      classStudent["FirstName"].strip(), ",",
                      aClassRecord["Name"], ",",
                      aClassRecord["Section"], ",",
                      teacherLastName, ",",
                      teacherFirstName, ",",
                      familyCode, ",",
                      '"', family["Name"], '"', ",",
                      family["primaryEmail"], ",",
                      family["secondaryEmail"], ",",
                      family["tertiaryEmail"], ",",
                      '"', family["Address"], '"', ",",
                      cityStateZip))
        
        #print(familyCode)            
        #print(family)
