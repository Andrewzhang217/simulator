class CacheBlock:
    def __init__(self, block_size):
        self.valid = False
        self.dirty = False
        self.tag = None
        self.state = None
        self.data = [0] * block_size


class Cache:
    def __init__(self, size, associativity, block_size):
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.blocks = [{}] * (size // (associativity * block_size))

    def read(self, address):
        # Implement cache read operation
        pass

    def write(self, address):
        # Implement cache write operation
        pass
