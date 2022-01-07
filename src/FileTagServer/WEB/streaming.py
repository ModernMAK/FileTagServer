import mimetypes
import os
from io import BytesIO
from typing import Optional, Tuple, BinaryIO

from starlette.responses import StreamingResponse, FileResponse

Kibi = 1024
Mebi = Kibi * Kibi
Gibi = Mebi * Kibi
BYTES_PER_RESPONSE = 64 * Mebi
BYTES_PER_CHUNK = Mebi


def parse_byte_range(byte_range: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not byte_range:
        return None, None
    range_type, ranges = byte_range.split("=")
    ranges = ranges.split(",")
    parts = ranges[0].split("-")
    start = int(parts[0]) if len(parts[0]) > 0 else None
    end = int(parts[1]) if (len(parts) > 1 and len(parts[1]) > 0) else None
    return start, end


def file_byte_generator(path: str, start_byte: int, end_byte: int, chunk_size: int):
    with open(path, "rb") as stream:
        return stream_byte_generator(stream, start_byte, end_byte, chunk_size)


def stream_byte_generator(stream: BinaryIO, start_byte: int, end_byte: int, chunk_size: int, should_close: bool = False):
    byte_range = end_byte - start_byte
    read_size = byte_range + 1

    bytes_read = 0
    stream.seek(start_byte)
    while bytes_read < read_size:
        bytes_to_read = min(chunk_size, read_size - bytes_read)
        yield stream.read(bytes_to_read)
        bytes_read += bytes_to_read

    if should_close:
        stream.close()


def handle_file_byte_range(start_byte: Optional[int], end_byte: Optional[int], file_size: int) -> Tuple[int, int]:

    if not start_byte and not end_byte:
        start_byte = 0
        end_byte = file_size - 1
    elif not end_byte and start_byte:
        end_byte = file_size - 1
    elif not start_byte and end_byte:
        if end_byte < 0:
            raise Exception("End Byte is not a suffix!")
        start_byte = (file_size - end_byte) - 1
        end_byte = file_size - 1
    return start_byte, end_byte


def limit_byte_range(start_byte: int, end_byte: int, limit_size: int = None):
    if not limit_size:
        return start_byte, end_byte

    range_size = end_byte - start_byte + 1
    if range_size > limit_size:
        end_byte = start_byte + limit_size - 1

    return start_byte, end_byte


class BufferStreamingResponse(StreamingResponse):
    def __init__(self, stream: BinaryIO, mime: str, start_byte: Optional[int] = None, end_byte: Optional[int] = None,
                 response_size: Optional[int] = None, chunk_size: Optional[int] = None,
                 allow_unlimited_responses: bool = False):
        # if we allow unlimited responses, keep response_size 'None' for our limit_byte_range check, if it's not None we limit, otherwise it's unlimited
        if not allow_unlimited_responses and not response_size:
            response_size = response_size or BYTES_PER_RESPONSE
        chunk_size = chunk_size or BYTES_PER_CHUNK
        stream.seek(0, 2)
        file_size = stream.tell()
        stream.seek(0, 0)
        start_byte, end_byte = handle_file_byte_range(start_byte, end_byte, file_size)
        if response_size:
            start_byte, end_byte = limit_byte_range(start_byte, end_byte, response_size)

        streamable = stream_byte_generator(stream, start_byte, end_byte, chunk_size)

        headers = {
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}"
            }
        if mime:
            headers["Content-Type"]= mime

        super().__init__(
            streamable,
            headers=headers,
            status_code=206
        )


class FileStreamingResponse(StreamingResponse):
    def __init__(self, path: str, start_byte: Optional[int] = None, end_byte: Optional[int] = None,
                 response_size: Optional[int] = None, chunk_size: Optional[int] = None,
                 allow_unlimited_responses: bool = False):
        # if we allow unlimited responses, keep response_size 'None' for our limit_byte_range check, if it's not None we limit, otherwise it's unlimited
        if not allow_unlimited_responses and not response_size:
            response_size = response_size or BYTES_PER_RESPONSE
        chunk_size = chunk_size or BYTES_PER_CHUNK
        file_size = os.stat(path).st_size
        file_mime = mimetypes.guess_type(path)

        start_byte, end_byte = handle_file_byte_range(start_byte, end_byte, file_size)
        if response_size:
            start_byte, end_byte = limit_byte_range(start_byte, end_byte, response_size)

        streamable = file_byte_generator(path, start_byte, end_byte, chunk_size)

        super().__init__(
            streamable,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Range": f"bytes {start_byte}-{end_byte}/{file_size}",
                "Content-Type": file_mime[0]
            },
            status_code=206
        )


def serve_streamable_file(path: str, byte_range: str = None, name: str = None):
    if not byte_range:
        return FileResponse(path, filename=name)
    else:
        start_byte, end_byte = parse_byte_range(byte_range)
        return FileStreamingResponse(path, start_byte, end_byte)


def serve_streamable_buffer(stream: BinaryIO, mime: str, byte_range: str = None, name: str = None):
    if not byte_range:
        return BufferStreamingResponse(stream, mime, allow_unlimited_responses=True)
    else:
        start_byte, end_byte = parse_byte_range(byte_range)
        return BufferStreamingResponse(stream, mime, start_byte, end_byte)
