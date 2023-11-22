from collections import deque
from cache import *


class Core:
    def __init__(self, cache_size, associativity, block_size, protocol, data):
        self.cache = Cache(cache_size, associativity, block_size)
        self.protocol = protocol
        self.data = deque(data)
        self.cycles = 0
        self.compute_cycles = 0
        self.load_store = 0
        self.idle_cycles = 0

    def is_empty(self):
        return not self.data

    def execute(self, global_cycle):
        if global_cycle < self.cycles:
            return

        line = self.data.popleft()
        label, value = line.split()
        label = int(label)

        if label == 0 or label == 1:  # Load or store instructions
            address = int(value, 16)
            if label == 0:
                self.cache.read(address)
            else:
                self.cache.write(address)
            self.load_store += 1
            self.cycles += 1

        elif label == 2:  # Other instructions
            cycles = int(value, 16)
            self.compute_cycles += cycles
            self.cycles += cycles
