import argparse


class CacheBlock:
    def __init__(self, block_size):
        self.valid = False
        self.dirty = False
        self.tag = None
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


class Core:
    def __init__(self, cache_size, associativity, block_size, protocol, data):
        self.cache = Cache(cache_size, associativity, block_size)
        self.protocol = protocol
        self.data = data
        self.cycles = 0
        self.compute_cycles = 0
        self.load_store = 0
        self.idle_cycles = 0

    def execute(self):
        for line in self.data:
            label, value = line.split()
            label = int(label)

            # TODO: actual cycles computation
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


def main():
    parser = argparse.ArgumentParser(description="Cache Coherence Simulator")
    parser.add_argument(
        "protocol", choices=["MESI", "Dragon"], help="Coherence protocol"
    )
    parser.add_argument("input_file", help="Input benchmark name")
    parser.add_argument(
        "cache_size", type=int, default=4096, help="Cache size in bytes"
    )
    parser.add_argument(
        "associativity", type=int, default=2, help="Cache associativity"
    )
    parser.add_argument("block_size", type=int, default=32, help="Block size in bytes")
    args = parser.parse_args()

    protocol = args.protocol
    input_file = args.input_file
    cache_size = args.cache_size
    associativity = args.associativity
    block_size = args.block_size

    cores = []
    for i in range(4):
        # Read and process the trace file for each core
        with open(f"{input_file}_{i}.data", 'r') as file:
            trace_data = file.readlines()  # Read the trace data
        core = Core(cache_size, associativity, block_size, protocol, trace_data)
        cores.append(core)

    for core in cores:
        core.execute()
        # print(core.cycles)


if __name__ == "__main__":
    main()
