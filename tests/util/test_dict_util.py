import os
import unittest
from src.util import dict_util, path_util


class TestDictUtil(unittest.TestCase):
    playground_path = os.path.join(os.getcwd(), "test_playground/dict_util")
    module_name = dict_util.__name__

    def get_file_path(self, path):
        return os.path.join(self.playground_path, path)

    def test_write_and_read_dict(self):
        ignore = [dict_util.DictFormat.xml, dict_util.DictFormat.ini]
        data = [
            {'A': 'Hello World'}
        ]
        if len(ignore) > 0:
            print(f"Dict Util:")
        for format in dict_util.DictFormat:
            # XML does not support reading
            # INI supports reading but its janky
            if format in ignore:
                print(f"\tLimited support for {format} (No Tests Run)")
                continue
            for i in range(len(data)):
                f_name = f"{i}.{str(format)}"
                f_path = self.get_file_path(f_name)
                d = data[i]
                path_util.enforce_dirs_exists(f_path)
                dict_util.write_dict(f_path, d, format)
                result = dict_util.read_dict(f_path, format)
                assert d == result
