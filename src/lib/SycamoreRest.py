# to handle  data retrieval
import urllib3
from urllib3 import request
# to handle certificate verification
import certifi
# to manage json data
import json
# for pandas dataframes
import pandas

import logging

##           

class RestError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value);

class Extract:
    MAIN_URL = 'https://app.sycamoreschool.com/api/v1'

    def __init__(self, schoolId: int, token: str):
        self.schoolId = schoolId
        self.token = token

    def retrieve(self, query: str):
        # handle certificate verification and SSL warnings
        # https://urllib3.readthedocs.io/en/latest/user-guide.html#ssl
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())

        # get data from the API
        url = self.MAIN_URL + query
        print(url)
        response = http.request(
            'GET',
            url,
            headers={'Authorization': 'Bearer ' + self.token,
                     'Content-type': 'application/json; charset=utf-8'})
        
        if response.status != 200:
            msg = 'Request ' + url + ' failed with code ' + str(response.status);
            raise RestError(msg)

        return json.loads(response.data.decode('utf-8'))

    def getFamilies(self):
        data = self.retrieve('/School/' + str(self.schoolId) + '/Families')
        return pandas.json_normalize(data)

    def getStudents(self):
        # "ID": 987123456,
        # "FamilyID": 123654,
        # "Family2ID": 0,
        # "UserID": 0,
        # "StudentCode": "MUS1234-5",
        # "FirstName": "Max",
        # "LastName": "Mustermann",
        # "Grade": -1,
        # "GradYear": 0,
        # "Graduated": 0,
        # "ExternalID": "8765"
        data = self.retrieve('/School/' + str(self.schoolId) + '/Students')
        return pandas.json_normalize(data)

    def getContacts(self):
        data = self.retrieve('/School/' + str(self.schoolId) + '/Contacts')
        return pandas.json_normalize(data)

    def getClasses(self):
        data = self.retrieve('/School/' + str(self.schoolId) + '/Classes')
        return pandas.json_normalize(data)

    def getEmployees(self):
        data = self.retrieve('/School/' + str(self.schoolId) + '/Employees')
        return pandas.json_normalize(data)

    def getStudent(self, studentId: int):
        data = self.retrieve('/Student/' + str(studentId) + '')
        return pandas.json_normalize(data)

