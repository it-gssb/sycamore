from __future__ import annotations

# to handle  data retrieval
import urllib3
from urllib3 import request
# to handle certificate verification
import certifi
# to manage json data
import json
# for pandas dataframes
import pandas
from lib import SycamoreEntity
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

    def __init__(self, school_id: int, token: str):
        self.school_id = school_id
        self.token = token

        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            headers={'Authorization': 'Bearer ' + self.token,
                     'Content-type': 'application/json; charset=utf-8'})


    def _retrieve(self, query: str) -> Dict[str, str]:
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

    def get(self, entity: SycamoreEntity.Definition, entity_id: str = None) -> pandas.DataFrame:
        print(entity)
        data = self._retrieve(entity.url.format(school_id=self.school_id, entity_id=entity_id))
        if entity.data_location is not None:
            data = data[entity.data_location]
        if entity.iterate_over is not None:
            data = [data]
        return pandas.DataFrame.from_records(
            pandas.json_normalize(data),
            index=entity.index_col if entity.index_col is not None else [entity_id])
