import os


def project_root():
    return os.getcwd()


def get_formatted_ext(source: str) -> str:
    path, ext = os.path.splitext(source)
    if ext is None:
        ext = path
    ext = ext.lstrip('.')
    ext = ext.lower()
    return ext


def enforce_dirs_exists(file_path: str):
    try:
        base, ext = os.path.splitext(file_path)
        if ext == '':
            file_path = base
        else:
            file_path = os.path.dirname(base)
        os.makedirs(file_path)
    except FileExistsError:
        pass
