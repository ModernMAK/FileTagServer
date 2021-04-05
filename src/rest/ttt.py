# import json
# from enum import Enum
#
# # from os.path import join
# from inspect import signature
# from typing import Callable, Dict, Any, Tuple, List, Union, Optional, Set, Type, ForwardRef, Mapping, AbstractSet
#
# from src.api.models import File, Tag
# from src.rest.decorators import Endpoint
#
#
# # STOLEN FROM https://stackoverflow.com/questions/19022868/how-to-make-dictionary-read-only-in-python
# from litespeed import route, start_with_args
# from pydantic import BaseModel, Field, validate_arguments, parse_obj_as
#
#
# class ReadOnlyDict(dict):
#     def __readonly__(self, *args, **kwargs):
#         raise RuntimeError("Cannot modify ReadOnlyDict")
#
#     __setitem__ = __readonly__
#     __delitem__ = __readonly__
#     pop = __readonly__
#     popitem = __readonly__
#     clear = __readonly__
#     update = __readonly__
#     setdefault = __readonly__
#     del __readonly__
#
#
# # Should always be get_path(*args,**kwargs):
# # keyword variables can be placed before *args
# # get_path(id:str,*args,**kwargs)
#
# # StarArgs = Tuple[Any,...]
# # PathSignature = Callable[[Union[List[Any,...], StarArgs], Dict[str, Any]], str]
# # MethodSignature = Callable[[Request,StarArgs], Response]
#
#
#
#
# # @file.methods.get
# # @validate_arguments
# # def file_get(request: Dict[str, Any], id: int) -> Dict:
# #     return {}
#
#
# # @endpoint
# # def path():
# #     return '/'
#
#
# # @APISchema
# # @files.methods.get
# # @validate_arguments
# # def files_get(request) -> List[File]:
# #     pass
#     # test_files = [File(id=1, file='example.text'), File(id=2, file='test.text'),
#     #               File(id=3, file='tutorial.text', tags=[Tag(id=1, name='test')])]
#     # include_keys = {'id': ..., 'tags': {'__all__': {'id', 'name'}}}
#     #
#     # a = test_files
#     # print(a)
#     # print(include_keys)
#     # b = [t.copy(include=include_keys) for t in a]
#     #
#     # def complex_print(i):
#     #     strs = [j.dict() for j in i]
#     #     return json.dumps(strs)
#     #
#     # print(f"A: {a}")
#     # a2 = complex_print(a)
#     # a3 = Util.json(a)
#     # print(f"A2: {a2}")
#     # print(f"A3: {a3}")
#     # print(f"A2=3: {a2 == a3}")
#     # print(f"B: {b}")
#     # print(f"B2: {complex_print(b)}")
#     # print(f"B3: {Util.json(b)}")
#     # return b
#
#
# # print("H")
# # print(files_get(None))
#
#
# @file.methods.get
# @validate_arguments
# def file_get(request, id: int):
#     return f'file {id}'
#
#
# @file_tags.methods.get
# @validate_arguments
# def file_tags_get(request, id: int):
#     return f'file {id} tags'
#
#
# path_args = {'file_id': "(\d+)"}
# route_args = {'no_end_slash': True}
#
# files.route(path_args, route_args)
# file.route(path_args, route_args)
# file_tags.route(path_args, route_args)
# #
# # print(files.path(**path_args))
# # print(file.path(**path_args))
# # print(file_tags.path(**path_args))
# # print(f'allowed: {file.methods.allowed}')
# # print(f'methods: {file.methods.lookup()}')
# # print(f'rev methods: {file.methods.reverse_lookup()}')
# # print(File.schema())
# # start_with_args()
