# import json
# from os.path import join
# from typing import List, Dict, Union, Tuple, Type
# from litespeed import App, start_with_args, route
# from src.util.litespeedx import multiroute, Response, Request, JSend
# from sqlite3 import connect, Row, DatabaseError
# from http import HTTPStatus as ResponseCode
# import jsonpatch
#
# db_path = "local.db"
# RestResponse = Union[Response, Dict, Tuple[Dict, int], Tuple[Dict, int, Dict]]
#
#
# def __read_sql_file(file: str, strip_terminal=False):
#     with open(file, "r") as f:
#         r = f.read()
#         if strip_terminal and r[-1] == ';':
#             return r[:-1]
#         else:
#             return r
#
#
# def __reformat_url(url: str, base: str = None):
#     if base is None:
#         base = "http://localhost:8000"
#     return join(base, url)
#
#
# def __reformat_file_row(row: Row) -> Dict:
#     tag_list: List[str] = [] if row['tags'] is None else row['tags'].split()
#     tags = []
#     for tag in tag_list:
#         tags.append({
#             'id': tag,
#             "url": __reformat_url(f"api/tags/{tag}")
#         })
#     return {
#         'id': row['id'],
#         'url': __reformat_url(f"api/files/{row['id']}"),
#         'internal_path': row['path'],
#         'mime': row['mime'],
#         'name': row['name'],
#         'description': row['description'],
#         'tags': tags
#     }
#
#
# def __reformat_tag_row(row: Row) -> Dict:
#     return {
#         'id': row['id'],
#         'url': __reformat_url(f"api/tags/{row['id']}"),
#         'name': row['name'],
#         'description': row['description'],
#         'count': row['count'],
#     }
#
#
# def __validate_required_fields(d: Dict, fields: List[Tuple[str, Type, str]], errors: List[str]):
#     for field, type, typename in fields:
#         if field not in d:
#             errors.append(f"Missing required field: '{field}'")
#         elif not isinstance(d[field], type):
#             errors.append(f"Field '{field}' did not receive expected type '{typename}', received '{d[field]}'")
#
#
# def __validate_expected_fields(d: Dict, fields: List[Tuple[str, Type, str]], errors: List[str]):
#     for field, type, typename in fields:
#         if field in d and not isinstance(d[field], type):
#             errors.append(f"Field '{field}' did not receive expected type '{typename}', received '{d[field]}'")
#
#
# def __validate_unexpected_fields(d: Dict, fields: List[str], errors: List[str]):
#     for field in d:
#         if field not in fields:
#             errors.append(f"Unknown field received: '{field}'")
#
# def init_tables():
#     with connect(db_path) as conn:
#         cursor = conn.cursor()
#         cursor.execute(__read_sql_file("static/sql/file/create.sql"))
#         cursor.execute(__read_sql_file("static/sql/tag/create.sql"))
#         cursor.execute(__read_sql_file("static/sql/file_tag/create.sql"))
#         conn.commit()
#
#
# def add_routes():
#     route(function=index)
#     route("api-ref", function=index)
#     route("api/files", function=get_files, methods="GET")
#     multiroute("api/files/(\d*)", get=get_file, put=update_file, patch=patch_file, delete=delete_file)
#     multiroute("api/files/(\d*)/tags", get=get_file_tags, put=update_file_tags, delete=delete_file_tags)
#     multiroute("api/tags", get=get_tags)
#     multiroute("api/tags/(\d*)", get=get_tag)
#
#
# def index(request: Request) -> Dict:
#     base_url = "http://localhost:8000"
#     formatted_urls = []
#     for url in App._urls:
#         formatted_urls.append(join(base_url, str(url)))
#     return JSend.success(formatted_urls)
#
#
# def get_files(request: Request) -> Dict:
#     with connect(db_path) as conn:
#         cursor = conn.cursor()
#         cursor.row_factory = Row
#         query = __read_sql_file("static/sql/file/select.sql")
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         formatted = []
#         for row in rows:
#             formatted.append(__reformat_file_row(row))
#         return JSend.success(formatted)
#
#
# def get_file(request: Request, id: str) -> RestResponse:
#     with connect(db_path) as conn:
#         cursor = conn.cursor()
#         cursor.row_factory = Row
#         query = __read_sql_file("static/sql/file/select_by_id.sql")
#         cursor.execute(query, id)
#         rows = cursor.fetchall()
#         if len(rows) < 1:
#             return JSend.fail(f"No file found with the given id: '{id}'"), ResponseCode.NOT_FOUND
#         elif len(rows) > 1:
#             return JSend.fail(f"Too many files found with the given id: '{id}'"), ResponseCode.CONFLICT
#         return JSend.success(__reformat_file_row(rows[0]))
#
#
# def delete_file(request: Request, id: str) -> Dict:
#     try:
#         with connect(db_path) as conn:
#             cursor = conn.cursor()
#             query = __read_sql_file("static/sql/file/delete_by_id.sql")
#             cursor.execute(query, id)
#             conn.commit()
#         return JSend.success(f"Deleted file '{id}'")
#     except DatabaseError as e:
#         return JSend.fail(e)
#
#
# def patch_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     optional_fields = [("name", str, "string"), ("path", str, "string"), ("mime", str, "string"),
#                        ("description", str, "string")]
#     expected_fields = [name for (name, _, _) in optional_fields]
#
#     errors = []
#     __validate_expected_fields(file_json, optional_fields, errors)
#     __validate_unexpected_fields(file_json, expected_fields, errors)
#
#     if len(errors) > 0:
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         parts: List[str] = [f"{key} = :{key}" for key in file_json]
#         query = f"UPDATE file SET {', '.join(parts)} WHERE id = :id"
#
#         file_json['id'] = id
#         with connect(db_path) as conn:
#             cursor = conn.cursor()
#             cursor.execute(query, file_json)
#             conn.commit()
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e)
#
#
#
# def update_file(request: Request, id: str) -> RestResponse:
#     body = request['BODY']
#     file_json = json.loads(body)
#
#     required_fields = [("name", str, "string"), ("path", str, "string"), ("mime", str, "string"),
#                        ("description", str, "string")]
#     required_field_names = [name for (name, _, _) in required_fields]
#
#     errors = []
#     __validate_required_fields(file_json, required_fields, errors)
#     __validate_unexpected_fields(file_json, required_field_names, errors)
#
#     if len(errors) > 0:
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         file_json['id'] = id
#         with connect(db_path) as conn:
#             cursor = conn.cursor()
#             query = __read_sql_file("static/sql/file/update.sql")
#             cursor.execute(query, file_json)
#             conn.commit()
#
#         return b'', ResponseCode.NO_CONTENT, {}
#     except DatabaseError as e:
#         return JSend.fail(e)
#
#
# def create_file(request: Request) -> RestResponse:
#     body = request['BODY']
#     post_file = json.loads(body)
#     errors = []
#
#     __validate_required_fields(post_file, [("path", str, "string")], errors)
#     __validate_expected_fields(post_file,
#                                [("name", str, "string"), ("mime", str, "string"), ("description", str, "string")],
#                                errors)
#     __validate_unexpected_fields(post_file, ['name', 'path', 'mime', 'description'], errors)
#
#     optional_fields = ['name', 'mime', 'description']
#     for opt in optional_fields:
#         if opt not in post_file:
#             post_file[opt] = ""
#
#     if len(errors) > 0:
#         return JSend.fail(errors), ResponseCode.BAD_REQUEST
#     try:
#         with connect(db_path) as conn:
#             cursor = conn.cursor()
#             query = __read_sql_file("static/sql/file/insert.sql")
#             cursor.execute(query, post_file)
#             conn.commit()
#             id = cursor.lastrowid
#             file = {
#                 'id': id,
#                 'url': __reformat_url(f"api/files/{id}"),
#             }
#         return JSend.success(file), ResponseCode.CREATED, {'Location': file['url']}
#     except DatabaseError as e:
#         return JSend.fail(e)
#
#
# def get_file_tags(request: Request, id: str) -> RestResponse:
#     with connect(db_path) as conn:
#         cursor = conn.cursor()
#         cursor.row_factory = Row
#
#         file_query = __read_sql_file("static/sql/file/select_by_id.sql")
#         cursor.execute(file_query, id)
#         files = cursor.fetchall()
#         if len(files) < 1:
#             return JSend.fail(f"No file found with the given id: '{id}'"), ResponseCode.NOT_FOUND
#         elif len(files) > 1:
#             return JSend.fail(f"Too many files found with the given id: '{id}'"), ResponseCode.CONFLICT
#
#         tag_id_list: List[str] = [] if files[0]['tags'] is None else files[0]['tags'].split()
#
#         internal_tag_query = __read_sql_file("static/sql/tag/select.sql", True)
#         tag_query = f"SELECT * FROM ({internal_tag_query}) WHERE tag.id IN ({'?' * len(tag_id_list)}) "
#         cursor.execute(tag_query, tag_id_list)
#         tags = cursor.fetchall()
#         formatted = []
#         for tag in tags:
#             formatted.append(__reformat_tag_row(tag))
#         return JSend.success(formatted)
#
#
# def patch_file_tags(request: Request):
#     pass
#
#
# def update_file_tags(request: Request):
#     pass
#
#
# def delete_file_tags(request: Request):
#     pass
#
#
# if __name__ == "__main__":
#     print("\n".join(App._urls))
#     init_tables()
#     add_routes()
#     start_with_args()
