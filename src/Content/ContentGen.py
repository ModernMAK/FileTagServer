import os
import shutil
from typing import List, Union
import PIL


def enforce_dirs_exists(file_path: str):
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path)
    except FileExistsError:
        pass


def get_formatted_ext(path: str) -> str:
    _, ext = os.path.splitext(path)
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


class ContentGenerator:
    def __init__(self):
        self.generators = []

    @staticmethod
    def get_default():
        cg = ContentGenerator()
        cg.add_generator(ImageContentGen())
        cg.add_generator(SvgContentGen())
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

    def generate(self, source: str, dest_folder: str) -> (int, int, int):
        passed, failed, total = 0, 0, 0
        for generator in self.generators:
            if generator.is_supported(source):
                if generator.generate(source, dest_folder):
                    passed += 1
                else:
                    failed += 1
                total += 1
        return passed, failed, total


class ImageContentGen(AbstractContentGen):
    @staticmethod
    def static_get_supported():
        return ['png', 'jpeg', 'jpg', 'bmp', 'gif', 'psd']

    @staticmethod
    def static_get_retargeting():
        return {
            'psd': 'png',
        }

    def get_supported(self):
        return ImageContentGen.static_get_supported()

    def get_retargeting(self):
        return ImageContentGen.static_get_retargeting()

    def generate(self, source: str, dest_folder: str) -> bool:
        try:
            ext = get_formatted_ext(source)
            retargeting = self.get_retargeting().get(ext)
            with PIL.Image.open(source) as img:
                with self.generate_thumbnail(img) as thumb:
                    save_path = build_save_path('thumbnail', source, dest_folder, desired_ext=retargeting)
                    enforce_dirs_exists(save_path)
                    thumb.save(save_path)

                save_path = build_save_path('full_rez', source, dest_folder, desired_ext=retargeting)
                enforce_dirs_exists(save_path)
                img.save(save_path)
                return True
        except PIL.UnidentifiedImageError as e:
            print(e)
            return False
        except ValueError as e:
            # We expect psd to sometimes fail on a value error,
            # but we want to make sure other value errors dont get caught
            # We'll stil hide some errors, but only on PSD files
            if ext == 'psd':
                return False
            else:
                raise
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

    def generate(self, source: str, dest_folder: str) -> bool:
        try:
            ext = get_formatted_ext(source)
            save_path = build_save_path('full_rez', source, dest_folder, desired_ext=ext)
            enforce_dirs_exists(save_path)
            shutil.copyfile(source, save_path)
            return True
        except Exception as e:
            print(e)
            raise
