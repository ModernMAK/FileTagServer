from os.path import join
from os import getcwd


# It may be dumb to have this all by itself, BUT
# makes it easier to differentiate this root from the other roots in this file
# also, i dont have to type global root
class LocalRoot:
    root = getcwd()


class Static:
    root = join(LocalRoot.root, "static")
    html = join(root, "html")
    js = join(root, "js")
    css = join(root, "css")
    image = join(root, "image")
    db = join(root, 'data')

    @classmethod
    def get_html(cls, path: str) -> str:
        return join(cls.html, path)

    @classmethod
    def get_database(cls, path: str) -> str:
        return join(cls.db, path)

    @classmethod
    def get_javascript(cls, path: str) -> str:
        return join(cls.js, path)

    @classmethod
    def get_css(cls, path: str) -> str:
        return join(cls.css, path)

    @classmethod
    def get_image(cls, path: str) -> str:
        return join(cls.image, path)
