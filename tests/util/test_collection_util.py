import os
import shutil
import unittest
from src.util import collection_util


class TestCollectionUtil(unittest.TestCase):
    playground_path = os.path.join(os.getcwd(), "test_playground", "collection_util")
    module_name = collection_util.__name__

    def test_list_tuple_to_list(self):
        pairs = [
            (
                [('hi', 'dave'), ('will', 'i', 'dream'), ('dave', '?')],
                ['hi', 'dave', 'will', 'i', 'dream', 'dave', '?']),
        ]
        for (input, expected) in pairs:
            output = collection_util.list_tuple_to_list(input)
            assert output == expected, f"{output} != {expected}"

    def test_tuple_to_dict(self):
        pairs = [
            (('hi', 'dave'), ('a', 'b'), {'a': 'hi', 'b': 'dave'}),
            (('hi', 'dave'), ('a', 'b'), {'a': 'hi', 'b': 'dave'}),
        ]
        for (input, mapping, expected) in pairs:
            output = collection_util.tuple_to_dict(input, mapping)
            assert output == expected, f"{output} != {expected}"

    def test_get_unique_values_on_key(self):
        pairs = [
            ([{'key': 'hi'}, {'key': 'dave'}, {'key': 'hi'}], 'key', {'hi', 'dave'})
        ]
        for (input, key, expected) in pairs:
            output = collection_util.get_unique_values_on_key(input, key)
            assert output == expected, f"{output} != {expected}"

    def test_get_unique_values(self):
        pairs = [
            ({'a': ['yes', 'no'], 'b': ['stop', 'go go go'], 'c': ['yes', 'stop']}, {'yes', 'no', 'stop', 'go go go'})
        ]
        for (input, expected) in pairs:
            output = collection_util.get_unique_values(input)
            assert output == expected, f"{output} != {expected}"

    def test_group_dicts_on_key(self):
        pairs = [
            (
                [{'a': 0, 'b': 'YES'}, {'a': 1}, {'a': 0, 'b': 'NO'}],
                'a',
                {0: [{'a': 0, 'b': 'YES'}, {'a': 0, 'b': 'NO'}], 1: [{'a': 1}]}
            )
        ]
        for (input, key, expected) in pairs:
            output = collection_util.group_dicts_on_key(input, key)
            assert output == expected, f"{output} != {expected}"

    def test_create_lookup(self):
        # our tests are dicts, but any object could be supported
        def get_key_func(key):
            def wrapper(d):
                return d[key]
            return wrapper

        pairs = [
            (
                [{'id': 0, 'value': 'Zero'}, {'id': 1, 'value': 'Hero'}, {'id': 2, 'value': 'Nero'}],
                get_key_func('id'),
                {0: {'id': 0, 'value': 'Zero'}, 1: {'id': 1, 'value': 'Hero'}, 2: {'id': 2, 'value': 'Nero'}}
            )
        ]
        for (input, key_func, expected) in pairs:
            output = collection_util.create_lookup(input, key_func)
            assert output == expected, f"{output} != {expected}"

    def test_flatten(self):
        pairs = [
            (
                ['a', 'b', ['c', 'd', ['e', 'f', 'g']]],
                ['a', 'b', 'c', 'd', 'e', 'f', 'g']
            ),
            (
                ['a', 'b'],
                ['a', 'b']
            ),
            (
                ['a', 'b', []],
                ['a', 'b']
            )
        ]
        for (input, expected) in pairs:
            output = collection_util.flatten(input)
            assert output == expected, f"{output} != {expected}"
