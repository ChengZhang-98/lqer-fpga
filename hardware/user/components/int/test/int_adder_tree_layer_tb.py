from random import randint

import numpy as np
import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time

from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.utils import array1d_int, array1d_uint
from lqer_cocotb.quantize import quantize_to_fixed_point


class IntAdderTreeLayerTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        self.assign_self_params(
            "NUM_IN_WORDS",
            "BITS_PER_IN_WORD",
            "BITS_PER_IN_WORD",
            "BITS_PER_OUT_WORD",
            "SIGN_EXT",
            "REGISTER_MIDDLE",
            "REGISTER_OUTPUT",
            "EXTRA_BIT_CONNECTED",
        )

        if self.SIGN_EXT:
            self.IN_MAX = 2 ** (self.BITS_PER_IN_WORD - 1) - 1
            self.IN_MIN = -(2 ** (self.BITS_PER_IN_WORD - 1))
        else:
            self.IN_MAX = 2**self.BITS_PER_IN_WORD - 1
            self.IN_MIN = 0

    def generate_inputs(self, random: bool):
        if random:
            words_in = [randint(self.IN_MIN, self.IN_MAX) for _ in range(self.NUM_IN_WORDS)]
        else:
            words_in = np.linspace(self.IN_MIN, self.IN_MAX, self.NUM_IN_WORDS)
            words_in = quantize_to_fixed_point(
                words_in,
                self.BITS_PER_IN_WORD,
                frac_width=0,
                is_signed=self.SIGN_EXT,
                rounding="nearest",
            ).tolist()
        return words_in

    def model(self, words_in: list[int]) -> int:
        words_out = []
        for pair_id in range(self.dut.NumInPairs.value):
            words_out.append(words_in[2 * pair_id] + words_in[2 * pair_id + 1])

        if self.dut.NumInOdd.value:
            words_out.append(words_in[-1])

        return words_out


def check_msg(msg: str):
    return f"{msg} failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_determined_inputs(dut):
    tb = IntAdderTreeLayerTB(dut)
    await tb.reset()
    inputs = tb.generate_inputs(random=False)
    exp_out = tb.model(inputs)

    dut.words_in.value = inputs
    await cc_triggers.Timer(1, "us")

    array1d2int = array1d_int if tb.SIGN_EXT else array1d_uint
    assert array1d2int(dut.words_out) == exp_out, check_msg("check_determined_inputs")


@cocotb.test()
async def check_random_inputs(dut):
    tb = IntAdderTreeLayerTB(dut)
    await tb.reset()
    inputs = tb.generate_inputs(random=True)
    exp_out = tb.model(inputs)

    dut.words_in.value = inputs
    await cc_triggers.Timer(1, "us")

    array1d2int = array1d_int if tb.SIGN_EXT else array1d_uint
    assert array1d2int(dut.words_out) == exp_out, check_msg("check_random_inputs")


def generate_random_params(sign_ext: bool):
    params = {
        "NUM_IN_WORDS": randint(1, 16),
        "BITS_PER_IN_WORD": randint(1, 10),
        "SIGN_EXT": sign_ext,
        "REGISTER_MIDDLE": randint(0, 1),
        "REGISTER_OUTPUT": randint(0, 1),
        "EXTRA_BIT_CONNECTED": randint(0, 1),
    }

    params["BITS_PER_OUT_WORD"] = params["BITS_PER_IN_WORD"] + 1
    return params


def pytest_int_adder_tree_layer():
    NUM_RANDOM_TESTS = 10
    param_list = [
        {
            "NUM_IN_WORDS": 4,
            "BITS_PER_IN_WORD": 4,
            "BITS_PER_OUT_WORD": 5,
            "SIGN_EXT": 0,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
            "EXTRA_BIT_CONNECTED": 0,
        },
        {
            "NUM_IN_WORDS": 4,
            "BITS_PER_IN_WORD": 4,
            "BITS_PER_OUT_WORD": 5,
            "SIGN_EXT": 1,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
            "EXTRA_BIT_CONNECTED": 0,
        },
        {
            "NUM_IN_WORDS": 5,
            "BITS_PER_IN_WORD": 4,
            "BITS_PER_OUT_WORD": 5,
            "SIGN_EXT": 0,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
            "EXTRA_BIT_CONNECTED": 0,
        },
        {
            "NUM_IN_WORDS": 4,
            "BITS_PER_IN_WORD": 4,
            "BITS_PER_OUT_WORD": 5,
            "SIGN_EXT": 1,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
            "EXTRA_BIT_CONNECTED": 0,
        },
    ]
    for _ in range(NUM_RANDOM_TESTS):
        param_list.append(generate_random_params(sign_ext=0))
        param_list.append(generate_random_params(sign_ext=1))

    lqer_runner(param_list)


if __name__ == "__main__":
    pytest_int_adder_tree_layer()
