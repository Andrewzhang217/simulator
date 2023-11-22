import math


class CacheBlock:
    def __init__(self, tag=None, state='I'):
        self.tag = tag
        self.state = state
        self.last_used_cycle = 0


class Cache:
    def __init__(self, size, associativity, block_size):
        self.size = size
        self.associativity = associativity
        self.block_size = block_size
        self.num_blocks = self.size // (block_size * associativity)
        self.num_sets = self.num_blocks // self.associativity
        self.offset_bits = int(math.log2(block_size))
        self.index_bits = int(math.log2(self.num_blocks))
        self.blocks = [[CacheBlock() for _ in range(associativity)] for _ in range(self.num_sets)]

    def read(self, address, cycle):
        # Implement cache read operation

        tag_bits = address[:len(address) - self.index_bits - self.offset_bits]
        index_bits = address[len(address) - self.index_bits - self.offset_bits:len(address) - self.offset_bits]
        offset_bits = address[-self.offset_bits:]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.blocks[index]
        hit = False

        # hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                block.last_used_cycle = cycle

        # miss, load from main memory
        if not hit:
            empty_block = -1
            for i, block in enumerate(cache_set):
                if block.state == 'I':
                    empty_block = i
                    break
            if empty_block == -1:  # no empty block, cache set full
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                # load from main memory
                cache_set[min_lru_index].last_used_cycle = cycle

    def write(self, address, cycle):
        # Implement cache write operation
        tag_bits = address[:len(address) - self.index_bits - self.offset_bits]
        index_bits = address[len(address) - self.index_bits - self.offset_bits:len(address) - self.offset_bits]
        offset_bits = address[-self.offset_bits:]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.blocks[index]
        hit = False

        # hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                block.last_used_cycle = cycle

        # miss, load from main memory
        if not hit:
            empty_block = -1
            for i, block in enumerate(cache_set):
                if block.state == 'I':
                    empty_block = i
                    break
            if empty_block == -1:  # no empty block, cache set full
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                # load from main memory
                cache_set[min_lru_index].last_used_cycle = cycle
