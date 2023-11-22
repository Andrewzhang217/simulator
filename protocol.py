from abc import ABC, abstractmethod
from enum import Enum
from bus import Bus, Transaction


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

    # Todo: prrd prwr write back
    # if selectedState.get_state() == State.M:
    #     # Write back to memory
    #     new_transaction = Transaction(core_id, TransactionType.BusWr, address)
    #     sharedBus.add_transaction(Transaction.Type.BusWr, new_transaction)

    def PrRd(self, address, cycle):

        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
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

            new_transaction = Transaction(self.core_id, Transaction.Type.BusRd, address)
            self.shared_bus.add_transaction(Transaction.Type.BusRd, new_transaction)

    def PrWr(self, address, cycle):
        tag_bits = address[:len(address) - self.cache.index_bits - self.cache.offset_bits]
        index_bits = address[len(address) - self.cache.index_bits - self.cache.offset_bits:len(
            address) - self.cache.offset_bits]

        index = int(index_bits, 2)
        tag = int(tag_bits, 2)
        cache_set = self.cache.blocks[index]
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
            new_transaction = Transaction(self.core_id, Transaction.Type.BusRdX, address)
            self.shared_bus.add_transaction(Transaction.Type.BusRdX, new_transaction)

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

            if trans_type == Transaction.Type.BusRd:
                if block_to_transit.state == MESI.State.M or block_to_transit.state == MESI.State.E:
                    block_to_transit.state = MESI.State.S
                    new_transaction = Transaction(
                        self.core_id,
                        Transaction.Type.Flush,
                        address
                    )
                    self.shared_bus.add_transaction(
                        Transaction.Type.BusWr,
                        new_transaction
                    )

            elif trans_type == Transaction.Type.BusRdX:
                if block_to_transit.state == MESI.State.M or block_to_transit.state == MESI.State.E:
                    block_to_transit.state = MESI.State.I
                    new_transaction = Transaction(
                        self.core_id,
                        Transaction.Type.Flush,
                        address
                    )
                    self.shared_bus.add_transaction(
                        Transaction.Type.BusWr,
                        new_transaction
                    )
                elif block_to_transit.state == MESI.State.S:
                    block_to_transit.state = MESI.State.I
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
