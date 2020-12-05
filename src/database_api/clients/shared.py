

class AbstractTable:
    @staticmethod
    def qualify_name(*parts):
        return ".".join(parts)


