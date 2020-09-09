from os.path import join


# This is primarily for me to group constants together
# None of these classes should be instantiated
def append_get_args(path: str, **kwargs) -> str:
    args = []
    for keyword in kwargs:
        value = kwargs[keyword]
        # TODO sanitize keyword and value
        args.append(f"{keyword}={value}")

    if len(args) > 0:
        return path + "?" + "&".join(args)
    return path


def web_join(*args) -> str:
    # Join on my system inserts \\
    # which works great for file systems
    # but bad for a regex parsing html paths
    # (which route does to allow capturing certain portions of the path)
    return join(*args).replace('\\', '/')


# It may be dumb to have this all by itself, BUT
# makes it easier to differentiate this root from the other roots in this file
# also, i dont have to type global root
class WebRoot:
    root = "/"


class Static:
    root = WebRoot.root
    html = web_join(root, "html")
    image = join(root, "img")
    js = web_join(root, "js")
    css = web_join(root, "css")

    @classmethod
    def get_css(cls, path_or_regex: str) -> str:
        return web_join(cls.css, path_or_regex)

    @classmethod
    def get_javascript(cls, path_or_regex: str) -> str:
        return web_join(cls.js, path_or_regex)

    @classmethod
    def get_image(cls, path_or_regex: str) -> str:
        return web_join(cls.image, path_or_regex)


class FilePage:
    root = web_join(WebRoot.root, "file")
    view_file = web_join(root, "view")
    index_list = web_join(root, "list")

    @classmethod
    def get_view_file(cls, id: int):
        return append_get_args(cls.view_file, id=id)

    @classmethod
    def get_index_list(cls, page: int):
        return append_get_args(cls.index_list, page=page)


class TagPage:
    root = web_join(WebRoot.root, "tag")
    view_tag = web_join(root, "view")
    index_list = web_join(root, "list")

    @classmethod
    def get_view_tag(cls, id: int):
        return append_get_args(cls.view_tag, id=id)

    @classmethod
    def get_index_list(cls, page: int):
        return append_get_args(cls.index_list, page=page)


class UploadPage:
    root = web_join(WebRoot.root, "upload")
    action_root = web_join(root, "action")

    upload_file = web_join(root, "file")
    action_upload_file = web_join(action_root, "file")

    add_file = web_join(root, "path")
    action_add_file = web_join(action_root, "path")
