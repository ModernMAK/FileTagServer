import locale
import os
import shutil
from typing import List, Union, Dict
import PIL
import ghostscript
from PIL import Image


def enforce_dirs_exists(file_path: str):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path)
    except FileExistsError:
        pass


def get_formatted_ext(path: str) -> str:
    base, ext = os.path.splitext(path)
    if ext is None or len(ext) == 0:
        ext = base
    ext = ext.lstrip('.').lower()
    return ext


def build_save_path(new_name: str, src_path: str, dest_path: str, desired_ext=None):
    if desired_ext is None:
        _, ext = os.path.splitext(src_path)
    else:
        if desired_ext[0] != '.':
            ext = f'.{desired_ext}'
        else:
            ext = desired_ext
    return os.path.join(f"{dest_path}", f"{new_name}{ext}")


class AbstractContentGen:
    def get_supported(self) -> List[str]:
        raise NotImplementedError

    def is_supported(self, source: str) -> bool:
        return get_formatted_ext(source) in self.get_supported()

    def generate(self, source: str, dest_folder: str) -> (int, int, int):
        raise NotImplementedError

    def get_content_mapping(self, ext: str) -> Dict[str, str]:
        raise NotImplementedError

    def get_content_path(self, content_name: str, content_ext: str) -> Union[None, str]:
        return self.get_content_mapping(content_ext).get(content_name, None)


CONTENT_PREVIEW = 'preview'
CONTENT_RAW = 'raw'


class ContentGenerator:
    def __init__(self):
        self.generators = []

    @staticmethod
    def get_default():
        cg = ContentGenerator()
        cg.add_generator(ImageContentGen())
        cg.add_generator(SvgContentGen())
        cg.add_generator(NonBrowserImageContentGen())
        cg.add_generator(PdfContentGen())
        return cg

    def add_generator(self, generator: AbstractContentGen):
        self.generators.append(generator)

    def get_supported(self):
        unique = set()
        for generator in self.generators:
            unique.update(generator.get_supported())
        return unique

    def is_supported(self, source):
        for generator in self.generators:
            if generator.is_supported(source):
                return True
        return False

    def generate(self, source: str, dest_folder: str, **kwargs) -> (int, int, int):
        passed, failed, total = 0, 0, 0
        for generator in self.generators:
            if generator.is_supported(source):
                if generator.generate(source, dest_folder, **kwargs):
                    passed += 1
                else:
                    failed += 1
                total += 1
        return passed, failed, total

    def get_content_path(self, content_name: str, content_ext: str) -> Union[None, str]:
        for generator in self.generators:
            if generator.is_supported(content_ext):
                return generator.get_content_path(content_name, content_ext)


class ImageContentGen(AbstractContentGen):
    @staticmethod
    def static_get_supported():
        return ['png', 'jpeg', 'jpg', 'bmp', 'gif']

    def get_supported(self):
        return ImageContentGen.static_get_supported()

    def get_content_mapping(self, ext) -> Dict[str, str]:
        return {
            CONTENT_PREVIEW: f'thumbnail.{ext}',
            CONTENT_RAW: f'full_rez.{ext}'
        }

    def generate(self, source: str, dest_folder: str, **kwargs) -> bool:
        try:
            ext = get_formatted_ext(source)
            with PIL.Image.open(source) as img:
                save_path = build_save_path('thumbnail', source, dest_folder, desired_ext=ext)
                if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                    thumb = self.generate_thumbnail(img)
                    enforce_dirs_exists(save_path)
                    thumb.save(save_path)
                    thumb.close()

                save_path = build_save_path('full_rez', source, dest_folder, desired_ext=ext)
                if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                    enforce_dirs_exists(save_path)
                    shutil.copyfile(source, save_path)
                return True
        except PIL.UnidentifiedImageError as e:
            print(e)
            return False
        except PIL.Image.DecompressionBombError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            raise

    # False if thumbnail shouldnt be generated
    def generate_thumbnail(self, img: PIL.Image) -> Union[None, PIL.Image.Image]:
        (thm_x, thm_y) = thumbnail_size = (256, 256)
        (img_x, img_y) = img.size
        if thm_x >= img_x and thm_y >= img_y:
            return None
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size)
        return thumb


class NonBrowserImageContentGen(ImageContentGen):
    @staticmethod
    def static_get_supported():
        return ['psd', 'tiff', 'tif']

    def get_supported(self):
        return NonBrowserImageContentGen.static_get_supported()

    def get_content_mapping(self, ext) -> Dict[str, str]:
        return {
            CONTENT_PREVIEW: f'thumbnail.png',
            CONTENT_RAW: f'full_rez.png'
        }

    def generate(self, source: str, dest_folder: str, **kwargs) -> bool:
        try:
            ext = get_formatted_ext(source)
            retargeting = 'png'
            with PIL.Image.open(source) as img:
                with self.generate_thumbnail(img) as thumb:
                    save_path = build_save_path('thumbnail', source, dest_folder, desired_ext=retargeting)
                    if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                        enforce_dirs_exists(save_path)
                        thumb.save(save_path)

                if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                    save_path = build_save_path('full_rez', source, dest_folder, desired_ext=retargeting)
                    enforce_dirs_exists(save_path)
                    img.save(save_path)
                return True
        except PIL.UnidentifiedImageError as e:
            print(e)
            return False
        except ValueError as e:
            print(e)
            return False
        except PIL.Image.DecompressionBombError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            raise

    # False if thumbnail shouldnt be generated
    def generate_thumbnail(self, img: PIL.Image) -> Union[None, PIL.Image.Image]:
        (thm_x, thm_y) = thumbnail_size = (256, 256)
        (img_x, img_y) = img.size
        if thm_x >= img_x and thm_y >= img_y:
            return None
        thumb = img.copy()
        thumb.thumbnail(thumbnail_size)
        return thumb


class SvgContentGen(AbstractContentGen):
    @staticmethod
    def static_get_supported():
        return ['svg']

    def get_supported(self):
        return SvgContentGen.static_get_supported()

    def get_content_mapping(self, ext) -> Dict[str, str]:
        return {
            CONTENT_PREVIEW: f'full_rez.{ext}',
            CONTENT_RAW: f'full_rez.{ext}'
        }

    def generate(self, source: str, dest_folder: str, **kwargs) -> bool:
        try:
            ext = get_formatted_ext(source)
            save_path = build_save_path('full_rez', source, dest_folder, desired_ext=ext)
            if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                enforce_dirs_exists(save_path)
                shutil.copyfile(source, save_path)
            return True
        except Exception as e:
            print(e)
            raise


def pdf_to_png(input, output):
    args = ["-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=png16m", "-r144", "-dFirstPage=1", "-dLastPage=1",
            "-sOutputFile=" + output,
            input]
    encoding = locale.getpreferredencoding()
    args = [a.encode(encoding) for a in args]
    with ghostscript.Ghostscript(*args) as g:
        ghostscript.cleanup()


class PdfContentGen(AbstractContentGen):
    @staticmethod
    def static_get_supported():
        return ['pdf', 'ai']

    def get_content_mapping(self, ext: str) -> Dict[str, str]:
        return {
            CONTENT_PREVIEW: 'preview.png',
            CONTENT_RAW: 'local_copy.pdf'
        }

    def get_supported(self):
        return PdfContentGen.static_get_supported()

    def generate(self, source: str, dest_folder: str, **kwargs) -> bool:
        try:

            raw_save_path = save_path = build_save_path('local_copy', source, dest_folder, desired_ext='pdf')
            if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                enforce_dirs_exists(save_path)
                shutil.copyfile(source, save_path)
            save_path = build_save_path('preview', source, dest_folder, desired_ext='png')
            if kwargs.get('rebuild', False) or not os.path.exists(save_path):
                enforce_dirs_exists(save_path)
                pdf_to_png(raw_save_path, save_path)
            return True
        except ghostscript.GhostscriptError as e:
            print(e)
            return False
        except Exception as e:
            print(e)
            raise
