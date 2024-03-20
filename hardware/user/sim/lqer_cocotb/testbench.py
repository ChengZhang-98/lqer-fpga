import cocotb
from cocotb.triggers import *
from cocotb.clock import Clock
from cocotb.log import SimLog
from cocotb.utils import get_sim_time


class Testbench:
    def __init__(self, dut, clk=None, rst=None) -> None:
        self.dut = dut
        self.clk = clk
        self.rst = rst

        self.logger = SimLog(f"lqer_cocotb.{type(self).__qualname__}")

        self.input_drivers = []
        self.output_monitors = []

        if self.clk is not None:
            self.clock = Clock(self.clk, 20, units="ns")
            cocotb.start_soon(self.clock.start())

    def assign_self_params(self, *attrs):
        for att in attrs:
            setattr(self, att, getattr(self.dut, att).value)

    async def reset(self, active_high=True):
        if self.rst is None:
            raise Exception(
                "Cannot reset. Either a reset wire was not provided or " + "the module does not have a reset."
            )

        await RisingEdge(self.clk)
        self.rst.value = 1 if active_high else 0
        await RisingEdge(self.clk)
        self.rst.value = 0 if active_high else 1
        await FallingEdge(self.clk)

    def generate_inputs(self, random: bool):
        raise NotImplementedError

    def log_sim_time(self, msg: str):
        self.logger.info(f"{get_sim_time('ns')} ns: {msg}")
