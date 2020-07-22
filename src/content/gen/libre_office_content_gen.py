import shutil
from io import BytesIO
from typing import List, Union, Tuple
import tempfile
from src.util import path_util
import os.path
import os
import subprocess
from os.path import dirname, basename

from src.content.content_gen import GeneratedContentType, DynamicContentGenerator, SimpleContentGenerator


class LibreOfficeConverter:
    # A path generated from a windows install, installed in the depends folder
    WIN_PATH = os.path.join(path_util.project_root(), 'depends',
                            'LibreOffice', 'program', 'soffice')
    # A path generated from a windows portable install, installed in the depends folder
    WIN_PORTABLE_PATH = os.path.join(path_util.project_root(), 'depends',
                                     'LibreOfficePortable', 'App', 'libreoffice', 'program', 'soffice')

    LIBRE_OFFICE_PATH = WIN_PORTABLE_PATH

    @classmethod
    def convert_file(cls, input_file, output_file, format) -> None:
        output_dir = dirname(output_file)
        input_name = basename(input_file)
        args = [
            cls.LIBRE_OFFICE_PATH,
            '--headless',
            '--convert-to', format,
            '--outdir', f'{output_dir}',
            f'{input_file}']

        p = subprocess.run(args, shell=True)
        if p.returncode != 0:
            raise Exception(p.stderr)
        save_name = os.path.join(output_dir, input_name)
        save_base_name, _ = os.path.splitext(save_name)
        save_path = save_base_name + f".{format}"
        if save_path != output_file:
            os.rename(save_path, output_file)

    @classmethod
    def convert_bytes(cls, file: BytesIO, output: BytesIO, format) -> None:
        with tempfile.NamedTemporaryFile(mode='wb') as temp_in:
            with tempfile.NamedTemporaryFile(mode='rb') as temp_out:
                temp_in.write(file.read())
                cls.convert_file(temp_in.name, temp_out.name, format)
                output.write(temp_out.read())


class DynamicLibreOfficeContentGenerator(DynamicContentGenerator):
    # While range is supported, it is HIGHLY recommended, to not
    def generate(self, file: BytesIO, **kwargs) -> List[bytes]:
        if 'format' not in kwargs:
            sub_generator = kwargs.get('sub_generator', super())
            kwargs.update(kwargs.get('sub_kwargs', {}))
            return sub_generator.generate(file, **kwargs)
        with BytesIO() as output:
            LibreOfficeConverter.convert_bytes(file, output, kwargs['format'])
            kwargs.update(kwargs.get('sub_kwargs', {}))
            sub_generator = kwargs.get('sub_generator', super())
            return sub_generator.generate(output, **kwargs)


class SimpleLibreOfficeContentGenerator(SimpleContentGenerator):
    def __init__(self):
        self.backing_generator = DynamicLibreOfficeContentGenerator()

    def _generate_thumbnail(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        kwargs = {
            'format': 'jpeg',
            'sub_kwargs': {
                'thumbnail': (128, 128),
                'format': 'webp'
            }
        }
        try:
            from .pillow_content_gen import DynamicImageContentGenerator
            kwargs['sub_generator'] = DynamicImageContentGenerator()
            kwargs['format'] = 'png'  # If we have pil, use PNG as intermediary for higher quality
        except ModuleNotFoundError as e:
            print(e)
            pass

        results = self.backing_generator.generate(file, **kwargs)
        format = kwargs['format']
        if 'sub_generator' in kwargs:
            format = kwargs.get('sub_kwargs', {}).get('format', format)
        return results[0], format  # Returns one range, the whole file

    def _generate_viewable(self, file: BytesIO, file_ext: str) -> Union[Tuple[bytes, str], None]:
        kwargs = {
            'format': 'pdf'
        }
        results = self.backing_generator.generate(file, **kwargs)
        return results[0], 'pdf'  # Returns one range, the whole file
