import requests
from ast import literal_eval

token="<define here>";

mainUrl = 'https://app.sycamoreschool.com/api/v1';
schoolId = 2132;

relationships = {'Parents' : 1, 'Mother' : 2, 'Father' : 3,
                 'Grandmother' : 4, 'Grandfather' : 5,
                 'Stepmother' : 6, 'Stepfather' : 7,
                 'Aunt' : 8, 'Uncle' : 9, 'Relative' : 10};
                 

class RestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value);
    
def retrieve(url):
    response = requests.get(url, headers={'Authorization': 'Bearer ' + token });
    if not response.status_code == 200:
        raise RestError('Request ' + url + ' failed with code ' + str(response.status_code))
    info = response.text
#     print((info))
    record = [];
    if len(info) > 0:  
        record = literal_eval(info)
    return record;

def getFamilyDict(mainUrl, schoolId):
    listFamiliesUrl = mainUrl + '/School/' + str(schoolId) + '/Families'
    listFamilies = retrieve(listFamiliesUrl)
    print 'Retrieving {0} family records.'.format(str(len(listFamilies)))
    familyDict = {}
    for family in listFamilies:
        [primaryEmail, secondaryEmail, tertiaryEmail] = getFamilyEmails(family["ID"])
        family['primaryEmail'] = primaryEmail
        family['secondaryEmail'] = secondaryEmail
        family['tertiaryEmail'] = tertiaryEmail
        familyDict[family["Code"]] = family
#         print(family)
    return familyDict

def getClassDict(mainUrl, schoolId):
    listClassesUrl = mainUrl + '/School/' + str(schoolId) + '/Classes'
    classesDict = retrieve(listClassesUrl)
    print 'Retrieving {0} class records.'.format(str(len(classesDict["Period"])))
#     print(classesDict)
#     print(type(classesDict["Period"]))
    # validate class data
    validateClassDetails(classesDict["Period"])
    return classesDict
    
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
    familyContactsDict = retrieve(familyContactsURL)
    #print(familyContactsDict)

    # Sort family based on relationships
    familyContactsDict = sorted(familyContactsDict, 
                                key=lambda family: sortCriteria(family));
    # pick up to three first family contacts that define an email
    firstThree = list(filter(lambda r: includeEmail(r), familyContactsDict))[:3];
    result = ["", "", ""];
    for i in range(0, len(firstThree)):
        result[i] = firstThree[i]["Email"].strip();
    return result;

def createRecord(aClassRecord, classStudent, familyDict):
    # family code is 7 characters long
    familyCode = classStudent["Code"][:7]
    family = familyDict.get(familyCode);
    family["State"] = formatStateName(family["State"]);
#     print(familyCode)            
#     print(family)
    
    teacherFullName = aClassRecord["PrimaryTeacher"]
    teacherFirstName = ""
    teacherLastName  = ""
    if (teacherFullName.strip()):
        teacherNameTokens = teacherFullName.split()
        teacherFirstName = teacherNameTokens[0]
        teacherLastName = " ".join(teacherNameTokens[1:])
    
    cityStateZip = '"' + \
                   family["City"] + ", " + \
                   family["State"] + " " + \
                   family["ZIP"] + '"';
                   
    return "{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}" \
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
                   cityStateZip)

def validateClassDetails(classes):
    for aClassRecord in classes:
        teacherFullName = aClassRecord["PrimaryTeacher"]
        # Report Missing Teacher details
        if (not teacherFullName.strip()):
            print('Warning: Missing teacher name in record for class {0}'
                  .format(aClassRecord["Name"]))
            
def saveRecords(allRecords):
    for record in allRecords:
        print record;

# Want LastName, FirstName, Class, Room, Teacher LastName, Teacher FirstName, 
# FamilyId, ParentName, Primary Parent Name, VolunteerAssignment, Address, 
# From Classes record, get Room(Section), Class(Description),
# TeacherName(PrimaryTeacher), ClassID for each ClassID

# In /Family/<Id>/Contacts I will get email addresses of both mother and father
# Use token here.
try:
    familyDict = getFamilyDict(mainUrl, schoolId)
    classesDict = getClassDict(mainUrl, schoolId)
    
    allRecords=[];
    for aClassRecord in classesDict["Period"]:
        # clean name of record
        aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
#         print("Class Name = {}, Class Room = {}, Class ID = {}"
#               .format(aClassRecord["Name"], aClassRecord["Section"], aClassRecord["ID"]))
   
        classInfoUrl = mainUrl + '/Class/' + str(aClassRecord["ID"]) + '/Directory'    
        classStudentsInfoDict = retrieve(classInfoUrl)
        print('Retrieved {0} student records in class {1}.'
              .format(str(len(classStudentsInfoDict)), aClassRecord["Name"]))
#         print(classStudentsInfoDict)
        
        # create records for all students
        for classStudent in classStudentsInfoDict:
            allRecords.append(createRecord(aClassRecord, classStudent, familyDict))
            
    saveRecords(allRecords);
except RestError as e:
    print("REST API error: {0}".format(e.value));
else:
    print("Connection failed");
