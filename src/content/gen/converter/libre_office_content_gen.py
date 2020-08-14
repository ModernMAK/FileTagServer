from io import BytesIO
import tempfile

from src.util import path_util
import os.path
import os
import subprocess
from os.path import dirname, basename
from src.content.gen.content_gen import GeneratorFunction


class LibreOfficeConverter:
    # A path generated from a windows install, installed in the depends folder
    WIN_PATH = os.path.join(
        path_util.project_root(), 'depends',
        'LibreOffice', 'program', 'soffice'
    )
    # A path generated from a windows portable install, installed in the depends folder
    WIN_PORTABLE_PATH = os.path.join(
        path_util.project_root(), 'depends',
        'LibreOfficePortable', 'App', 'libreoffice', 'program', 'soffice'
    )

    LIBRE_OFFICE_PATH = WIN_PORTABLE_PATH

    @classmethod
    def convert_file(cls, input_file, output_file, format: str) -> None:
        output_dir = dirname(output_file)
        input_name = basename(input_file)
        args = [
            cls.LIBRE_OFFICE_PATH,
            '--headless',
            '--convert-to', format,
            '--outdir', f'{output_dir}',
            f'{input_file}'
        ]
        process = subprocess.run(args, shell=True, capture_output=True)
        if process.returncode != 0:
            raise Exception(process.stderr)
        save_name = os.path.join(output_dir, input_name)
        save_base_name, _ = os.path.splitext(save_name)
        save_path = save_base_name + f".{format}"
        if save_path != output_file:
            os.rename(save_path, output_file)

    @classmethod
    def convert_bytes(cls, file: BytesIO, output: BytesIO, format: str) -> None:
        with tempfile.NamedTemporaryFile(mode='wb') as temp_in:
            with tempfile.NamedTemporaryFile(mode='rb') as temp_out:
                temp_in.write(file.read())
                cls.convert_file(temp_in.name, temp_out.name, format)
                output.write(temp_out.read())


# The same for either
def get_convert_function(format: str) -> GeneratorFunction:
    def convert_function(input: BytesIO, output: BytesIO):
        LibreOfficeConverter.convert_bytes(input, output, format)

    return convert_function
