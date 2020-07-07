import os
import shutil
import unittest
from src.util import path_util


class TestPathUtil(unittest.TestCase):
    playground_path = os.path.join(os.getcwd(), "test_playground", "path_util")
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

