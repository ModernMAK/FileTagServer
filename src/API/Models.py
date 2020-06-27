from typing import List


class BaseModel:
    def to_dictionary(self):
        pass

    def from_dictionary(self, **kwargs):
        pass


class ImageModel(BaseModel):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', -1)
        self.width = kwargs.get('width', 2)
        self.height = kwargs.get('height', 2)
        self.extension = kwargs.get('extension', '')
        self.tags = kwargs.get('tags', [])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.id != other.id \
                    or self.width != other.width \
                    or self.height != other.height \
                    or self.extension != other.extension:
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
        result = (result * prime_b) + self.id.__hash__()
        result = (result * prime_b) + self.width.__hash__()
        result = (result * prime_b) + self.height.__hash__()
        result = (result * prime_b) + self.extension.__hash__()
        # TODO perform hash on tags
        # since (as of this being written) __eq__ does not check tags, this is fine for now
        return result

    def __str__(self):
        return f"{self.id}: ({self.width} px, {self.height} px) ~ '.{self.extension}'"

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        def tags_to_list_dict(tags: List[TagModel]):
            result = []
            for tag in tags:
                result.append(tag.to_dictionary())

        return {
            'id': self.id,
            'width': self.width,
            'height': self.height,
            'extension': self.extension,
            'tags': tags_to_list_dict(self.tags)
        }


class TagModel(BaseModel):
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', -1)
        self.name = kwargs.get('name', 2)
        self.count = kwargs.get('count', 0)

    def from_dictionary(self, **kwargs):
        self.__init__(**kwargs)

    def to_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            'count': self.count
        }

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self.id != other.id \
                    or self.id != other.id \
                    or self.name != other.name \
                    or self.count != other.count:
                return False
            return True

    def __str__(self):
        return f"{self.id}: {self.name} ~ {self.count}"

    def __hash__(self):
        prime_a = 23
        prime_b = 29
        result = prime_a
        result = (result * prime_b) + self.id.__hash__()
        result = (result * prime_b) + self.name.__hash__()
        result = (result * prime_b) + self.count.__hash__()
        return result
