import mimetypes
import os

from fastapi import FastAPI
from fastapi.datastructures import Default
from pystache import Renderer
from starlette.responses import HTMLResponse, StreamingResponse, FileResponse



def create_app_instance(**kwargs):
    # Default to none for any api/doc urls
    default_none_keys = ["openapi_url", "docs_url", "redoc_url"]
    for key in default_none_keys:
        kwargs[key] = None if key not in kwargs else kwargs[key]

    # Default to HTML Response (unless overriden)
    kwargs["default_response_class"] = Default(HTMLResponse) if "default_response_class" not in kwargs else kwargs["default_response_class"]
    return FastAPI(**kwargs)


def create_renderer(**kwargs):
    kwargs["search_dirs"] = "../static/html/templates" if "search_dirs" not in kwargs else kwargs["search_dirs"]
    return Renderer(**kwargs)

# stolen from 'https://github.com/tiangolo/fastapi/issues/1240'
Kibi = 1024
Mebi = Kibi * Kibi
Gibi = Mebi * Kibi
BYTES_PER_RESPONSE = Gibi
BYTES_PER_CHUNK = Mebi


def chunk_generator_from_stream(stream, chunk_size, start, size):
    bytes_read = 0
    stream.seek(start)

    while bytes_read < size:
        bytes_to_read = min(chunk_size,
                            size - bytes_read)
        yield stream.read(bytes_to_read)
        bytes_read = bytes_read + bytes_to_read

    stream.close()


def serve_streamable(path: str, range: str = None):
    if range is None:
        return FileResponse(path)

    size = os.stat(path).st_size
    # !!! The file is closed in the chunk generator !!!
    file = open(path, mode="rb")
    start_byte_requested = int(range.split("=")[-1][:-1])
    end_byte_planned = min(start_byte_requested + BYTES_PER_RESPONSE, size) - 1
    # Somebody commented this correction
    # But it'd like to point out that I ran into this EXACT issue in litespeed.
    # The end byte is inclusive; so we subtract one from the last byte to get the proper index

    # This serve also doesn't support ALL range requests, only the first
    #   Actually, it only supports single range requests (which should be normal)

    chunk_generator = chunk_generator_from_stream(
        file,
        chunk_size=BYTES_PER_CHUNK,
        start=start_byte_requested,
        size=BYTES_PER_RESPONSE
    )
    mime = mimetypes.guess_type(path)
    return StreamingResponse(
        chunk_generator,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start_byte_requested}-{end_byte_planned}/{size}",
            "Content-Type": mime[0]
        },
        status_code=206
    )
