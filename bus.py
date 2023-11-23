from collections import deque
from enum import Enum


class Transaction:
    class Type(Enum):
        BusRd = 0
        BusRdX = 1
        Flush = 2
        BusUpd = 3

    def __init__(self, core_id, trans_type, address):
        self.core_id = core_id
        self.trans_type = trans_type
        self.address = address


class Bus:
    def __init__(self):
        self.S = {}
        self.queue = deque()
        self.traffic_bytes = 0
        self.invalidations = 0

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

    def add_transaction(self, transaction):
        self.queue.appendleft(transaction)

    def get_next_transaction(self):
        return self.queue.pop()
    
    def output(self):
        print('===== REPORT FOR BUS =====')
        print('Data Traffic (Bytes):', self.traffic_bytes)
        print('Invalidations:', self.invalidations)
        # print('Access to Private Data:', self.private_access/(self.private_access + self.public_access))
        # print('Access to Public Data:', self.public_access / (self.private_access + self.public_access))
        print('\n')