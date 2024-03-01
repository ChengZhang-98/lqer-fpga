import random
import numpy as np
from cocotb.binary import BinaryValue

import cocotb.triggers as cc_triggers

from .driver import Driver
from .monitor import Monitor
from .utils import binary_value_to_binstr, binary_value_to_integer, binary_value_to_signed_integer


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
            await cc_triggers.FallingEdge(self.clk)
            if random.random() > self.valid_prob:
                self.valid.value = 0
                continue  # Try roll random valid again at next clock
            self.data.value = data
            self.valid.value = 1
            await cc_triggers.ReadOnly()
            if self.ready.value == 1:
                self.logger.debug(f"Sent {data}")
                break

        if self.send_queue.empty():
            await cc_triggers.FallingEdge(self.clk)
            self.valid.value = 0


class StreamMonitor(Monitor):
    def __init__(self, clk, data, valid, ready, check=True, check_fmt="signed_integer"):
        super().__init__(clk, check=check)
        self.clk = clk
        self.data = data
        self.valid = valid
        self.ready = ready

        assert check_fmt in ["binstr", "integer", "unsigned_integer", "signed_integer"]
        self.check_fmt = check_fmt

    def _value_to_check(self, value):
        match self.check_fmt:
            case "binstr":
                return binary_value_to_binstr(value)
            case "integer" | "unsigned_integer":
                return binary_value_to_integer(value)
            case "signed_integer":
                return binary_value_to_signed_integer(value)
            case _:
                raise ValueError(f"Invalid check_fmt: {self.check_fmt}")

    def _trigger(self):
        return self.valid.value == 1 and self.ready.value == 1

    def _recv(self):
        if type(self.data.value) == list:
            return [self._value_to_check(x) for x in self.data.value]
        elif type(self.data.value) == BinaryValue:
            return self._value_to_check(self.data.value)
        else:
            raise ValueError(f"Data type not supported: {type(self.data.value)}")

    def _check(self, got, exp):
        if not self.check:
            return
        assert np.equal(got, exp).all(), f"Got \n{got}, \nExpected \n{exp}"
