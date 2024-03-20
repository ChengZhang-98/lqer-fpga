from random import randint
from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.utils import signal_int
import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time


class RegisterSliceTB(Testbench):
    def __init__(self, dut, clk=None, rst=None) -> None:
        super().__init__(dut, dut.clk, dut.rst)
        self.assign_self_params("DATA_WIDTH", "RESET_VALUE")
        self.DATA_MIN = 0
        self.DATA_MAX = 2**self.DATA_WIDTH - 1

    def generate_inputs(self, random: bool):
        if random:
            return randint(self.DATA_MIN, self.DATA_MAX)
        else:
            return 1

    def model(self, data_in):
        return data_in


@cocotb.test()
async def check_rst(dut):
    tb = RegisterSliceTB(dut)
    data_in = tb.generate_inputs(random=False)
    dut.data_in.value = data_in
    dut.clk_en.value = 1
    await tb.reset()
    tb.log_sim_time("check_rst reset")
    assert signal_int(dut.data_out) == dut.RESET_VALUE, f"rst check failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_clk_en(dut):
    tb = RegisterSliceTB(dut)
    data_in = tb.generate_inputs(random=False)
    dut.data_in.value = data_in
    dut.clk_en.value = 0
    await tb.reset()
    tb.log_sim_time("check_clk_en reset")
    await cc_triggers.RisingEdge(dut.clk)
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_int(dut.data_out) == dut.RESET_VALUE, f"clk_en check failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_determined_data_in(dut):
    tb = RegisterSliceTB(dut)
    # test clk_en
    data_in = tb.generate_inputs(random=False)
    dut.data_in.value = data_in
    dut.clk_en.value = 1
    await tb.reset()
    tb.log_sim_time("check_determined_data_in reset")
    # test data insert and remove (clk_en = 1)
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_int(dut.data_out) == tb.model(data_in), f"reg check failed (clk_en = 1) at {get_sim_time('ns')}"
    data_in = tb.DATA_MAX // 2
    dut.data_in.value = data_in
    await cc_triggers.FallingEdge(dut.clk)
    # test data insert and remove (clk_en = 1)
    assert signal_int(dut.data_out) == tb.model(data_in), f"reg check failed (clk_en = 1) at {get_sim_time('ns')}"
    dut.clk_en.value = 0
    dut.data_in.value = tb.DATA_MAX
    await cc_triggers.FallingEdge(dut.clk)
    # test data keep
    assert signal_int(dut.data_out) == tb.model(data_in), f"reg check failed (clk_en = 0) at {get_sim_time('ns')}"


@cocotb.test()
async def check_random_data_in(dut):
    NUM_ITERATIONS = 100
    tb = RegisterSliceTB(dut)
    dut.clk_en.value = 1
    await tb.reset()
    tb.log_sim_time("check_random_data_in reset")
    await cc_triggers.FallingEdge(dut.clk)
    data_in = tb.generate_inputs(random=True)
    dut.data_in.value = data_in
    for i in range(NUM_ITERATIONS):
        await cc_triggers.FallingEdge(dut.clk)
        assert signal_int(dut.data_out) == tb.model(data_in), f"random check failed at {get_sim_time('ns')}"
        data_in = tb.generate_inputs(random=True)
        dut.data_in.value = data_in


def generate_random_module_params():
    params = {"DATA_WIDTH": randint(1, 256), "RESET_VALUE": 0}
    return params


def pytest_register_slice():
    NUM_RANDOM_TESTS = 5
    module_param_list = [
        {"DATA_WIDTH": 1, "RESET_VALUE": 0},
        {"DATA_WIDTH": 1, "RESET_VALUE": 1},
        {"DATA_WIDTH": 8, "RESET_VALUE": 0},
        {"DATA_WIDTH": 8, "RESET_VALUE": 255},
    ]

    for _ in range(NUM_RANDOM_TESTS):
        module_param_list.append(generate_random_module_params())

    lqer_runner(module_param_list)


if __name__ == "__main__":
    pytest_register_slice()
