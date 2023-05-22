from copy import deepcopy
from munch import Munch
import hashlib
import json
import os


def folder_check(directory):
    if not os.path.isdir(directory):
        os.mkdir(directory)


# Stores persistent player and server configurations
class PersistenceManager():

    class PersistenceObject(Munch):

        # Prevent deletion of root keys
        def __delitem__(self, key):
            if key in ['server', 'player']:
                self[key] = {}
            return super().__delitem__(key)


        # Prevent assignment to root keys
        def __setitem__(self, key, value):
            if not isinstance(value, dict):
                raise AttributeError(f"Root attribute '{key}' must be a dictionary, assign '{value}' to a key instead")
            return super().__setitem__(key, value)


    def __init__(self, server_name):
        # The server's persistent configuration will reside in the 'server' key
        # Individual players will have their own dictionary in the 'player' key
      
        self._name = server_name
        self._hash = int(hashlib.sha1(self._name.encode("utf-8")).hexdigest(), 16) % (10 ** 12)
        self._config_path = os.path.join(constants.configDir, 'amscript', 'pstconf')
        self._path = os.path.join(self._config_path, f"{self._hash}.json")
        self._data = None

        # Retrieve data if it exists
        # print(self._path)
        if os.path.exists(self._path):
            with open(self._path, 'r+') as f:
                try:
                    self._data = self.PersistenceObject(json.load(f))
                except json.JSONDecodeError:
                    pass

        # Else instantiate new object
        if not self._data:
            self._data = self.PersistenceObject({"server": {}, "player": {}})

        self._original_data = deepcopy(self._data)
        self.clean_keys()


    # Fixes deleted keys
    def clean_keys(self):
        try:
            if not self._data['server']:
                self._data.update({'server': {}})
        except KeyError:
            self._data.update({'server': {}})

        try:
            if not self._data['player']:
                self._data.update({'player': {}})
        except KeyError:
            self._data.update({'player': {}})


    # Writes persistent config to disk
    def write_config(self):
        self.clean_keys()

        # If data is not what it started with, write persistent config
        if self._data != self._original_data:
            folder_check(self._config_path)
            with open(self._path, 'w+') as f:
                json.dump(self._data, f, indent=4)

        # If data is empty, delete persistent config if it exists in file
        if not self._data['server'] and not self._data['player']:
            if os.path.exists(self._path):
                os.remove(self._path)
                
     
    # Resets data, and deletes file on disk
    def purge(self):
        self._data = PersistenceObject({"server": {}, "player": {}})
        self.write_config()
    
    

pst_mgr = PersistenceManager("test")
test = pst_mgr._data
# test['server'] = 10
test.server['test'] = 69
# del test['server']
pst_mgr.write_config()
