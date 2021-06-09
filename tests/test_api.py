import itertools
from multiprocessing.context import Process
from shutil import copyfile
from typing import Any, List

from FileTagServer.DBI.models import File, Tag

source_db = "../examples/example.db"
test_db = "../examples/test.db"

import pytest
from FileTagServer import config
from FileTagServer.DBI import common
from FileTagServer.API import file as file_api
from FileTagServer.REST import main

url = "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def create_db():
    config.db_path = source_db
    common.initialize_database()
    yield


@pytest.fixture(autouse=True)
def reset_db():
    copyfile(source_db, test_db)
    yield


def run():
    config.db_path = test_db
    return main.run(host="localhost", port=8000, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def server():
    proc = Process(target=run, args=(), daemon=True)
    proc.start()
    yield
    proc.kill()  # Cleanup after test


test_tags = [
    Tag(id=1, name="Public Domain", count=1),
    Tag(id=2, name="Personal", count=2),
    Tag(id=3, name="Example", count=3)
]
test_files = [
    File(id=1, path='examples/json.json', mime="application/json", name="json sample",
         tags=[test_tags[1], test_tags[2]]),
    File(id=2, path='examples/text.txt', mime="text/plain", name="text sample", tags=[test_tags[1], test_tags[2]]),
    File(id=7, path="examples/Public Domain Icon.svg", mime="image/svg+xml", name="Public Domain Icon",
         tags=[test_tags[0], test_tags[2]])
]


def test_get_files():
    files = file_api.get_files(url)
    assert files == test_files


def all_permutations(iterable:List[Any]) -> List[Any]:
    for r in range(len(iterable)):
        for perm in itertools.permutations(iterable,r):
            yield perm

def test_get_files_tags():
    fields_set = ['id', 'path', 'mime', 'name', 'tags']
    for fields in all_permutations(fields_set):
        set_fields = set(fields)
        if len(set_fields) == 0:
            set_fields = None # Special case

        for f in test_files:
            file = file_api.get_file(url, f.id, fields)
            fielded_f = f.copy(include=set_fields)
            assert file == fielded_f, (fields, set_fields, file, fielded_f)

#
#
# def test_405_files():
#     methods = ['PUT', 'PATCH', 'DELETE']
#     body = [b'']
#     code = HTTPStatus.METHOD_NOT_ALLOWED
#     headers = {}
#     for m in methods:
#         response = internal_fetch(__files, m)
#         assert_response(response, body, code, headers)
#
#
# def test_get_files():
#     def format_sql_result(json):
#         return [__reformat_file_row(r) for r in json]
#
#     # Get Args, sql result (as json str), status, headers
#     tests = [
#         (
#             {},
#             dict_to_body(JSend.success(format_sql_result(json.loads(
#                 '[{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"},{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"}]')))),
#             HTTPStatus.OK,
#             {}
#         ),
#         (
#             {'sort': '+name'},
#             dict_to_body(JSend.success(format_sql_result(json.loads(
#                 '[{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"},{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"}]')))),
#             HTTPStatus.OK,
#             {}
#         ),
#         (
#             {'sort': '-name'},
#             dict_to_body(JSend.success(format_sql_result(json.loads(
#                 '[{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"},{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"}]')))),
#             HTTPStatus.OK,
#             {}
#         ),
#         (
#             {'sort': '+blanchin'},
#             dict_to_body(JSend.fail(json.loads('{"sort": ["Unexpected field \'blanchin\'; expected: id, name, mime, description, path"]}'))),
#             HTTPStatus.BAD_REQUEST,
#             {}
#         ),
#     ]
#     for args, body, status, headers in tests:
#         response = internal_fetch(__files, 'GET', method_payload=args)
#         assert_response(response, body, status, headers)
