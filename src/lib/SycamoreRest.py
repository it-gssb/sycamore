# to handle  data retrieval
import urllib3
from urllib3 import request
# to handle certificate verification
import certifi
# to manage json data
import json
# for pandas dataframes
import pandas
from typing import Dict

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

        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            headers={'Authorization': 'Bearer ' + self.token,
                     'Content-type': 'application/json; charset=utf-8'})


    def retrieve(self, query: str) -> Dict[str, str]:
        # handle certificate verification and SSL warnings
        # https://urllib3.readthedocs.io/en/latest/user-guide.html#ssl

        # get data from the API
        url = self.MAIN_URL + query
        print(url)
        response = self.http.request('GET', url)
        
        if response.status != 200:
            msg = 'Request ' + url + ' failed with code ' + str(response.status);
            raise RestError(msg)

        return json.loads(response.data.decode('utf-8'))

    def getFamilies(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Families')
        return pandas.DataFrame.from_records(data, index="ID")

    def getFamily(self, familyId: int) -> Dict[str, str]:
        data = [self.retrieve('/Family/' + str(familyId) + '')]
        return pandas.DataFrame.from_records(data, index=[familyId])

    def getStudents(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Students')
        return pandas.DataFrame.from_records(data, index="ID")

    def getStudent(self, studentId: int) -> pandas.DataFrame:
        data = [self.retrieve('/Student/' + str(studentId) + '')]
        return pandas.DataFrame.from_records(data, index=[studentId])

    def getContacts(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Contacts')
        return pandas.DataFrame.from_records(data, index="ID")

    def getClasses(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Classes?quarter=0')
        return pandas.DataFrame.from_records(data['Period'], index="ID")

    def getEmployees(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Employees')
        return pandas.DataFrame.from_records(data, index="ID")

    def getYears(self) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Years')
        return pandas.DataFrame.from_records(data, index="ID")

    def getYear(self, yearId: int) -> pandas.DataFrame:
        data = self.retrieve('/School/' + str(self.schoolId) + '/Years/' + str(yearId) + '')
        return pandas.DataFrame.from_records(pandas.json_normalize(data), index=[yearId])
