from random import randint
import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time
from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.interface import StreamDriver, StreamMonitor, bit_driver
from lqer_cocotb.utils import signal_integer


class SkidBufferTB(Testbench):
    def __init__(self, dut, enable_driver: bool) -> None:
        super().__init__(dut, dut.clk, dut.rst)
        self.assign_self_params("DATA_WIDTH", "CIRCULAR_BUFFER_MODE")

        self.DATA_IN_MIN = 0
        self.DATA_IN_MAX = 2**self.DATA_WIDTH - 1

        self.EMPTY = 0
        self.BUSY = 1
        self.FULL = 2

        if enable_driver:
            self.input_driver = StreamDriver(dut.clk, dut.data_in, dut.valid_in, dut.ready_in)
            self.output_monitor = StreamMonitor(
                dut.clk, dut.data_out, dut.valid_out, dut.ready_out, check_fmt="unsigned_integer"
            )

    def generate_inputs(self, random: bool):
        if not random:
            return self.DATA_IN_MAX
        else:
            return randint(self.DATA_IN_MIN, self.DATA_IN_MAX)

    def model(self, data_in):
        return data_in


def generate_random_data_widths():
    params = {"DATA_WIDTH": randint(1, 64)}
    return params


def check_msg(name: str):
    return f"{name} check failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_rst(dut):
    tb = SkidBufferTB(dut, enable_driver=False)
    dut.ready_in.value = 1
    await tb.reset()
    assert signal_integer(dut.state_cur) == tb.EMPTY, check_msg("rst")


@cocotb.test()
async def check_control_path(dut):
    """
    Check the control flow FSM states transfer of skid_buffer

    This test goes through the following states counterclockwise:
    Empty - load -> Busy - flow -> Busy - fill -> Full [- dump -> Full - pass -> Full] - flush -> Busy - flow -> Busy - unload -> Empty

    ```txt
                    /--\  +- flow
                    |  |
            load   |  v   fill
     -------   +    ------   +    ------         (CBM)
    |       | ---> |      | ---> |      | ---\  +  dump
    | Empty |      | Busy |      | Full |    |    or
    |       | <--- |      | <--- |      | <--/  +- pass
     -------    -   ------    -   ------
            unload         flush
    ```
    """
    tb = SkidBufferTB(dut, enable_driver=False)
    dut.valid_in.value = 1
    dut.ready_out.value = 1
    dut.data_in.value = tb.DATA_IN_MAX
    await tb.reset()
    tb.log_sim_time("check_control_path reset")
    # load
    assert signal_integer(dut.load) == 1, check_msg("data path state 'load'")
    # EMPTY -> BUSY
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.BUSY, check_msg("FSM state 'BUSY'")
    # flow
    assert signal_integer(dut.flow) == 1, check_msg("data path state 'flow'")
    # BUSY -> BUSY
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.BUSY, check_msg("FSM state 'BUSY'")
    # fill
    dut.ready_out.value = 0
    await cc_triggers.ReadOnly()
    assert signal_integer(dut.fill) == 1, check_msg("data path state 'fill'")
    # BUSY -> FULL
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.FULL, check_msg("FSM state 'FULL'")
    if tb.CIRCULAR_BUFFER_MODE:
        # dump
        assert signal_integer(dut.dump) == 1, check_msg("data path state 'dump'")
        # FULL -> FULL
        await cc_triggers.FallingEdge(dut.clk)
        assert signal_integer(dut.state_cur) == tb.FULL, check_msg("FSM state 'FULL'")
        "Now valid_in should still be 1"
        dut.ready_out.value = 1
        await cc_triggers.ReadOnly()
        # pass
        assert signal_integer(getattr(dut, "pass")) == 1, check_msg("data path state 'pass'")
        # FULL -> FULL
        await cc_triggers.FallingEdge(dut.clk)
        assert signal_integer(dut.state_cur) == tb.FULL, check_msg("FSM state 'FULL'")
    else:
        "Now valid_in should be 0"
    dut.valid_in.value = 0
    dut.ready_out.value = 1
    # flush
    await cc_triggers.ReadOnly()
    assert signal_integer(dut.flush) == 1, check_msg("data path state 'flush'")
    # FULL -> BUSY
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.BUSY, check_msg("FSM state 'BUSY'")
    dut.valid_in.value = 1
    dut.ready_out.value = 1
    # fill
    await cc_triggers.ReadOnly()
    assert signal_integer(dut.flow) == 1, check_msg("data path state 'flow'")
    # BUSY -> BUSY
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.BUSY, check_msg("FSM state 'BUSY'")
    dut.valid_in.value = 0
    dut.ready_out.value = 1
    # unload
    await cc_triggers.ReadOnly()
    assert signal_integer(dut.unload) == 1, check_msg("data path state 'unload'")
    # BUSY -> EMPTY
    await cc_triggers.FallingEdge(dut.clk)
    assert signal_integer(dut.state_cur) == tb.EMPTY, check_msg("FSM state 'EMPTY'")


@cocotb.test()
async def check_data_path_no_back_pressure(dut):
    NUM_TRANSACTIONS = 100
    tb = SkidBufferTB(dut, enable_driver=True)
    await tb.reset()
    tb.log_sim_time("check_data_path_no_beck_pressure reset")
    tb.output_monitor.ready.value = 1
    tb.input_driver.set_valid_prob(0.5)

    for _ in range(NUM_TRANSACTIONS):
        data_in = tb.generate_inputs(random=True)
        expect_out = tb.model(data_in)
        tb.input_driver.append(data_in)
        tb.output_monitor.expect(expect_out)

    await cc_triggers.Timer(NUM_TRANSACTIONS, units="us")
    assert tb.output_monitor.exp_queue.empty()


@cocotb.test()
async def check_data_path_CBM(dut):
    if dut.CIRCULAR_BUFFER_MODE == 0:
        return
    tb = SkidBufferTB(dut, enable_driver=False)
    await tb.reset()
    data_in_0 = tb.generate_inputs(random=True)
    dut.data_in.value = data_in_0
    dut.valid_in.value = 1
    dut.ready_out.value = 0
    tb.log_sim_time("check_data_path_CBM")
    if tb.CIRCULAR_BUFFER_MODE:
        await cc_triggers.FallingEdge(dut.clk)  # BUSY
        await cc_triggers.FallingEdge(dut.clk)  # FULL
        assert signal_integer(dut.state_cur) == tb.FULL, check_msg("FSM state 'FULL'")
        assert signal_integer(dut.data_out) == data_in_0, check_msg("data path 'data_out'")
        data_in_1 = tb.generate_inputs(random=True)
        dut.data_in.value = data_in_1
        await cc_triggers.FallingEdge(dut.clk)
        assert signal_integer(dut.data_out) == data_in_0
        assert signal_integer(dut.data_buffer_out) == data_in_1
    else:
        tb.log_sim_time("Skip check_data_path_circular_buffer_mode (CIRCULAR_BUFFER_MODEl==0)")
        pass


@cocotb.test()
async def check_data_path_back_pressure_no_CBM(dut):
    NUM_ITERATIONS = 100
    if dut.CIRCULAR_BUFFER_MODE == 1:
        return
    tb = SkidBufferTB(dut, enable_driver=True)
    cocotb.start_soon(bit_driver(dut.ready_out, clk=dut.clk, prob=0.5))
    tb.input_driver.set_valid_prob(0.8)
    await tb.reset()
    tb.log_sim_time("check_data_path_back_pressure_no_CBM reset")

    for _ in range(NUM_ITERATIONS):
        data_in = tb.generate_inputs(random=True)
        expect_out = tb.model(data_in)
        tb.input_driver.append(data_in)
        tb.output_monitor.expect(expect_out)
    await cc_triggers.Timer(NUM_ITERATIONS, units="us")
    assert tb.output_monitor.exp_queue.empty()


def pytest_skid_buffer():
    NUM_RANDOM_TESTS = 10
    param_list = [
        {"DATA_WIDTH": 1, "CIRCULAR_BUFFER_MODE": 0},
        {"DATA_WIDTH": 1, "CIRCULAR_BUFFER_MODE": 1},
        {"DATA_WIDTH": 8, "CIRCULAR_BUFFER_MODE": 0},
        {"DATA_WIDTH": 8, "CIRCULAR_BUFFER_MODE": 1},
    ]

    for _ in range(NUM_RANDOM_TESTS):
        param_list.append(generate_random_data_widths() | {"CIRCULAR_BUFFER_MODE": 0})
        param_list.append(generate_random_data_widths() | {"CIRCULAR_BUFFER_MODE": 1})

    lqer_runner(param_list)


if __name__ == "__main__":
    pytest_skid_buffer()
