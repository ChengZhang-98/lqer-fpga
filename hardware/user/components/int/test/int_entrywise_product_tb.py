from random import randint

from cocotb import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time
import numpy as np

from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.interface import StreamDriver, StreamMonitor, bit_driver
from lqer_cocotb.quantize import quantize_to_fixed_point


class IntEntrywiseProductTB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        self.assign_self_params("A_WIDTH", "B_WIDTH", "A_DIM_0_B_DIM_0")
        self.data_in_a_driver = StreamDriver(dut.clk, dut.data_in_a, dut.valid_in_a, dut.ready_in_a)
        self.data_in_b_driver = StreamDriver(dut.clk, dut.data_in_b, dut.valid_in_b, dut.ready_in_b)
        self.data_out_monitor = StreamMonitor(
            dut.clk, dut.data_out, dut.valid_out, dut.ready_out, check_fmt="signed_integer"
        )

        self.DATA_IN_A_MAX = 2 ** (self.A_WIDTH - 1) - 1
        self.DATA_IN_A_MIN = -(2 ** (self.A_WIDTH - 1))

        self.DATA_IN_B_MAX = 2 ** (self.B_WIDTH - 1) - 1
        self.DATA_IN_B_MIN = -(2 ** (self.B_WIDTH - 1))

    def generate_inputs(self, random: bool):
        if random:
            a = [randint(self.DATA_IN_A_MIN, self.DATA_IN_A_MAX) for _ in range(self.A_DIM_0_B_DIM_0)]
            b = [randint(self.DATA_IN_B_MIN, self.DATA_IN_B_MAX) for _ in range(self.A_DIM_0_B_DIM_0)]
        else:
            a = np.linspace(self.DATA_IN_A_MIN, self.DATA_IN_A_MAX, self.A_DIM_0_B_DIM_0)
            b = np.linspace(self.DATA_IN_B_MIN, self.DATA_IN_B_MAX, self.A_DIM_0_B_DIM_0)
            a = quantize_to_fixed_point(a, self.A_WIDTH, frac_width=0, is_signed=True, rounding="nearest").tolist()
            b = quantize_to_fixed_point(b, self.B_WIDTH, frac_width=0, is_signed=True, rounding="nearest").tolist()
        return {"data_in_a": a, "data_in_b": b}

    def model(self, data_in_a, data_in_b):
        # ensure data_in_a/b is a list of integers
        # ensure len(data_in_a) == len(data_in_b)
        out = [a * b for a, b in zip(data_in_a, data_in_b)]
        return out


def check_msg(msg: str):
    return f"{msg} failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_determined_inputs_no_back_pressure(dut):
    tb = IntEntrywiseProductTB(dut)
    tb.data_in_a_driver.set_valid_prob(1.0)
    tb.data_in_b_driver.set_valid_prob(1.0)
    tb.data_out_monitor.ready.value = 1

    inputs = tb.generate_inputs(random=False)
    tb.data_in_a_driver.append(inputs["data_in_a"])
    tb.data_in_b_driver.append(inputs["data_in_b"])

    exp_out = tb.model(**inputs)
    tb.data_out_monitor.expect(exp_out)

    await cc_triggers.Timer(100, "us")
    assert tb.data_out_monitor.exp_queue.empty(), check_msg("check_determined_inputs_no_back_pressure")


@cocotb.test()
async def check_random_inputs_no_back_pressure(dut):
    NUM_ITERATIONS = 100

    tb = IntEntrywiseProductTB(dut)
    tb.data_in_a_driver.set_valid_prob(1.0)
    tb.data_in_b_driver.set_valid_prob(1.0)
    tb.data_out_monitor.ready.value = 1

    for _ in range(NUM_ITERATIONS):
        inputs = tb.generate_inputs(random=True)
        tb.data_in_a_driver.append(inputs["data_in_a"])
        tb.data_in_b_driver.append(inputs["data_in_b"])

        exp_out = tb.model(**inputs)
        tb.data_out_monitor.expect(exp_out)

    await cc_triggers.Timer(NUM_ITERATIONS, "us")
    assert tb.data_out_monitor.exp_queue.empty(), check_msg("check_random_inputs_no_back_pressure")


@cocotb.test()
async def check_determined_inputs_with_back_pressure(dut):
    NUM_ITERATIONS = 100
    tb = IntEntrywiseProductTB(dut)
    tb.data_in_a_driver.set_valid_prob(0.8)
    tb.data_in_b_driver.set_valid_prob(0.8)
    cocotb.start_soon(bit_driver(tb.data_out_monitor.ready, clk=dut.clk, prob=0.5))

    for _ in range(NUM_ITERATIONS):
        inputs = tb.generate_inputs(random=False)
        tb.data_in_a_driver.append(inputs["data_in_a"])
        tb.data_in_b_driver.append(inputs["data_in_b"])

        exp_out = tb.model(**inputs)
        tb.data_out_monitor.expect(exp_out)

    await cc_triggers.Timer(NUM_ITERATIONS, "us")
    assert tb.data_out_monitor.exp_queue.empty(), check_msg("check_determined_inputs_with_back_pressure")


@cocotb.test()
async def check_random_inputs_with_back_pressure(dut):
    NUM_ITERATIONS = 100
    tb = IntEntrywiseProductTB(dut)
    tb.data_in_a_driver.set_valid_prob(0.8)
    tb.data_in_b_driver.set_valid_prob(0.8)
    cocotb.start_soon(bit_driver(tb.data_out_monitor.ready, clk=dut.clk, prob=0.5))

    for _ in range(NUM_ITERATIONS):
        inputs = tb.generate_inputs(random=True)
        tb.data_in_a_driver.append(inputs["data_in_a"])
        tb.data_in_b_driver.append(inputs["data_in_b"])

        exp_out = tb.model(**inputs)
        tb.data_out_monitor.expect(exp_out)

    await cc_triggers.Timer(NUM_ITERATIONS, "us")
    assert tb.data_out_monitor.exp_queue.empty(), check_msg("check_random_inputs_with_back_pressure")


def generate_random_module_params():
    params = {"A_WIDTH": randint(2, 16), "B_WIDTH": randint(2, 16), "A_DIM_0_B_DIM_0": randint(1, 32)}
    return params


def pytest_int_entrywise_product():
    NUM_RANDOM_TESTS = 5
    module_param_list = [
        {"A_WIDTH": 2, "B_WIDTH": 2, "A_DIM_0_B_DIM_0": 4},
        {"A_WIDTH": 2, "B_WIDTH": 4, "A_DIM_0_B_DIM_0": 16},
        {"A_WIDTH": 4, "B_WIDTH": 8, "A_DIM_0_B_DIM_0": 16},
        {"A_WIDTH": 8, "B_WIDTH": 8, "A_DIM_0_B_DIM_0": 16},
        {"A_WIDTH": 16, "B_WIDTH": 16, "A_DIM_0_B_DIM_0": 16},
    ]
    for _ in range(NUM_RANDOM_TESTS):
        module_param_list.append(generate_random_module_params())

    lqer_runner(module_param_list)


if __name__ == "__main__":
    pytest_int_entrywise_product()
