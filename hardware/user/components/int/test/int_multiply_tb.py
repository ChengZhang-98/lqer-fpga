import logging
from random import randint
import math
import copy

import numpy as np
import torch
import cocotb
from cocotb.triggers import *

from lqer_cocotb.testbench import Testbench
from lqer_cocotb.interface.streaming import StreamDriver, StreamMonitor
from lqer_cocotb.quantize import quantize_to_fixed_point
from lqer_cocotb.runner import lqer_runner

logger = logging.getLogger(f"lqer_cocotb.{__name__}")


class IntMultiplyTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, clk=None, rst=None)
        self.assign_self_params("A_WIDTH", "B_WIDTH")

        self.A_MAX = 2 ** (self.A_WIDTH - 1) - 1
        self.A_MIN = -(2 ** (self.A_WIDTH - 1))
        self.B_MAX = 2 ** (self.B_WIDTH - 1) - 1
        self.B_MIN = -(2 ** (self.B_WIDTH - 1))

    def generate_inputs(self, random: bool):
        if random:
            a = randint(self.A_MIN, self.A_MAX)
            b = randint(self.B_MIN, self.B_MAX)
        else:
            a = self.A_MAX // 2
            b = self.B_MIN // 2

        return a, b

    def model(self, a, b):
        return a * b


@cocotb.test()
async def check_positive_times_positive(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MAX // 2
    b = tb.B_MAX // 2
    tb.dut.a = a
    tb.dut.b = b

    await Timer(1, units="us")
    assert tb.dut.out.value.signed_integer == tb.model(a, b)


@cocotb.test()
async def check_positive_times_negative(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MAX // 2
    b = tb.B_MIN // 2

    tb.dut.a = a
    tb.dut.b = b

    await Timer(1, units="us")
    assert tb.dut.out.value.signed_integer == tb.model(a, b)


@cocotb.test()
async def check_negative_times_negative(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MIN // 2
    b = tb.B_MIN // 2
    tb.dut.a = a
    tb.dut.b = b

    await Timer(1, units="us")
    assert tb.dut.out.value.signed_integer == tb.model(a, b)


@cocotb.test()
async def check_negative_times_positive(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MIN // 2
    b = tb.B_MAX // 2
    tb.dut.a = a
    tb.dut.b = b

    await Timer(1, units="us")
    assert tb.dut.out.value.signed_integer == tb.model(a, b)


@cocotb.test()
async def check_random_multiply(dut):
    tb = IntMultiplyTB(dut)
    a, b = tb.generate_inputs(random=True)
    tb.dut.a = a
    tb.dut.b = b

    await Timer(1, units="us")
    assert tb.dut.out.value.signed_integer == tb.model(a, b)


@cocotb.test()
async def check_repeated_random_multiply(dut):
    tb = IntMultiplyTB(dut)
    for _ in range(100):
        a, b = tb.generate_inputs(random=True)
        tb.dut.a = a
        tb.dut.b = b
        await Timer(1, units="us")
        assert tb.dut.out.value.signed_integer == tb.model(a, b)


def generate_random_widths():
    widths = {
        "A_WIDTH": randint(2, 16),
        "B_WIDTH": randint(2, 16),
    }

    return widths


def pytest_int_multiply():
    model_param_list = [
        {"A_WIDTH": 4, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 8},
        {"A_WIDTH": 2, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 8},
    ]
    for i in range(5):
        model_param_list.append(generate_random_widths())
    lqer_runner(
        module_param_list=model_param_list,
    )


if __name__ == "__main__":
    pytest_int_multiply()
