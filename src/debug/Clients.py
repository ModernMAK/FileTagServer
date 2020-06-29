import unittest
from src.API import Clients
from src import PathUtil

unittest_db_path = PathUtil.data_path('unittest_mediaserver.db')


class TestFileClient(unittest.TestCase):
    def test_get_all(self):
        client = Clients.FileClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = [
            {'id': 1, 'path': 'testpath.txt', 'extension': 'txt'},
            {'id': 2, 'path': 'testimage.png', 'extension': 'png'},
            {'id': 3, 'path': 'testimagemip.png', 'extension': 'png'}
        ]
        assert (result == expected), f'{"FileClient"} ~ {"get_all"} Failed'

    def test_get_paged(self):
        client = Clients.FileClient(db_path=unittest_db_path)
        result = client.get_paged(page_size=2, page_offset=1)
        expected = [
            # {'id': 1, 'path': 'testpath.txt', 'extension': 'txt'},
            {'id': 2, 'path': 'testimage.png', 'extension': 'png'},
            {'id': 3, 'path': 'testimagemip.png', 'extension': 'png'},
        ]
        assert (result == expected), f'{"FileClient"} ~ {"get_paged"} Failed'

    def test_get(self):
        client = Clients.FileClient(db_path=unittest_db_path)
        result = client.get(ids=[1, 2])
        expected = [
            {'id': 1, 'path': 'testpath.txt', 'extension': 'txt'},
            {'id': 2, 'path': 'testimage.png', 'extension': 'png'},
        ]
        assert (result == expected), f'{"FileClient"} ~ {"get"} Failed'


class TestImageFileClient(unittest.TestCase):
    def __records(self):
        return [
            {'id': 1, 'path': 'testimage.png', 'extension': 'png', 'width': 256, 'height': 256},
            {'id': 2, 'path': 'testimagemip.png', 'extension': 'png', 'width': 128, 'height': 128},
        ]

    def test_get_all(self):
        client = Clients.ImageFileClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = self.__records()
        assert (result == expected), f'{"ImageFileClient"} ~ {"get_all"} Failed ~ Unexpected Output'

    def test_get_paged(self):
        client = Clients.ImageFileClient(db_path=unittest_db_path)
        result = client.get_paged(page_size=1, page_offset=1)
        expected = [
            self.__records()[1]
        ]
        assert (result == expected), f'{"ImageFileClient"} ~ {"get_paged"} Failed ~ Unexpected Output'

    def test_get(self):
        client = Clients.ImageFileClient(db_path=unittest_db_path)
        result = client.get(ids=[1])
        expected = [
            self.__records()[0]
        ]
        assert (result == expected), f'{"ImageFileClient"} ~ {"get"} Failed ~ Unexpected Output'


class TestImageMipClient(unittest.TestCase):
    def __records(self):
        return [
            {'id': 1, 'path': 'testimage.png', 'extension': 'png',
             'width': 256, 'height': 256, 'name': 'Raw', 'scale': 1.0, 'map_id': 1},
            {'id': 2, 'path': 'testimagemip.png', 'extension': 'png',
             'width': 128, 'height': 128, 'name': 'Thumbnail', 'scale': 0.5, 'map_id': 1},
        ]

    def test_get_all(self):
        client = Clients.ImageMipClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = self.__records()
        assert (result == expected), f'{"ImageMipClient"} ~ {"get_all"} Failed ~ Unexpected Output'

    def test_get_paged(self):
        client = Clients.ImageMipClient(db_path=unittest_db_path)
        result = client.get_paged(page_size=1, page_offset=1)
        expected = [
            self.__records()[1],
        ]
        assert (result == expected), f'{"ImageMipClient"} ~ {"get_paged"} Failed ~ Unexpected Output'

    def test_get(self):
        client = Clients.ImageMipClient(db_path=unittest_db_path)
        result = client.get(ids=[1])
        expected = [
            self.__records()[0],
        ]
        assert (result == expected), f'{"ImageMipClient"} ~ {"get"} Failed ~ Unexpected Output'


class TestImageMipMapClient(unittest.TestCase):
    def __mip_records(self):
        return [
            {'id': 1, 'path': 'testimage.png', 'extension': 'png',
             'width': 256, 'height': 256, 'name': 'Raw', 'scale': 1.0, 'map_id': 1},
            {'id': 2, 'path': 'testimagemip.png', 'extension': 'png',
             'width': 128, 'height': 128, 'name': 'Thumbnail', 'scale': 0.5, 'map_id': 1},
        ]

    def __map_records(self):
        return [
            {'id': 1, 'mips': [self.__mip_records()[0], self.__mip_records()[1]]},
        ]

    def test_get_all(self):
        client = Clients.ImageMipmapClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = self.__map_records()
        assert (result == expected), f'{"ImageMipmapClient"} ~ {"get_all"} Failed ~ Unexpected Output'

    def test_get_paged(self):
        client = Clients.ImageMipmapClient(db_path=unittest_db_path)
        result = client.get_paged()
        expected = [self.__map_records()[0]]
        assert (result == expected), f'{"ImageMipmapClient"} ~ {"get_paged"} Failed ~ Unexpected Output'

    def test_get(self):
        client = Clients.ImageMipmapClient(db_path=unittest_db_path)
        result = client.get(ids=[1])
        expected = [self.__map_records()[0]]
        assert (result == expected), f'{"ImageMipmapClient"} ~ {"get"} Failed ~ Unexpected Output'


class TestTagClient(unittest.TestCase):
    def __tag_records(self):
        return [
            {'id': 1, 'name': 'Test', 'description': 'This is a test tag',
             'class': None, 'count': 1},
        ]

    def test_get_all(self):
        client = Clients.TagClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = self.__tag_records()
        assert (result == expected), f'{"TagClient"} ~ {"get_all"} Failed ~ Unexpected Output'

    def test_get_paged(self):
        client = Clients.TagClient(db_path=unittest_db_path)
        result = client.get_paged()
        expected = [self.__tag_records()[0]]
        assert (result == expected), f'{"TagClient"} ~ {"get_paged"} Failed ~ Unexpected Output'

    def test_get(self):
        client = Clients.TagClient(db_path=unittest_db_path)
        result = client.get(ids=[1])
        expected = [self.__tag_records()[0]]
        assert (result == expected), f'{"TagClient"} ~ {"get"} Failed ~ Unexpected Output'


class TestPostClient(unittest.TestCase):
    def __post_records(self):
        return [
            {'id': 1, 'name': 'Test Post', 'description': 'Test Post Description',
             'tags': [self.__tag_records()[0]]},
        ]

    def __tag_records(self):
        return [
            {'id': 1, 'name': 'Test', 'description': 'This is a test tag',
             'class': None, 'count': 1},
        ]

    def test_get_all(self):
        client = Clients.PostClient(db_path=unittest_db_path)
        result = client.get_all()
        expected = self.__post_records()
        assert (result == expected), f'{"PostClient"} ~ {"get_all"} Failed ~ Unexpected Output'

    def test_get_paged(self):
        client = Clients.PostClient(db_path=unittest_db_path)
        result = client.get_paged()
        expected = [self.__post_records()[0]]
        assert (result == expected), f'{"PostClient"} ~ {"get_paged"} Failed ~ Unexpected Output'

    def test_get(self):
        client = Clients.PostClient(db_path=unittest_db_path)
        result = client.get(ids=[1])
        expected = [self.__post_records()[0]]
        assert (result == expected), f'{"PostClient"} ~ {"get"} Failed ~ Unexpected Output'


if __name__ == '__main__':
    unittest.main()
