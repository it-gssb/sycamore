from __future__ import annotations

from lib import SycamoreRest
from lib import SycamoreEntity
import pandas
import os

##           

ENTITIES = [
    SycamoreEntity.Definition(name='school', index_col=None, url='/School/{school_id}'),
    SycamoreEntity.Definition(name='families', index_col='ID', url='/School/{school_id}/Families'),
    SycamoreEntity.Definition(name='family_contacts', index_col='ID', url='/Family/{entity_id}/Contacts', iterate_over='families'),
    SycamoreEntity.Definition(name='family_details', index_col=None, url='/Family/{entity_id}', iterate_over='families'),
    SycamoreEntity.Definition(name='family_students', index_col='ID', url='/Family/{entity_id}/Students', iterate_over='families'),
    SycamoreEntity.Definition(name='students', index_col='ID', url='/School/{school_id}/Students'),
    SycamoreEntity.Definition(name='student_classes', index_col='ID', url='/Student/{entity_id}/Classes?quarter=0&format=1', iterate_over='students'),
    SycamoreEntity.Definition(name='student_details', index_col=None, url='/Student/{entity_id}', iterate_over='students'),
    SycamoreEntity.Definition(name='student_custom_fields', index_col=None, url='/Student/{entity_id}/Statistics', iterate_over='students'),
    SycamoreEntity.Definition(name='contacts', index_col='ID', url='/School/{school_id}/Contacts'),
    SycamoreEntity.Definition(name='classes', index_col='ID', url='/School/{school_id}/Classes?quarter=0', data_location='Period'),
    SycamoreEntity.Definition(name='class_details', index_col=None, url='/School/{school_id}/Classes/{entity_id}', iterate_over='classes'),
    SycamoreEntity.Definition(name='class_students', index_col='ID', url='/Class/{entity_id}/Directory', iterate_over='classes'),
    SycamoreEntity.Definition(name='employees', index_col='ID', url='/School/{school_id}/Employees'),
    SycamoreEntity.Definition(name='years', index_col='ID', url='/School/{school_id}/Years'),
    SycamoreEntity.Definition(name='years_details', index_col=None, url='/School/{school_id}/Years/{entity_id}', iterate_over='years'),
]

def _get_entity(entity_name: str):
    for entity in ENTITIES:
        if entity.name == entity_name:
            return entity
    raise InvalidEntity

class InvalidEntity(Exception):
    pass

class InvalidCacheDir(Exception):
    pass

class InvalidRestInterface(Exception):
    pass

class Cache:
    def __init__(self, rest: SycamoreRest.Extract = None, cache_dir: str = None, reload: bool = False):
        self.rest = rest

        self.entities = {}
        self.cache_dir = cache_dir

        if self.cache_dir is not None:
            # If the cache_dir is set, but it's pointing to something that's not
            # a directory, we want to fail early.
            if os.path.exists(self.cache_dir) and not os.path.isdir(self.cache_dir):
                raise InvalidCacheDir('cache_dir "{}" is not a directory'.format(self.cache_dir))

            if not reload:
                try:
                    self._loadFromFiles()
                    # No need to contine, we're done initializing.
                    return
                except Exception as ex:
                    print('Could not load from files ({}), loading from remote."'.format(ex))
                    # Fall through to loading from remote.

        self._loadFromRemote()

        if self.cache_dir is not None:
            self._saveToFiles()


    def _loadFromFiles(self):
        if self.cache_dir is None:
            raise InvalidCacheDir('cache_dir not set')

        if not os.path.exists(self.cache_dir):
            raise InvalidCacheDir('cache_dir "{}" does not exist'.format(self.cache_dir))

        if not os.path.isdir(self.cache_dir):
            raise InvalidCacheDir('cache_dir "{}" is not a directory'.format(self.cache_dir))

        try:
            for entity in ENTITIES:
                self.entities[entity.name] = pandas.read_pickle(
                    os.path.join(self.cache_dir, '{name}.pkl'.format(name=entity.name)))
        except:
            # If anything goes wrong, clear the cache
            self.entities = {}
            raise

    def _loadFromRemote(self):
        if not self.rest:
            raise InvalidRestInterface('REST interface not set')

        for entity in ENTITIES:
            print('Loading {}'.format(entity))
            _ = self.get(entity.name)

    def _saveToFiles(self):
        # If target directory doesn't exist, create it.
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)
        elif not os.path.isdir(self.cache_dir):
            raise InvalidCacheDir('cache_dir "{}" is not a directory'.format(self.cache_dir))

        for entity in ENTITIES:
            if entity.name not in self.entities:
                continue
            self.entities[entity.name].to_pickle(
                os.path.join(self.cache_dir, '{name}.pkl'.format(name=entity.name)))

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
                entity_iterate_over = self.get(entity.iterate_over)
                total = len(entity_iterate_over.index)
                count = 0
                for entity_id, _ in entity_iterate_over.iterrows():
                    count = count + 1
                    try:
                        print('   entity={} percent={} entity_id={}'.format(entity.name, round(count * 100 / total), entity_id))
                        data = self.rest.get(entity, entity_id=entity_id)
                        if data is not None:
                            # Add the "[iterate_over]" entity_id as additional column for lookups
                            data.insert(loc=0, column=(entity.iterate_over + "_id"), value=entity_id)
                            all_data.append(data)
                    except KeyboardInterrupt:
                        raise
                    except:
                        print('Failed to load entity.name={} entity_id={}'.format(entity.name, entity_id))
                        raise

                self.entities[entity.name] = pandas.concat(all_data)

        return self.entities[entity.name]
