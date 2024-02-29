import random
import numpy as np
from cocotb.binary import BinaryValue
from cocotb.triggers import *

from .driver import Driver
from .monitor import Monitor


class StreamDriver(Driver):
    def __init__(self, clk, data, valid, ready, valid_prob=1.0) -> None:
        super().__init__()
        self.clk = clk
        self.data = data
        self.valid = valid
        self.ready = ready
        self.valid_prob = valid_prob

    def set_valid_prob(self, prob: float):
        assert prob >= 0.0 and prob <= 1.0
        self.valid_prob = prob

    async def _driver_send(self, data) -> None:
        while True:
            await FallingEdge(self.clk)
            if random.random() > self.valid_prob:
                self.valid.value = 0
                continue  # Try roll random valid again at next clock
            self.data.value = data
            self.valid.value = 1
            await ReadOnly()
            if self.ready.value == 1:
                self.logger.debug(f"Sent {data}")
                break

        if self.send_queue.empty():
            await FallingEdge(self.clk)
            self.valid.value = 0


class StreamMonitor(Monitor):
    def __init__(self, clk, data, valid, ready, check=True):
        super().__init__(clk)
        self.clk = clk
        self.data = data
        self.valid = valid
        self.ready = ready
        self.check = check

    def _trigger(self):
        return self.valid.value == 1 and self.ready.value == 1

    def _recv(self):
        if type(self.data.value) == list:
            return [int(x) for x in self.data.value]
        elif type(self.data.value) == BinaryValue:
            return int(self.data.value)
        else:
            raise ValueError(f"Data type not supported: {type(self.data.value)}")

    def _check(self, got, exp):
        if not self.check:
            return
        assert np.equal(got, exp).all(), f"Got \n{got}, \nExpected \n{exp}"
