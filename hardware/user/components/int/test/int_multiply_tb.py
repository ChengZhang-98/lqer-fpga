import logging
from random import randint

import cocotb
import cocotb.triggers as cc_triggers
from cocotb.utils import get_sim_time

from lqer_cocotb.testbench import Testbench
from lqer_cocotb.runner import lqer_runner
from lqer_cocotb.utils import signal_signed_integer

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


def check_msg(msg: str) -> str:
    return f"{msg} failed at {get_sim_time('us')} us"


@cocotb.test()
async def check_positive_times_positive(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MAX // 2
    b = tb.B_MAX // 2
    tb.dut.a.value = a
    tb.dut.b.value = b

    await cc_triggers.Timer(1, "us")
    assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_positive_times_positive")


@cocotb.test()
async def check_positive_times_negative(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MAX // 2
    b = tb.B_MIN // 2

    tb.dut.a.value = a
    tb.dut.b.value = b

    await cc_triggers.Timer(1, "us")
    assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_positive_times_negative")


@cocotb.test()
async def check_negative_times_negative(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MIN // 2
    b = tb.B_MIN // 2
    tb.dut.a.value = a
    tb.dut.b.value = b

    await cc_triggers.Timer(1, "us")
    assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_negative_times_negative")


@cocotb.test()
async def check_negative_times_positive(dut):
    tb = IntMultiplyTB(dut)
    a = tb.A_MIN // 2
    b = tb.B_MAX // 2
    tb.dut.a.value = a
    tb.dut.b.value = b

    await cc_triggers.Timer(1, "us")
    assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_negative_times_positive")


@cocotb.test()
async def check_random_multiply(dut):
    tb = IntMultiplyTB(dut)
    a, b = tb.generate_inputs(random=True)
    tb.dut.a.value = a
    tb.dut.b.value = b

    await cc_triggers.Timer(1, "us")
    assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_random_multiply")


@cocotb.test()
async def check_repeated_random_multiply(dut):
    NUM_ITERATIONS = 100
    tb = IntMultiplyTB(dut)
    for _ in range(NUM_ITERATIONS):
        a, b = tb.generate_inputs(random=True)
        tb.dut.a.value = a
        tb.dut.b.value = b
        await cc_triggers.Timer(1, "us")
        assert signal_signed_integer(dut.out) == tb.model(a, b), check_msg("check_repeated_random_multiply")


def generate_random_widths():
    widths = {
        "A_WIDTH": randint(2, 16),
        "B_WIDTH": randint(2, 16),
    }

    return widths


def pytest_int_multiply():
    NUM_RANDOM_TESTS = 5
    module_param_list = [
        {"A_WIDTH": 4, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 8},
        {"A_WIDTH": 2, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 4},
        {"A_WIDTH": 4, "B_WIDTH": 8},
    ]
    for _ in range(NUM_RANDOM_TESTS):
        module_param_list.append(generate_random_widths())
    lqer_runner(
        module_param_list=module_param_list,
    )


if __name__ == "__main__":
    pytest_int_multiply()
