from random import randint
from collections import deque
import math

from cocotb import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time
import numpy as np

from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.quantize import quantize_to_fixed_point
from lqer_cocotb.utils import signal_int, signal_uint


class IntAdderTreeTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        self.assign_self_params(
            "NUM_IN_WORDS",
            "BITS_PER_IN_WORD",
            "OUT_BITS",
            "SIGN_EXT",
            "REGISTER_MIDDLE",
            "REGISTER_OUTPUT",
            "EXTRA_BIT_USED",
        )

        if self.SIGN_EXT:
            self.WORD_IN_MAX = 2 ** (self.BITS_PER_IN_WORD - 1) - 1
            self.WORD_IN_MIN = -(2 ** (self.BITS_PER_IN_WORD - 1))
        else:
            self.WORD_IN_MAX = 2**self.BITS_PER_IN_WORD - 1
            self.WORD_IN_MIN = 0

    def generate_inputs(self, random: bool):
        if random:
            words_in = [randint(self.WORD_IN_MIN, self.WORD_IN_MAX) for _ in range(self.NUM_IN_WORDS)]
            extra_bit_in = randint(0, 1) if self.EXTRA_BIT_USED else None
        else:
            words_in = np.linspace(self.WORD_IN_MIN, self.WORD_IN_MAX, self.NUM_IN_WORDS)
            words_in = quantize_to_fixed_point(
                words_in,
                self.BITS_PER_IN_WORD,
                frac_width=0,
                is_signed=self.SIGN_EXT,
                rounding="nearest",
            ).tolist()
            extra_bit_in = 1 if self.EXTRA_BIT_USED else None

        return words_in, extra_bit_in

    def model(self, words_in: list[int], extra_bit_in=None) -> int:
        return sum(words_in), extra_bit_in


def check_msg(msg: str):
    return f"{msg} failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_determined_inputs_no_pipeline_reg(dut):
    tb = IntAdderTreeTB(dut)
    signal2int = signal_int if tb.SIGN_EXT else signal_uint
    await tb.reset()
    if tb.REGISTER_MIDDLE or tb.REGISTER_OUTPUT:
        return

    words_in, extra_bit_in = tb.generate_inputs(random=False)
    dut.words_in.value = words_in
    if tb.EXTRA_BIT_USED:
        dut.extra_bit_in.value = extra_bit_in
    await cc_triggers.FallingEdge(dut.clk)
    exp_out, exp_extra_bit = tb.model(words_in, extra_bit_in)
    assert signal2int(dut.out) == exp_out, check_msg("check_determined_inputs_no_pipeline_reg")
    if tb.EXTRA_BIT_USED:
        assert signal_uint(dut.extra_bit_out) == exp_extra_bit, check_msg("check_determined_inputs_no_pipeline_reg")


@cocotb.test()
async def check_random_inputs_no_pipeline_reg(dut):
    NUM_RANDOM_INPUTS = 100
    tb = IntAdderTreeTB(dut)
    signal2int = signal_int if tb.SIGN_EXT else signal_uint
    await tb.reset()
    if tb.REGISTER_MIDDLE or tb.REGISTER_OUTPUT:
        return
    for _ in range(NUM_RANDOM_INPUTS):
        words_in, extra_bit_in = tb.generate_inputs(random=True)
        exp_out, exp_extra_bit = tb.model(words_in, extra_bit_in)
        dut.words_in.value = words_in
        if tb.EXTRA_BIT_USED:
            dut.extra_bit_in.value = extra_bit_in
        await cc_triggers.FallingEdge(dut.clk)
        assert signal2int(dut.out) == exp_out, check_msg("check_random_inputs_no_pipeline_reg")
        if tb.EXTRA_BIT_USED:
            assert signal_uint(dut.extra_bit_out) == exp_extra_bit, check_msg("check_random_inputs_no_pipeline_reg")


@cocotb.test()
async def check_random_inputs_pipeline_reg(dut):
    NUM_RANDOM_INPUTS = 100
    tb = IntAdderTreeTB(dut)
    signal2int = signal_int if tb.SIGN_EXT else signal_uint
    out_queue = deque()
    exp_out_queue = deque()
    extra_bit_queue = deque()
    exp_extra_bit_queue = deque()
    await tb.reset()

    num_layers = dut.NumLayers.value
    num_prefill_cycles = (dut.REGISTER_MIDDLE.value + dut.REGISTER_OUTPUT.value) * num_layers

    for i in range(NUM_RANDOM_INPUTS + num_prefill_cycles):
        await cc_triggers.FallingEdge(dut.clk)
        if i < NUM_RANDOM_INPUTS:
            words_in, extra_bit_in = tb.generate_inputs(random=True)
            exp_out, exp_extra_bit_out = tb.model(words_in, extra_bit_in)
            exp_out_queue.append(exp_out)
            if tb.EXTRA_BIT_USED:
                exp_extra_bit_queue.append(exp_extra_bit_out)
            dut.words_in.value = words_in
            if tb.EXTRA_BIT_USED:
                dut.extra_bit_in.value = extra_bit_in

        if i >= num_prefill_cycles:
            await cc_triggers.ReadOnly()
            out = signal2int(dut.out)
            out_queue.append(out)
            if dut.EXTRA_BIT_USED.value:
                extra_bit_queue.append(signal_uint(dut.extra_bit_out))

    assert out_queue == exp_out_queue, check_msg("check_random_inputs_pipeline_reg")
    if dut.EXTRA_BIT_USED.value:
        assert extra_bit_queue == exp_extra_bit_queue, check_msg("check_random_inputs_pipeline_reg")


def generate_random_params(is_signed: bool):
    params = {
        "NUM_IN_WORDS": randint(2, 256),
        "BITS_PER_IN_WORD": randint(2, 16) if is_signed else randint(1, 16),
        "SIGN_EXT": int(is_signed),
        "REGISTER_MIDDLE": randint(0, 1),
        "REGISTER_OUTPUT": randint(0, 1),
        "EXTRA_BIT_USED": randint(0, 1),
    }
    num_layers = math.ceil(math.log2(params["NUM_IN_WORDS"]))
    params["OUT_BITS"] = params["BITS_PER_IN_WORD"] + num_layers
    return params


def pytest_adder_tree():
    NUM_RANDOM_PARAMS = 5
    # fmt: off
    param_list = [
        dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=5, SIGN_EXT=0, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # unsigned
        dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=5, SIGN_EXT=1, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # signed
        dict(NUM_IN_WORDS=3, BITS_PER_IN_WORD=4, OUT_BITS=6, SIGN_EXT=0, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # odd words_in
        dict(NUM_IN_WORDS=3, BITS_PER_IN_WORD=4, OUT_BITS=6, SIGN_EXT=1, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # odd words_in
        dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=7, SIGN_EXT=0, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # extension, output is more than input bits
        dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=7, SIGN_EXT=1, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # extension, output is more than input bits
        dict(NUM_IN_WORDS=8, BITS_PER_IN_WORD=8, OUT_BITS=11, SIGN_EXT=0, REGISTER_MIDDLE=1, REGISTER_OUTPUT=0, EXTRA_BIT_USED=1), # register middle
        dict(NUM_IN_WORDS=8, BITS_PER_IN_WORD=8, OUT_BITS=11, SIGN_EXT=0, REGISTER_MIDDLE=0, REGISTER_OUTPUT=1, EXTRA_BIT_USED=1), # register output
        dict(NUM_IN_WORDS=8, BITS_PER_IN_WORD=8, OUT_BITS=11, SIGN_EXT=0, REGISTER_MIDDLE=1, REGISTER_OUTPUT=1, EXTRA_BIT_USED=1), # register middle and output
        # doesn't support truncation. Simulation will be terminated.
        # dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=4, SIGN_EXT=0, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # truncation, output is less than input bits
        # dict(NUM_IN_WORDS=2, BITS_PER_IN_WORD=4, OUT_BITS=4, SIGN_EXT=1, REGISTER_MIDDLE=0, REGISTER_OUTPUT=0, EXTRA_BIT_USED=0), # truncation, output is less than input bits
    ]
    # fmt: on

    for _ in range(NUM_RANDOM_PARAMS):
        param_list.append(generate_random_params(is_signed=False))
        param_list.append(generate_random_params(is_signed=True))

    lqer_runner(param_list, seed=0)


if __name__ == "__main__":
    pytest_adder_tree()
