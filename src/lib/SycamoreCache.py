from __future__ import annotations

from lib import SycamoreRest
from lib import SycamoreEntity
import pandas
import os

##           

ENTITIES = [
    SycamoreEntity.Definition(name='families', index_col='ID', url='/School/{school_id}/Families'),
    SycamoreEntity.Definition(name='family_contacts', index_col='ID', url='/Family/{entity_id}/Contacts', iterate_over='families'),
    SycamoreEntity.Definition(name='family_details', index_col=None, url='/Family/{entity_id}', iterate_over='families'),
    SycamoreEntity.Definition(name='family_students', index_col='ID', url='/Family/{entity_id}/Students', iterate_over='families'),
    SycamoreEntity.Definition(name='students', index_col='ID', url='/School/{school_id}/Students'),
    SycamoreEntity.Definition(name='student_classes', index_col=None, url='/Student/{entity_id}/Classes?quarter=0&format=1', iterate_over='students'),
    SycamoreEntity.Definition(name='student_details', index_col=None, url='/Student/{entity_id}', iterate_over='students'),
    SycamoreEntity.Definition(name='contacts', index_col='ID', url='/School/{school_id}/Contacts'),
    SycamoreEntity.Definition(name='classes', index_col='ID', url='/School/{school_id}/Classes?quarter=0', data_location='Period'),
    SycamoreEntity.Definition(name='employees', index_col='ID', url='/School/{school_id}/Employees'),
    SycamoreEntity.Definition(name='years', index_col='ID', url='/School/{school_id}/Years'),
    SycamoreEntity.Definition(name='years_details', index_col=None, url='/School/{school_id}/Years/{entity_id}', iterate_over='years'),
]

def _get_entity(entity_name: str):
    for entity in ENTITIES:
        if entity.name == entity_name:
            return entity
    raise InvalidEntity

class InvalidEntity:
    pass

class Cache:
    def __init__(self, rest: SycamoreRest.Extract = None, source_dir: str = None):
        self.rest = rest

        self.entities = {}

        if source_dir is not None:
            self._loadFromFiles(source_dir)

    def _loadFromFiles(self, source_dir: str):
        for entity in ENTITIES:
            self.entities[entity.name] = pandas.read_pickle(
                os.path.join(source_dir, '{name}.pkl'.format(name=entity.name)))

    def loadAll(self):
        for entity in ENTITIES:
            _ = self.get(entity.name)

    def saveToFiles(self, target_dir: str):
        for entity in ENTITIES:
            if entity.name not in self.entities:
                continue
            self.entities[entity.name].to_pickle(
                os.path.join(target_dir, '{name}.pkl'.format(name=entity.name)))

    def compare(self, other: 'Cache'):
        for entity in ENTITIES:
            print(self.get(entity.name).compare(other.get(entity.name)))

    def get(self, entity_name: str):
        entity = _get_entity(entity_name)
        if entity.name not in self.entities:
            if entity.iterate_over is None:
                self.entities[entity.name] = self.rest.get(entity)
            else:
                all_data = []
                for entity_id, _ in self.get(entity.iterate_over).iterrows():
                    data = self.rest.get(entity, entity_id=entity_id)
                    if data is not None:
                        # Add the "[iterate_over]" entity_id as additional column for lookups
                        data.insert(loc=0, column=(entity.iterate_over + "_id"), value=entity_id)
                        all_data.append(data)

                self.entities[entity.name] = pandas.concat(all_data)

        return self.entities[entity.name]
