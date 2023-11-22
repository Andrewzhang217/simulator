import argparse
from cache import Cache
from bus import Bus
from core import Core


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
    shared_bus = Bus()

    cores = []
    for i in range(4):
        # Read and process the trace file for each core
        with open(f"{input_file}_{i}.data", 'r') as file:
            trace_data = file.readlines()  # Read the trace data
        core = Core(i, cache_size, associativity, block_size, protocol, trace_data, shared_bus)
        cores.append(core)

    global_cycle = 0

    has_instr = True
    while has_instr:
        has_instr = False
        for core in cores:
            if not core.is_empty():
                has_instr = True
                core.execute(global_cycle)
        global_cycle += 1


if __name__ == "__main__":
    main()
