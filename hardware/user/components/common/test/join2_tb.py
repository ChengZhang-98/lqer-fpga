from lqer_cocotb import Testbench, lqer_runner

import cocotb
import cocotb.triggers as cc_triggers
from cocotb.utils import get_sim_time

# (ready_out, valid_in_a, valid_in_b) -> (ready_in_a, ready_in_b)
TRUTH_TABLE = {
    repr((0, 0, 0)): (0, 0),
    repr((0, 0, 1)): (0, 0),
    repr((0, 1, 0)): (0, 0),
    repr((0, 1, 1)): (0, 0),
    repr((1, 0, 0)): (1, 1),
    repr((1, 0, 1)): (1, 0),
    repr((1, 1, 0)): (0, 1),
    repr((1, 1, 1)): (1, 1),
}


class Join2TB(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, None, None)

    def model(self, ready_out, valid_in_a, valid_in_b):
        ready_in_a_b = TRUTH_TABLE[repr((ready_out, valid_in_a, valid_in_b))]
        valid_out = valid_in_a and valid_in_b
        return {"ready_in_a": ready_in_a_b[0], "ready_in_b": ready_in_a_b[1], "valid_out": valid_out}


def check_msg(name: str):
    return f"{name} failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_join2(dut):
    tb = Join2TB(dut)

    for ready_out in [0, 1]:
        for valid_in_a in [0, 1]:
            for valid_in_b in [0, 1]:
                dut.ready_out.value = ready_out
                dut.valid_in_a.value = valid_in_a
                dut.valid_in_b.value = valid_in_b
                expect_out = tb.model(ready_out, valid_in_a, valid_in_b)
                await cc_triggers.Timer(1, "us")
                assert dut.ready_in_a.value == expect_out["ready_in_a"], check_msg("check 'ready_in_a'")
                assert dut.ready_in_b.value == expect_out["ready_in_b"], check_msg("check 'ready_in_b'")
                assert dut.valid_out.value == expect_out["valid_out"], check_msg("check 'valid_out'")


def pytest_join2():
    lqer_runner()


if __name__ == "__main__":
    pytest_join2()
