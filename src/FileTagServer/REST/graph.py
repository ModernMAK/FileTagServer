import graphene
from graphene import String, ObjectType, Schema
from starlette.graphql import GraphQLApp

from FileTagServer.DBI import file as file_api, tag as tag_api
from FileTagServer.DBI.common import Util
from FileTagServer.DBI.file import FilesQuery
from FileTagServer.DBI.tag import TagsQuery
from FileTagServer.REST.common import rest_api
from FileTagServer.REST.routing import graph_route


def dummy():
    pass

class TagGraph(ObjectType):
    id = graphene.Int()
    name = graphene.String()
    description = graphene.String()
    count = graphene.Int()

class FileGraph(ObjectType):
    id = graphene.Int()
    path = graphene.String()
    name = graphene.String()
    description = graphene.String()
    mime = graphene.String()
    tags = graphene.List(TagGraph)

class Query(ObjectType):
    files = graphene.List(FileGraph)
    tags = graphene.List(TagGraph)

    def resolve_files(root, info):
        q = FilesQuery()
        r = file_api.get_files(q)
        d = Util.dict(r)
        return d

    def resolve_tags(root, info):
        q = TagsQuery()
        r = tag_api.get_tags(q)
        d = Util.dict(r)
        return d

rest_api.add_route(graph_route, GraphQLApp(schema=Schema(query=Query)))
