from collections import deque
from cache import Cache
from protocol import MESI, Dragon


class Core:
    def __init__(self, core_id, cache_size, associativity, block_size, protocol, data, shared_bus):
        self.core_id = core_id
        self.cache = Cache(cache_size, associativity, block_size)
        self.protocol = protocol
        if protocol == "MESI":
            self.protocol = MESI(core_id, self.cache, shared_bus)
        elif protocol == "Dragon":
            self.protocol = Dragon(core_id, self.cache, shared_bus)
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
        value = int(value, 16)

        if label == 0 or label == 1:  # Load or store instructions
            address = bin(value)[2:].zfill(32)
            if label == 0:
                self.protocol.PrRd(address, global_cycle)
            else:
                self.protocol.PrWr(address, global_cycle)
            self.load_store += 1
            self.cycles += 1

        elif label == 2:  # Other instructions
            self.compute_cycles += value
            self.cycles += value
