from typing import List, Optional

from fastapi import Form
from starlette import status
from starlette.responses import RedirectResponse

from FileTagServer.DBI.file import FullModifyFileQuery
from FileTagServer.REST.routing import reformat
from FileTagServer.WEB.common import web_app
from FileTagServer.DBI import tag, file
from FileTagServer.WEB.routing import file_edit_submit_route, file_edit_route, file_route


def dummy():
    pass


# @web_app.post(response_model=List[AutoComplete])
# def get_tag_autocomplete(name: str) -> List[AutoComplete]:
#     return autocomplete_tag(name)


@web_app.post(file_edit_submit_route)
def update_file(file_id: int, name: Optional[str] = Form(None), description: Optional[str] = Form(None),
                tags: Optional[str] = Form(None)):
    tag_list = tags.splitlines(False)
    # TODO more robust newline-tag handler (current one can allow blank tags, which are a no-go)
    full_tags = tag.ensure_tags_exist(tag_list)
    tag_ids = [t.id for t in full_tags]
    q = FullModifyFileQuery(id=file_id, description=description, name=name, tags=tag_ids)
    file.modify_file(q)
    url = reformat(file_route, file_id=file_id)
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
