import math


class CacheBlock:
    def __init__(self, tag=None, state='I', cycle=0):
        self.tag = tag
        self.state = state
        self.last_used_cycle = cycle


class Cache:
    def __init__(self, size, associativity, block_size):
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.num_blocks = self.size // block_size
        self.num_sets = self.num_blocks // self.associativity
        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_sets))
        self.blocks = [[CacheBlock() for _ in range(associativity)] for _ in range(self.num_sets)]
        self.hit = 0
        self.miss = 0
