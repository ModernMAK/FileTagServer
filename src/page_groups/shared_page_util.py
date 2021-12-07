from typing import List, Dict, Any, Union

from src.page_groups import routing


# This navbar is shared and should be used across the site
# It relies on the navbar mustache template
def get_navbar_context(active: Union[str, List[str]] = None) -> List[Dict[str, Any]]:
    def link_helper(link: str, text: str) -> Dict[str, Any]:
        info = {'path': link, 'text': text}
        nonlocal active
        if active is not None:
            status = "active"
            if isinstance(active, str):
                active = [active]
            # Allow the text OR the link to determine if the page is active
            if text in active or link in active:
                info['status'] = status

        return {'link': info}

    def dropdown_helper(dropdown, links):
        fixed = []
        for link in links:
            link = link['link']
            fixed.append(link)

        info = {'text': dropdown, 'links': fixed}
        return {'dropdown': info}

    # TODO use dropdown if we allow local path uploads
    # otherwise, dont use dropdown, just link to upload page
    return [
        link_helper(routing.FilePage.root, "File"),
        link_helper(routing.TagPage.root, "Tag"),
        dropdown_helper("Upload",
                        [link_helper(routing.UploadPage.add_file, "Path"),
                         link_helper(routing.UploadPage.upload_file, "File")]),
        dropdown_helper("Api",
                        [link_helper(routing.ApiPage.get_file_list(), "File")])
    ]
