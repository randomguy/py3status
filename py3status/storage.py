from __future__ import with_statement

import json
import os

from tempfile import NamedTemporaryFile


class Storage:

    data = {}
    initialized = False

    def init(self, py3_wrapper):
        self.py3_wrapper = py3_wrapper
        config_dir = os.path.dirname(
            py3_wrapper.config['i3status_config_path']
        )
        storage_path = os.path.join(config_dir, 'py3status.json')
        self.storage_path = storage_path
        try:
            with open(storage_path) as f:
                for line in f.readlines():
                    data = json.loads(line)
                    type = data['type']
                    module_name = data['module']
                    key = data['key']

                    if type == 'clear':
                        if module_name in self.data:
                            if key in self.data[module_name]:
                                del self.data[module_name][key]
                        continue

                    if type == 'json':
                        value = json.loads(data['value'])
                    if module_name not in self.data:
                        self.data[module_name] = {}
                    self.data[module_name][key] = value
            self.vacuum()
        except IOError:
            pass
        self.initialized = True

    @staticmethod
    def encode(module_name, key, value):

        data = json.dumps(value)
        data_type = 'json'

        stored_data = {
            'key': key,
            'module': module_name,
            'type': data_type,
            'value': data,
        }
        return json.dumps(stored_data)

    def vacuum(self):
        f = NamedTemporaryFile(dir=os.path.dirname(self.storage_path))
        for module_name, data in self.data.items():
            for key, value in data.items():
                f.write(self.encode(module_name, key, value))
                f.write('\n')
        f.flush()
        os.fsync(f.fileno())
        tmppath = f.name
        os.rename(tmppath, self.storage_path)

    def storage_set(self, module_name, key, value):
        if self.data.get(module_name, {}).get(key) == value:
            return

        if module_name not in self.data:
            self.data[module_name] = {}
        self.data[module_name][key] = value

        with open(self.storage_path, 'a') as f:
            f.write(self.encode(module_name, key, value))
            f.write('\n')

    def storage_get(self, module_name, key):
        return self.data.get(module_name, {}).get(key, None)

    def storage_clear(self, module_name, key=None):
        if module_name in self.data and key in self.data[module_name]:
            del self.data[module_name][key]

        stored_data = {
            'key': key,
            'module': module_name,
            'type': 'clear',
        }
        data = json.dumps(stored_data)

        with open(self.storage_path, 'a') as f:
            f.write(data)
            f.write('\n')

    def storage_keys(self, module_name):
        return self.data.get(module_name, {}).keys()
