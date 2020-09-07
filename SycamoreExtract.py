import argparse
import re
import logging
import requests
from ast import literal_eval

## CONSTANTS

MAIN_URL = 'https://app.sycamoreschool.com/api/v1';

RELATIONSHIPS = {'Parents' : 1, 'Mother' : 2, 'Father' : 3,
                 'Grandmother' : 4, 'Grandfather' : 5,
                 'Stepmother' : 6, 'Stepfather' : 7,
                 'Aunt' : 8, 'Uncle' : 9, 'Relative' : 10};
                 
##           

class RestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value);
    
def correctUnicodeEscape(text):
    # find all occurrences of the pattern
    newText = '';
    startIndex = 0;
    # find all occurrences of the pattern \uhhhh in text
    for m in re.finditer('\\u[\\da-f]{4}', text):
        # attach text between patterns to result string
        newText += text[startIndex:m.start()-1]
        startIndex = m.end()
        # convert \uhhhh with 4 digit hex number to unicode
        hexnum = '0x' + text[m.start()+1:m.end()]
        uChar = ''
        # only convert and add unicode 
        if int(hexnum, 0) <= 255:
            uChar = unichr(int(hexnum, 0))
            logging.debug("Converted hex " + hexnum +
                         " to special character '" + uChar + "'")
        # attach converted unicode character to return string
        newText += uChar
    
    # attach remaining text after last occurrence of pattern
    newText += text[startIndex:len(text)]

    return newText;
    
def retrieve(url, token):
    response = requests.get(url, headers={'Authorization': 'Bearer ' + token,
                                          'Content-type': 'application/json; charset=utf-8'});
    if not response.status_code == 200:
        msg = 'Request ' + url + ' failed with code ' + str(response.status_code);
        raise RestError(msg)
    info = correctUnicodeEscape(response.text)
    logging.debug((info))
    record = [];
    if len(info) > 0:
        record = literal_eval(info)
    return record;

def camelCase(string):
    return " ".join(a.capitalize() for a in re.split(r"[^a-zA-Z0-9&#\.-]", string))

def getFamilyDict(MAIN_URL, schoolId, token):
    listFamiliesUrl = MAIN_URL + '/School/' + str(schoolId) + '/Families'
    listFamilies = retrieve(listFamiliesUrl, token)
    logging.info('Found {0} family records.'.format(str(len(listFamilies))))
    familyDict = {}
    for family in listFamilies:
        [primaryEmail, secondaryEmail, tertiaryEmail] = getFamilyEmails(family["ID"], token)
        family['primaryEmail'] = primaryEmail
        family['secondaryEmail'] = secondaryEmail
        family['tertiaryEmail'] = tertiaryEmail
        familyDict[family["Code"]] = family
        logging.debug(family)
    return familyDict

def getClassDict(MAIN_URL, schoolId, token):
    listClassesUrl = MAIN_URL + '/School/' + str(schoolId) + '/Classes'
    classesDict = retrieve(listClassesUrl, token)
    logging.info('Retrieving {0} class records.'
                 .format(str(len(classesDict["Period"]))))
    logging.debug(classesDict)
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

def formatClassName(className, teacherLast, teacherFirst):
    result = className
    if ('DSD I/' in className):
        components = className.split('/')
        c = ''
        if len(components)>1 and components[1].strip() == teacherLast:
            c = teacherFirst[0] + teacherLast[0]
        result = 'DSD I/' + c
    elif ("DSD II" in className):
        result = className.replace(' Jahr', 'J')
    return result;

def sortCriteria(familyMemberRecord):
    code = RELATIONSHIPS.get(familyMemberRecord["Relation"], 100);
    if (familyMemberRecord["PrimaryParent"] == 1):
        code = 1;
    return code;

def containsEmail(familyMemberRecord):
    email = familyMemberRecord["Email"].strip();
    return email and "@" in email;

def includeEmail(familyMemberRecord):
    return (sortCriteria(familyMemberRecord) < 100 and
            containsEmail(familyMemberRecord));

def getFamilyEmails(familyId, token):
    familyContactsURL = MAIN_URL + '/Family/' + str(familyId) + '/Contacts'
    familyContactsDict = retrieve(familyContactsURL, token)
    #print(familyContactsDict)

    # Sort family based on RELATIONSHIPS
    familyContactsDict = sorted(familyContactsDict, 
                                key=lambda family: sortCriteria(family));
    # pick up to three first family contacts that define an email
    firstThree = list(filter(lambda r: includeEmail(r), familyContactsDict))[:3];
    result = ["", "", ""];
    for i in range(0, len(firstThree)):
        result[i] = firstThree[i]["Email"].strip();
    return result

def createRecordHeader() :
    header = ["StudentLastName",
              "StudentFirstName",
              "Class",
              "Room",
              "TeacherLastName",
              "TeacherFirstName",
              "FamilyID",
              "ParentNames",
              "PrimaryEmail",
              "SecondaryEmail",
              "TertiaryEmail",
              "StreetAddress", 
              "CityStateZip"]
    
    return ",".join(header);

def getAddress(family):
    address = ''
    addresses = [camelCase(family["Address"].strip()), 
                 camelCase(family["Address2"].strip())]
    if (addresses[0] == addresses[1]):
        address = '"' + addresses[0] + '"'
    else:
        neAddresses = filter(lambda a:a.strip(), addresses)
        address = '"' + ', '.join(neAddresses) + '"'
    return address
   
def createRecord(aClassRecord, classStudent, familyDict):
    try:
        # family code is 7 characters long
        familyCode = classStudent["Code"][:7]
        family = familyDict.get(familyCode);
        family["State"] = formatStateName(family["State"]);
        
        teacherFullName = aClassRecord["PrimaryTeacher"]
        teacherFirstName = ""
        teacherLastName  = ""
        if (teacherFullName.strip()):
            teacherNameTokens = teacherFullName.split()
            teacherFirstName = teacherNameTokens[0]
            teacherLastName = " ".join(teacherNameTokens[1:])
        
        cityStateZip = '"' + \
                       camelCase(family["City"].strip()) + ", " + \
                       family["State"] + " " + \
                       family["ZIP"][0:5].strip() + '"';
    
        record = [classStudent["LastName"].strip(),
                  classStudent["FirstName"].strip(),
                  formatClassName(aClassRecord["Name"].strip(),
                                  teacherLastName.strip(),
                                  teacherFirstName.strip()),
                  aClassRecord["Section"].strip(),
                  teacherLastName.strip(),
                  teacherFirstName.strip(),
                  familyCode,
                  '"' + family["Name"].strip() + '"',
                  family["primaryEmail"].strip(),
                  family["secondaryEmail"].strip(),
                  family["tertiaryEmail"].strip(),
                  getAddress(family), 
                  cityStateZip]
    except TypeError: 
        logging.exception("Incorrect family record for code {0} and student {1} {2}"
                           .format(familyCode, 
                                   classStudent["FirstName"],
                                   classStudent["LastName"]));
        record = [];
    finally:
        if len(record) == 0:
            return "";
        return ",".join(record);

def validateClassDetails(classes):
    for aClassRecord in classes:
        teacherFullName = aClassRecord["PrimaryTeacher"]
        # Report Missing Teacher details
        if (not teacherFullName.strip()):
            logging.warn('Warning: Missing teacher name in record for class {0}'
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
def extractRecords(schoolId, token):
    try:
        familyDict = getFamilyDict(MAIN_URL, schoolId, token)
        classesDict = getClassDict(MAIN_URL, schoolId, token)
        
        allRecords=[];
        allRecords.append(createRecordHeader())
        for aClassRecord in classesDict["Period"]:
            # clean name of record
            aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
            logging.debug(("Class Name = {}, Class Room = {}, Class ID = {}"
                          .format(aClassRecord["Name"], aClassRecord["Section"],
                                  aClassRecord["ID"])))
       
            classInfoUrl = MAIN_URL + '/Class/' + str(aClassRecord["ID"]) + '/Directory'    
            classStudentsInfoDict = retrieve(classInfoUrl, token)
            logging.info('Retrieved {0} student records in class {1}'
                         .format(str(len(classStudentsInfoDict)), aClassRecord["Name"]))
            logging.debug(classStudentsInfoDict)
            
            # create records for all students
            for classStudent in classStudentsInfoDict:
                r = createRecord(aClassRecord, classStudent, familyDict);
                if len(r)>0:
                    allRecords.append(r);
                
        saveRecords(allRecords);
    except RestError as e:
        msg = "REST API error: {0}".format(e.value);
        logging.exception(msg, e);
    except Exception as ex:
        logging.exception("Connection failed", ex);

def parseArguments():
    parser = argparse.ArgumentParser(description='Extract Family and School Data')
    parser.add_argument('--school', dest='schoolId', action='store',
                        type=int, required=True, help='Sycamore school ID.')
    parser.add_argument('--token', dest='securityToken', action='store',
                        required=True, help='Sycamore security token.')
    args = parser.parse_args()
    return (args.schoolId, args.securityToken)

if __name__ == "__main__" :
    logging.basicConfig(level=logging.INFO)
    args = parseArguments()
    extractRecords(args[0], args[1])
