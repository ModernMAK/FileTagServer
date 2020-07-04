import distutils.util
from typing import List


class BaseModel:
    def __iter__(self):
        d = self.to_dictionary()
        for k in d:
            yield k, d[k]

    def to_dictionary(self):
        raise NotImplementedError

    def from_dictionary(self, **kwargs):
        raise NotImplementedError


class Page(BaseModel):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.description = kwargs.get('description', None)
        tags = kwargs.get('tags', None)
        if tags is None:
            self.tags = None
        else:
            self.tags = []
            for tag in tags:
                self.tags.append(Tag(**tag))

    @property
    def page_id(self):
        return self.__id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.__id != other.__id \
                    or self.name != other.name \
                    or self.description != other.description:
                return False
            # TODO compare tags,
            # Each tag should also be in other (and every tag in other should be in self)
            # We dont care about duplicates or tag order
            # Another way to describe this, we need to get a unique set from both
            # Then check that the unique sets are identical, ignoring order
            return True

    def __hash__(self):
        prime_a = 29
        prime_b = 31
        result = prime_a
        parts = [self.__id, self.name, self.description]
        # TODO perform hash on tags
        # since (as of this being written) __eq__ does not check tags, this is fine for now
        for part in parts:
            result = (result * prime_b) + hash(part)
        return result

    def __str__(self):
        return f"Id: {self.__id}, Name: '{self.name}', Desc: '{self.description}'"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        def tags_to_list_dict(tags: List[Tag]):
            result = []
            for tag in tags:
                result.append(tag.to_dictionary())
            return result

        return {
            'id': self.__id,
            'name': self.name,
            'descripyion': self.description,
            'tags': tags_to_list_dict(self.tags),
        }


class FilePage(Page):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id')
        kwargs['id'] = kwargs.get('page_id')
        super().__init__(**kwargs)
        self.file = kwargs.get('file')

    @property
    def file_page_id(self):
        return self.__id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                if self.__id != other.__id \
                        or self.file != other.file:
                    return False
            # TODO compare tags,
            # Each tag should also be in other (and every tag in other should be in self)
            # We dont care about duplicates or tag order
            # Another way to describe this, we need to get a unique set from both
            # Then check that the unique sets are identical, ignoring order
            return True

    def __hash__(self):
        prime_a = 17
        prime_b = 23
        result = prime_a
        parts = [super(), self.__id, self.file]
        for part in parts:
            result = (result * prime_b) + hash(part)
        return result

    def __str__(self):
        return f"Id: {self.__id}, Page: ({super()}), File: ({self.file})"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        base = super().to_dictionary()
        base['page_id'] = base['id']
        base['id'] = self.__id
        base['file'] = self.file.to_dictionary()
        return base


class File(BaseModel):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id', None)
        self.path = kwargs.get('path', None)
        self.extension = kwargs.get('extension', None)

    @property
    def file_id(self):
        return self.__id

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'id': self.__id,
            'path': self.path,
            'extension': self.extension
        }


class Tag(BaseModel):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.count = kwargs.get('count')
        self.classification = kwargs.get('class')

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'count': self.count,
            'description': self.description,
            'class': self.classification
        }

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.id != other.id \
                    or self.id != other.id \
                    or self.name != other.name \
                    or self.count != other.count \
                    or self.description != other.description \
                    or self.classification != other.classification:
                return False
            return True

    def __str__(self):
        return f"Id: '{self.id}', Name: '{self.name}', Desc: '{self.description}', Count: '{self.count}', Class: '{self.classification}'"

    def __hash__(self):
        prime_a = 23
        prime_b = 29
        result = prime_a
        parts = [self.id, self.name, self.count, self.description, self.classification]
        for part in parts:
            result = (result * prime_b) + hash(part)
        return result


class FileMeta(BaseModel):
    def __init__(self, **kwargs):
        self.id = int(kwargs.get('File', {}).get('id'))
        self.ignore = kwargs.get('File', {}).get('ignore')
        self.error_ignore = kwargs.get('Error', {}).get('ignore')

        if self.ignore is not None:
            self.ignore = bool(distutils.util.strtobool(self.ignore))
        if self.error_ignore is not None:
            self.error_ignore = bool(distutils.util.strtobool(self.error_ignore))

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'File': {
                'id': self.id,
                'ignore': self.ignore,
            },
            'Error':
                {
                    'ignore': self.error_ignore
                }

        }
