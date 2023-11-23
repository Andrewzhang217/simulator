from abc import ABC, abstractmethod
from enum import Enum
from bus import Bus, Transaction
from cache import Cache, CacheBlock


class Protocol(ABC):
    class Type(Enum):
        NONE = 0
        MESI = 1
        DRAGON = 2

    @abstractmethod
    def PrRd(self, address, cycle):
        pass

    @abstractmethod
    def PrWr(self, address, cycle):
        pass

    @abstractmethod
    def Snoop(self, transaction):
        pass


# Todo: Evict block with state M should actually add a new transaction with its own address, instead of new address
class MESI(Protocol):
    class State(Enum):
        M = 0
        E = 1
        S = 2
        I = 3

    def __init__(self, core_id, cache, shared_bus):
        self.core_id = core_id
        self.cache = cache
        self.shared_bus = shared_bus

    def PrRd(self, address, cycle):

        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
        hit = False
        execution_cycle = 0

        # determine cache hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                execution_cycle += 1
                block.last_used_cycle = cycle
        # miss, load from main memory
        if not hit:
            empty_block = -1
            execution_cycle += 2
            for i, block in enumerate(cache_set):
                if block.state == 'I':
                    empty_block = i
                    break
            if empty_block != -1:  # find empty block in cache set

                if address in self.shared_bus.S:
                    state = MESI.State.S
                else:
                    state = MESI.State.E

                self.shared_bus.set_shared_block(address)
                cache_set[empty_block] = CacheBlock(tag, state, cycle)
                # execution_cycle += 2

            else:  # no empty block, cache set full, evict a block
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                if cache_set[min_lru_index].state == MESI.State.M:
                    # Write dirty block back to memory
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)
                    execution_cycle += 100

                # load from main memory
                if address in self.shared_bus.S:
                    state = MESI.State.S
                else:
                    state = MESI.State.E

                self.shared_bus.set_shared_block(address)
                cache_set[min_lru_index] = CacheBlock(tag, state, cycle)
                execution_cycle += 100

            new_transaction = Transaction(self.core_id, Transaction.Type.BusRd, address)
            self.shared_bus.add_transaction(new_transaction)
        return execution_cycle

    def PrWr(self, address, cycle):
        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
        hit = False
        execution_cycle = 0

        # determine cache hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                execution_cycle += 1
                if block.state == MESI.State.E:
                    cache_set[i] = CacheBlock(tag, MESI.State.M, cycle)
                elif block.state == MESI.State.S:
                    cache_set[i] = CacheBlock(tag, MESI.State.M, cycle)
                    new_transaction = Transaction(self.core_id, Transaction.Type.BusRdX, address)
                    self.shared_bus.add_transaction(new_transaction)
                    self.shared_bus.unset_shared_block(address)
        
        # miss, load from main memory
        if not hit:
            empty_block = -1
            execution_cycle += 2
            for i, block in enumerate(cache_set):
                if block.state == 'I':
                    empty_block = i
                    break

            if empty_block != -1:  # find empty block in cache set
                cache_set[empty_block] = CacheBlock(tag, MESI.State.M, cycle)
                # execution_cycle += 2
            else:  # no empty block, cache set full, evict a block
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                if cache_set[min_lru_index].state == MESI.State.M:
                    # Write dirty block back to memory
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)
                    execution_cycle += 100

                # load from main memory
                self.shared_bus.unset_shared_block(address)
                cache_set[min_lru_index] = CacheBlock(tag, MESI.State.M, cycle)
                execution_cycle += 100
            new_transaction = Transaction(self.core_id, Transaction.Type.BusRdX, address)
            self.shared_bus.add_transaction(new_transaction)
        return execution_cycle

    def Snoop(self, transaction):
        trans_type = transaction.trans_type
        address = transaction.address

        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]

        block_to_transit = None
        if transaction.core_id != self.core_id:
            # Implement logic for transactions issued by other processors
            for block in cache_set:
                if block.tag == tag:
                    block_to_transit = block

            if block_to_transit is None:
                return

            self.shared_bus.traffic_bytes += self.cache.block_size
            if trans_type == Transaction.Type.BusRd:
                if block_to_transit.state == MESI.State.M or block_to_transit.state == MESI.State.E:
                    block_to_transit.state = MESI.State.S
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)

            elif trans_type == Transaction.Type.BusRdX:
                if block_to_transit.state == MESI.State.M or block_to_transit.state == MESI.State.E:
                    block_to_transit.state = MESI.State.I
                    self.shared_bus.invalidations += 1
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)
                elif block_to_transit.state == MESI.State.S:
                    block_to_transit.state = MESI.State.I
                    self.shared_bus.invalidations += 1
                self.shared_bus.unset_shared_line(address)


class Dragon(Protocol):
    class State(Enum):
        M = 0
        E = 1
        Sc = 2
        Sm = 3

    def __init__(self, core_id, cache, shared_bus):
        self.core_id = core_id
        self.cache = cache
        self.shared_bus = shared_bus

    def PrRd(self, address, cycle):

        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
        hit = False
        execution_cycle = 0

        # determine cache hit, no state trasition if hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                execution_cycle += 1
                block.last_used_cycle = cycle

        # PrRdMiss, load from main memory
        if not hit:
            empty_block = -1
            execution_cycle += 2
            for i, block in enumerate(cache_set):
                # empty block is 'I' state by default
                if block.state == 'I':
                    empty_block = i
                    break
            if empty_block != -1:  # find empty block in cache set
                # determine whether this cache block is shared on bus
                if address in self.shared_bus.S: 
                    # data is retrieved from another cache
                    state = Dragon.State.Sc
                    execution_cycle += 2 * self.cache.block_size // 4
                else:
                    # data is retrieved from the main memory
                    state = Dragon.State.E
                    execution_cycle += 100

                self.shared_bus.set_shared_block(address)
                cache_set[empty_block] = CacheBlock(tag, state, cycle)
                # execution_cycle += 2

            else:  # no empty block, cache set full, evict a block
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                if cache_set[min_lru_index].state == Dragon.State.M and cache_set[min_lru_index].state == Dragon.State.Sm:
                    # Write dirty block back to memory
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)
                    execution_cycle += 100

                if cache_set[min_lru_index].state == Dragon.State.Sm:
                    # Notify other caches that hold the same data to change state
                    new_transaction = Transaction(self.core_id, Transaction.Type.BusUpd, address)
                    self.shared_bus.add_transaction(new_transaction)

                # load from main memory or other cache
                if address in self.shared_bus.S: 
                    # data is retrieved from another cache
                    state = Dragon.State.Sc
                    execution_cycle += 2 * self.cache.block_size // 4
                else:
                    # data is retrieved from the main memory
                    state = Dragon.State.E
                    execution_cycle += 100

                self.shared_bus.set_shared_block(address)
                cache_set[min_lru_index] = CacheBlock(tag, state, cycle)
                

            new_transaction = Transaction(self.core_id, Transaction.Type.BusRd, address)
            self.shared_bus.add_transaction(new_transaction)
        return execution_cycle

    def PrWr(self, address, cycle):
        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
        hit = False
        execution_cycle = 0

        # determine cache hit, if hit
        for i, block in enumerate(cache_set):
            if block.tag == tag and block.state != 'I':
                hit = True
                execution_cycle += 1
                if block.state == Dragon.State.M:
                    cache_set[i] = CacheBlock(tag, Dragon.State.M, cycle)
                elif block.state == Dragon.State.Sm and address not in self.shared_bus.S:
                    cache_set[i] = CacheBlock(tag, Dragon.State.M, cycle)
                elif block.state == Dragon.State.Sm and address in self.shared_bus.S:
                    cache_set[i] = CacheBlock(tag, Dragon.State.Sm, cycle)
                    # tell other caches that they should update their state for this particular cache line
                    new_transaction = Transaction(self.core_id, Transaction.Type.BusUpd, address)
                    self.shared_bus.add_transaction(new_transaction)
                elif block.state == Dragon.State.E:
                    cache_set[i] = CacheBlock(tag, Dragon.State.M, cycle)
                elif block.state == Dragon.State.Sc and address not in self.shared_bus.S:
                    cache_set[i] = CacheBlock(tag, Dragon.State.M, cycle)
                elif block.state == Dragon.State.Sc and address in self.shared_bus.S:
                    cache_set[i] = CacheBlock(tag, Dragon.State.Sm, cycle)
                    # tell other caches that they should update their state for this particular cache line
                    new_transaction = Transaction(self.core_id, Transaction.Type.BusUpd, address) 
                    self.shared_bus.add_transaction(new_transaction)
        
        # PrWrMiss, the cache must obtain the data block, place it in the cache, and then write the new data
        if not hit:
            empty_block = -1
            execution_cycle += 2
            for i, block in enumerate(cache_set):
                if block.state == 'I':
                    empty_block = i
                    break

            if empty_block != -1:  # find empty block in cache set
                # determine whether this address is shared on bus
                if address in self.shared_bus.S: 
                    # cache block is shared and this cache set is the owner
                    cache_set[empty_block] = CacheBlock(tag, Dragon.State.Sm, cycle)
                else:
                    # cache block is not shared 
                    cache_set[empty_block] = CacheBlock(tag, Dragon.State.M, cycle)
                # execution_cycle += 2
            else:  # no empty block, cache set full, evict a block
                min_lru_index = 0
                min_lru = cache_set[0].last_used_cycle

                for i, block in enumerate(cache_set[1:], start=1):
                    if block.last_used_cycle < min_lru:
                        min_lru = block.last_used_cycle
                        min_lru_index = i

                if cache_set[min_lru_index].state == Dragon.State.M or cache_set[min_lru_index].state == Dragon.State.Sm:
                    # Write dirty block back to memory
                    new_transaction = Transaction(self.core_id, Transaction.Type.Flush, address)
                    self.shared_bus.add_transaction(new_transaction)
                    execution_cycle += 100

                if cache_set[min_lru_index].state == Dragon.State.Sm:
                    # Notify other caches that hold the same data to change state
                    new_transaction = Transaction(self.core_id, Transaction.Type.BusUpd, address)
                    self.shared_bus.add_transaction(new_transaction)

                # load from main memory
                self.shared_bus.unset_shared_block(address)
                execution_cycle += 100
                # determine whether this address is shared on bus
                if address in self.shared_bus.S: 
                    # cache block is shared and this cache set is the owner
                    cache_set[min_lru_index] = CacheBlock(tag, Dragon.State.Sm, cycle)
                else:
                    # cache block is not shared 
                    cache_set[min_lru_index] = CacheBlock(tag, Dragon.State.M, cycle)
                
            
            new_transaction = Transaction(self.core_id, Transaction.Type.BusRd, address)
            self.shared_bus.add_transaction(new_transaction)
        return execution_cycle
    
    def Snoop(self, transaction):
        pass