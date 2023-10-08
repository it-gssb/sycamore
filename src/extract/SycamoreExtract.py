import argparse
import re
import logging
import requests
from ast import literal_eval
import sys

## CONSTANTS

MAIN_URL = 'https://app.sycamoreschool.com/api/v1';

RELATIONSHIPS = {'Parents' : 1, 'Mother' : 2, 'Father' : 3,
                 'Grandmother' : 4, 'Grandfather' : 5,
                 'Stepmother' : 6, 'Stepfather' : 7,
                 'Aunt' : 8, 'Uncle' : 9, 'Relative' : 10};
                 
STUDENT_DOMAIN = '@student.gssb.org'
                 
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
    for m in re.finditer(r'\\u[0-9a-f]{4}', text): 
        # attach text between patterns to result string
        newText += text[startIndex:m.start()]
        startIndex = m.end()
        # convert \uhhhh with 4 digit hex number to unicode
        hexnum = '0x' + text[m.start()+2:m.end()]
        uChar = ''
        # only convert and add unicode 
        if int(hexnum, 0) <= 255:
            uChar = chr(int(hexnum, 0))
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
    if response.status_code == 204:
        logging.debug("No content found for " + url)
    elif not response.status_code == 200:
        msg = 'Request ' + url + ' failed with code ' + str(response.status_code);
        raise RestError(msg)
    info = correctUnicodeEscape(response.text).replace('\\','')
    logging.debug((info))
    record = [];
    try:
        if len(info) > 0:
            logging.debug(info)
            replacedNull = info.replace(':null', ':""')
            record = literal_eval(replacedNull)
    except ValueError as e:
        print(info)
        msg = "Failed type conversion of result " + info + " Exception: " + e.message;
        logging.error(msg);
    return record;

def incrChar(char):
    n = chr(ord(char) + 1)
    
    if (ord(char) == ord('z')):
        n = ord('a')
    elif (ord(char) == ord('Z')):
        n = ord('A')
    elif (ord(char) == ord('9')):
        n = ord('0')
    elif (ord(char) == ord('-')):
        n = ord('~')
    else:
        n = ord(char) + 1
        
    return chr(n)

def incrString(string):
    return "".join(incrChar(a) for a in string)

def camelCase(string):
    return " ".join(a.capitalize() for a in re.split(r"[^a-zA-Z0-9&#\.-]", string))

def getSortedContacts(familyId, token):
    familyContactsURL = MAIN_URL + '/Family/' + str(familyId) + '/Contacts'
    familyContactsDict = retrieve(familyContactsURL, token)

    # Sort family based on RELATIONSHIPS
    familyContactsDict = sorted(familyContactsDict, 
                                key=lambda family: sortCriteria(family));
    return familyContactsDict

def __formatFirstName(name: str) -> str:
    return (
        name
            .strip()
            .replace(' ', '')
            .replace('\'', '')
            )

def __formatLastName(name: str) -> str:
    name = (
        name
            .strip()
            .replace('\'', '')
            )

    if name[:4] in ('van ', 'Van ', 'von ', 'Von '):
        return name.replace(' ', '')
    elif name.startswith('Freiin von '):
        return name.replace('Freiin von ', 'Von').replace(' ','-')
    elif ' zu ' in name:
        return name.replace(' ', '')
    elif ' Zu ' in name:
        return name.replace(' ', '')
    elif name.startswith('de '):
        return name.replace(' ', '')
    elif name.startswith('De '):
        return name.replace(' ', '')
    elif ' Nguyen' in name:
        return name.replace(' ', '')
    elif ' nguyen' in name:
        return name.replace(' ', '')
    else:
        return name.replace(' ', '-')

def __createEmailAddress(first_name: str, last_name: str, domain: str) -> str:
    return (__formatFirstName(first_name) + '.'
            + __formatLastName(last_name)
            + domain)

def createStudentEmailAddress(first_name: str, last_name: str) -> str:
    return __createEmailAddress(first_name, last_name, STUDENT_DOMAIN)

def getFamilyEmails(familyContacts):
    # pick up to three first family contacts that define an email
    firstThree = list(filter(lambda r: includeEmail(r), familyContacts))[:3];
    result = [None, "", ""];
    for i in range(0, len(firstThree)):
        result[i] = firstThree[i]["Email"].strip();

    if (not result[0]):
        logging.warning("No Email defined for {0} {1}".format(familyContacts[0]["LastName"],
                                                           familyContacts[0]["FirstName"]))
    return result

def getParents(familyContacts : list, familyId):
    parents = list(filter(lambda r: r["PrimaryParent"] == 1, familyContacts))
    result = [None, None];
    if len(parents) > 2:
        logging.info("more than two primaries for family {}".format(familyId))
    result[0:len(parents[:2])] = parents[:2]
    assert result[0], "At least one parent must exist"
    return result

def getFamilyDict(MAIN_URL, schoolId, token):
    listFamiliesUrl = MAIN_URL + '/School/' + str(schoolId) + '/Families'
    listFamilies = retrieve(listFamiliesUrl, token)
    logging.info('Found {0} family records.'.format(str(len(listFamilies))))
    
    familyDict = {}
    for family in listFamilies:
        familyContacts     = getSortedContacts(family["ID"], token)
        familyEmails       = getFamilyEmails(familyContacts)
        [parent1, parent2] = getParents(familyContacts, family["Code"][:7])
        family['primaryEmail']     = familyEmails[0]
        family['secondaryEmail']   = familyEmails[1]
        family['tertiaryEmail']    = familyEmails[2]
        
        family['parent1FirstName'] = parent1["FirstName"].strip()
        family['parent1LastName']  = parent1["LastName"].strip()
        family['parent2FirstName'] = parent2["FirstName"].strip() if parent2 else ''
        family['parent2LastName']  = parent2["LastName"].strip()  if parent2 else ''

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
    return className;

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
            
def createRecordHeader() :
    header = ["StudentLastName",
              "StudentFirstName",
              "StudentName",
              "Class",
              "Room",
              "TeacherLastName",
              "TeacherFirstName",
              "TeacherName",
              "StudentGSSBEmail,"
              "FamilyID",
              "StudentCode",
              "LingcoPwd",
              "Nikolaus",
              "Parent1LastName",
              "Parent1FirstName",
              "Parent2LastName",
              "Parent2FirstName",
              "ParentNames",
              "StudentLastNameIfDifferent1",
              "StudentLastNameIfDifferent2",
              "PrimaryParentEmail",
              "SecondaryParentEmail",
              "TertiaryParentEmail",
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
   
def createRecord(aClassRecord, classDetailDict, classStudent, nikolaus, familyDict):
    try:
        # family code is 7 characters long
        familyCode = classStudent["Code"][:7]
        studentCode = classStudent["Code"].strip()
        family = familyDict.get(familyCode);
        if (not family):
            logging.error("unable to include student with Code " + familyCode);
            record = [];
            return ""
    
        family["State"] = formatStateName(family["State"]);
        
        teacherFullName = aClassRecord["PrimaryTeacher"]
        teacherFirstName = ""
        teacherLastName  = ""
        if (teacherFullName.strip()):
            teacherNameTokens = teacherFullName.split()
            teacherFirstName = teacherNameTokens[0]
            teacherLastName = " ".join(teacherNameTokens[1:])
        
        studentLastNameIfDifferent1 = ''
        if (classStudent["LastName"].strip().lower() !=
                  family["parent1LastName"].strip().lower()):
            studentLastNameIfDifferent1 = classStudent["LastName"].strip()
            
        studentLastNameIfDifferent2 = ''
        if (family["parent2LastName"] and
            family["parent2LastName"].strip() != '' and
            classStudent["LastName"].strip().lower() !=
                  family["parent2LastName"].strip().lower()):
            studentLastNameIfDifferent2 = classStudent["LastName"].strip()
        
        cityStateZip = '"' + \
                       camelCase(family["City"].strip()) + ", " + \
                       family["State"] + " " + \
                       family["ZIP"][0:5].strip() + '"';
    
        facility = classDetailDict.get("Facility", None);
        room = ""
        if facility:
            room = facility["Name"].strip();
        else:
            logging.info('No room for class ' + aClassRecord["Name"].strip())
                         
        record = [classStudent["LastName"].strip(),
                  classStudent["FirstName"].strip(),
                  ('"' + classStudent["LastName"].strip() + ', ' +
                         classStudent["FirstName"].strip() + '"'),
                  formatClassName(aClassRecord["Name"].strip(),
                                  teacherLastName.strip(),
                                  teacherFirstName.strip()),
                  room,
                  teacherLastName.strip(),
                  teacherFirstName.strip(),
                  ('"' + teacherLastName.strip() + ', ' +
                         teacherFirstName.strip() + '"'),
                  createStudentEmailAddress(classStudent["FirstName"].strip(), 
                                            classStudent["LastName"].strip()),
                  familyCode,
                  studentCode,
                  incrString(studentCode),
                  nikolaus,
                  family["parent1LastName"],
                  family["parent1FirstName"],
                  family["parent2LastName"],
                  family["parent2FirstName"],
                  '"' + family["Name"].strip() + '"',
                  studentLastNameIfDifferent1,
                  studentLastNameIfDifferent2,
                  family["primaryEmail"].strip(),
                  family["secondaryEmail"].strip(),
                  family["tertiaryEmail"].strip(),
                  getAddress(family), 
                  cityStateZip]
                  
        # array of dictionary records
        record2 = {}
        record2["LastName"] = classStudent["LastName"]
        record2["FirstName"] = classStudent["FirstName"]
        record2["parent1LastName"] = family["parent1LastName"]
        record2["parent1FirstName"] = family["parent1FirstName"]
        record2["parent2LastName"] = family["parent2LastName"]
        record2["parent2FirstName"] = family["parent2FirstName"]
        record2["primaryEmail"] = family["primaryEmail"]
        record2["secondaryEmail"] = family["secondaryEmail"]
        record2["tertiaryEmail"] = family["tertiaryEmail"]
        record2["PrimaryTeacher"] = aClassRecord["PrimaryTeacher"]
        record2["HomeroomTeacher"] = classStudent["HomeroomTeacher"]

        
        
        
    except TypeError: 
        logging.exception("Incorrect family record for code {0} and student {1} {2}"
                           .format(familyCode, 
                                   classStudent["FirstName"],
                                   classStudent["LastName"]));
        record = [];
    finally:
        if len(record) == 0:
            return ("", {});
        return (",".join(record), record2)

def validateClassDetails(classes):
    for aClassRecord in classes:
        teacherFullName = aClassRecord["PrimaryTeacher"]
        # Report Missing Teacher details
        if (not teacherFullName.strip()):
            logging.warning('Warning: Missing teacher name in record for class {0}'
                         .format(aClassRecord["Name"]))
            
def saveRecords(allRecords):
    for record in allRecords:
        print (record)


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
        dictRecordArray = []
        for aClassRecord in classesDict["Period"]:
            # clean name of record
            aClassRecord["Name"] = aClassRecord["Name"].replace("\\","")
            logging.debug(("Class Name = {}, Class Room = {}, Class ID = {}"
                          .format(aClassRecord["Name"], aClassRecord["Section"],
                                  aClassRecord["ID"])))
            try:
                classDetailUrl = MAIN_URL + '/School/'+ str(schoolId) +'/Classes/' + str(aClassRecord["ID"]) 
                classDetailDict = retrieve(classDetailUrl, token)
                classStudentsInfoDict = dict()
                classInfoUrl = MAIN_URL + '/Class/' + str(aClassRecord["ID"]) + '/Directory'
                classStudentsInfoDict = retrieve(classInfoUrl, token)
                logging.info('Retrieved {0} student records in class {1}'
                             .format(str(len(classStudentsInfoDict)), aClassRecord["Name"]))
                logging.debug(classStudentsInfoDict)
                
                
                
                # create records for all students
                detailedStudentInfoDict = []
                for classStudent in classStudentsInfoDict:
                    studentID = classStudent["ID"].strip()
                    studentStatistcssUrl = MAIN_URL + '/Student/' + str(studentID) + '/Statistics/' + '9255'
                    stat = retrieve(studentStatistcssUrl, token)
                    logging.debug('Found {0} stat for student {1}.'.format(stat["Value"], classStudent["Code"]))
                    
                    studentInfoUrl = MAIN_URL + '/Student/' + str(studentID)
                    detailedStudentInfo = retrieve(studentInfoUrl, token)
                    detailedStudentInfoDict.append(detailedStudentInfo)
                    
                for detailedStudentInfo in detailedStudentInfoDict:
                    [r, dictRecord] = createRecord(aClassRecord, classDetailDict, detailedStudentInfo, stat["Value"], familyDict);
                    if len(r)>0:
                        allRecords.append(r);
                        dictRecordArray.append(dictRecord)
                    
            except RestError as e:
                msg = "REST API error when retrieving {0} student records " + \
                      "in class {1} with message {2}" \
                      .format(str(len(classStudentsInfoDict)), aClassRecord["Name"],
                              str(e));
                logging.debug(msg);
                logging.warning('No student records available for class {0}'.format(aClassRecord["Name"]));
                
        saveRecords(allRecords)
    except Exception as ex:
        msg = "Connection failed: {0}".format(ex);
        logging.exception(msg);

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
