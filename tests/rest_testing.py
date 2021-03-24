import json

import pytest

from src.util.litespeedx import JSend
from tests.litespeed_test import internal_fetch, assert_response, dict_to_body
from src.rest.file import __files
from http import HTTPStatus
from shutil import copyfile

from src.rest.file import App, __reformat_file_row
from src.rest.tag import App
import src.api.common as api
import src.rest.common as rest

source_db = "examples/example.db"
test_db = "examples/test.db"


@pytest.fixture(scope="session", autouse=True)
def create_db():
    api.db_path = source_db
    rest.init_tables()
    yield


@pytest.fixture(autouse=True)
def reset_db():
    copyfile(source_db, test_db)
    yield


def test_405_files():
    methods = ['PUT', 'PATCH', 'DELETE']
    body = [b'']
    code = HTTPStatus.METHOD_NOT_ALLOWED
    headers = {}
    for m in methods:
        response = internal_fetch(__files, m)
        assert_response(response, body, code, headers)


def test_get_files():
    def format_sql_result(json):
        return [__reformat_file_row(r) for r in json]

    # Get Args, sql result (as json str), status, headers
    tests = [
        (
            {},
            dict_to_body(JSend.success(format_sql_result(json.loads(
                '[{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"},{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"}]')))),
            HTTPStatus.OK,
            {}
        ),
        (
            {'sort': '+name'},
            dict_to_body(JSend.success(format_sql_result(json.loads(
                '[{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"},{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"}]')))),
            HTTPStatus.OK,
            {}
        ),
        (
            {'sort': '-name'},
            dict_to_body(JSend.success(format_sql_result(json.loads(
                '[{"id":2,"path":"examples/text.txt","mime":"text/plain","name":"text sample","description":null,"tags":"2,3"},{"id":1,"path":"examples/json.json","mime":"application/json","name":"json sample","description":null,"tags":"2,3"},{"id":7,"path":"examples/Public Domain Icon.svg","mime":"image/svg+xml","name":"Public Domain Icon","description":null,"tags":"1,3"}]')))),
            HTTPStatus.OK,
            {}
        ),
        (
            {'sort': '+blanchin'},
            dict_to_body(JSend.fail(json.loads('{"sort": ["Unexpected field \'blanchin\'; expected: id, name, mime, description, path"]}'))),
            HTTPStatus.BAD_REQUEST,
            {}
        ),
    ]
    for args, body, status, headers in tests:
        response = internal_fetch(__files, 'GET', method_payload=args)
        assert_response(response, body, status, headers)
