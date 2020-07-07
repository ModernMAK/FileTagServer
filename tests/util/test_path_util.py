import os
import shutil
import unittest
from src.util import path_util


class TestPathUtil(unittest.TestCase):
    playground_path = os.path.join(os.getcwd(), "test_playground")
    module_name = path_util.__name__

    def test_formatted_ext(self):
        pairs = [
            ('file.png', 'png'),
            ('test/file.PNG', 'png'),
            ('test', '')
        ]
        for (input, expected) in pairs:
            output = path_util.get_formatted_ext(input)
            error_msg = f"{self.module_name}.get_formatted_ext('{input}') returned '{output}'; expected '{expected}'"
            assert output == expected, error_msg

    def test_enforce_dirs_exists(self):
        # Files are relative to the playground path
        # Pairs are path, should_exist pairs
        pairs = [
            ('enforce_dirs/test.png', 'enforce_dirs', True),
            ('enforce_dirs/test_folder', 'enforce_dirs/test_folder', True),
            ('enforce_dirs/test', 'enforce_dirs', False)
        ]
        for (input, created, expected) in pairs:
            input = os.path.join(self.playground_path, input)
            created = os.path.join(self.playground_path, created)
            try:
                shutil.rmtree(created)
            except FileNotFoundError:
                pass
            path_util.enforce_dirs_exists(input)
            output = os.path.exists(created)
            error_msg = f"{self.module_name}.enforce_dirs_exists('{input}'). Exists: '{output}' Expected '{expected}'"

            assert output == expected, error_msg
