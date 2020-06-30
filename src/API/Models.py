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


class Post(BaseModel):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id', None)
        self.name = kwargs.get('name', None)
        self.description = kwargs.get('description', None)
        self.tags = kwargs.get('tags', [Tag])

    @property
    def post_id(self):
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


class ImagePost(Post):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id')
        kwargs['id'] = kwargs.get('post_id')
        super().__init__(**kwargs)
        self.mipmap = kwargs.get('mipmap',ImageMipmap())

    @property
    def image_post_id(self):
        return self.__id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                if self.__id != other.__id \
                        or self.mipmap != other.mipmap:
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
        parts = [super(), self.__id, self.mipmap]
        for part in parts:
            result = (result * prime_b) + hash(part)
        return result

    def __str__(self):
        return f"Id: {self.__id}, Post: ({super()}), MipMap: ({self.mipmap})"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        base = super().to_dictionary()
        base['post_id'] = base['id']
        base['id'] = self.__id
        base['mipmap'] = self.mipmap.to_dictionary()
        return base


class ImageMipmap(BaseModel):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id')
        self.mips = kwargs.get('mips', [ImageMip()])

    def get_mip_by_name(self, name):
        for mip in self.mips:
            if mip.name == name:
                return mip
        return None


    @property
    def mipmap_id(self):
        return self.__id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                if self.__id != other.__id:
                    return False
            # TODO compare mips
        return True

    def __hash__(self):
        prime_a = 17
        prime_b = 23
        result = prime_a
        parts = [super(), self.__id]
        for part in parts:
            result = (result * prime_b)+ hash(part)
        return result

    def __str__(self):
        mip_str = []
        for mip in self.mips:
            mip_str.append(f"Mip: ({mip})")
        mip_str = ', '.join(mip_str)
        return f"Id: {self.__id}, Mips: [{mip_str}]"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        def mips_to_list_dict(mips: List[ImageMip]):
            result = []
            for mip in mips:
                result.append(mip.to_dictionary())
            return result

        return {
            'id': self.__id,
            'mips': mips_to_list_dict(self.mips),
        }


class ImageMip(BaseModel):
    def __init__(self, **kwargs):
        self.__id = kwargs.get('id')
        self.file_id = kwargs.get('file_id', None)
        self.name = kwargs.get('name', None)
        self.scale = kwargs.get('scale', None)
        self.width = kwargs.get('width', None)
        self.height = kwargs.get('height', None)
        self.path = kwargs.get('path', None)
        self.v_path = kwargs.get('v_path', 'None')
        self.extension = kwargs.get('extension', None)

    @property
    def mip_id(self):
        return self.__id

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if super().__eq__(other):
                if self.__id != other.__id \
                        or self.file_id == other.file_id \
                        or self.name == other.name \
                        or self.scale == other.scale \
                        or self.width == other.width \
                        or self.height == other.height \
                        or self.path == other.path \
                        or self.v_path == other.v_path \
                        or self.extension == other.extension:
                    return False
            # TODO compare mips
        return True

    def __hash__(self):
        prime_a = 17
        prime_b = 23
        result = prime_a
        parts = [super(), self.__id, self.name, self.scale, self.width, self.height, self.path,self.file_id, self.extension]
        for part in parts:
            result = (result * prime_b)+ hash(part)
        return result

    def __str__(self):
        return f"Id: {self.__id}, Name: '{self.name}', TODO... '"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'id': self.__id,
            'name': self.name,
            'scale': self.scale,
            'width': self.width,
            'height': self.height,
            'path': self.path,
            'v_path': self.v_path,
            'file_id': self.file_id,
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
