from collections import deque
from enum import Enum


class Transaction:
    class Type(Enum):
        BusRd = 0
        BusRdX = 1
        Flush = 2

    def __init__(self, core_id, trans_type, address):
        self.core_id = core_id
        self.trans_type = trans_type
        self.address = address


class Bus:
    def __init__(self):
        self.S = {}
        self.queue = deque()

    def set_shared_block(self, address):
        if address in self.S:
            self.S[address] += 1
        else:
            self.S[address] = 1

    def unset_shared_block(self, address):
        if address in self.S:
            if self.S[address] > 0:
                self.S[address] -= 1
                if self.S[address] == 0:
                    del self.S[address]

    def add_transaction(self, trans_type, new_transaction):
        pass  # Implement add_transaction logic for shared bus