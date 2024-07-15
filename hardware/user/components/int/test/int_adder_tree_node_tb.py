from random import randint

import cocotb
from cocotb import triggers as cc_triggers
from cocotb.utils import get_sim_time

from lqer_cocotb import Testbench, lqer_runner
from lqer_cocotb.utils import signal_int, signal_uint, unsigned_extend


class IntAdderTreeNode(Testbench):
    def __init__(self, dut) -> None:
        super().__init__(dut, dut.clk, dut.rst)

        self.assign_self_params(
            "IN_BITS", "OUT_BITS", "SIGN_EXT", "REGISTER_MIDDLE", "REGISTER_OUTPUT"
        )

        if self.SIGN_EXT:
            self.IN_MAX = 2 ** (self.IN_BITS - 1) - 1
            self.IN_MIN = -(2 ** (self.IN_BITS - 1))
        else:
            self.IN_MAX = 2**self.IN_BITS - 1
            self.IN_MIN = 0

    def generate_inputs(self, random: bool):
        if random:
            a = randint(self.IN_MIN, self.IN_MAX)
            b = randint(self.IN_MIN, self.IN_MAX)

        else:
            if self.SIGN_EXT:
                a = self.IN_MAX
                b = self.IN_MIN // 2
            else:
                a = self.IN_MAX
                b = self.IN_MAX // 2

        return {"a": a, "b": b}

    def model(self, a: int, b: int) -> int:
        return a + b


def check_msg(msg: str):
    return f"{msg} failed at {get_sim_time('ns')}"


@cocotb.test()
async def check_determined_inputs(dut):
    tb = IntAdderTreeNode(dut)
    await tb.reset()
    inputs = tb.generate_inputs(random=False)
    dut.a.value = inputs["a"]
    dut.b.value = inputs["b"]
    exp_out = tb.model(**inputs)

    await cc_triggers.Timer(1, "us")

    signal2int = signal_int if tb.SIGN_EXT else signal_uint
    assert signal2int(dut.out) == exp_out, check_msg("check_determined_inputs")


@cocotb.test()
async def check_random_inputs(dut):
    NUM_ITERATIONS = 100
    tb = IntAdderTreeNode(dut)
    await tb.reset()

    for _ in range(NUM_ITERATIONS):
        inputs = tb.generate_inputs(random=True)
        dut.a.value = inputs["a"]
        dut.b.value = inputs["b"]
        exp_out = tb.model(**inputs)

        await cc_triggers.Timer(1, "us")
        signal2int = signal_int if tb.SIGN_EXT else signal_uint
        assert signal2int(dut.out) == exp_out, check_msg("check_random_inputs")


@cocotb.test()
async def check_pipeline_register_middle_values(dut):
    tb = IntAdderTreeNode(dut)

    signal2int = signal_int if tb.SIGN_EXT else signal_uint
    if not tb.REGISTER_MIDDLE:
        return
    await tb.reset()
    inputs = tb.generate_inputs(random=False)
    dut.a.value = inputs["a"]
    dut.b.value = inputs["b"]
    await cc_triggers.FallingEdge(dut.clk)
    exp_ls_adder = unsigned_extend(inputs["a"], dut.LSWidth.value) + unsigned_extend(
        inputs["b"], dut.LSWidth.value
    )
    exp_cross_carry = exp_ls_adder >> dut.LSWidth.value
    assert signal_uint(dut.gen_register_middle.ls_adder) == exp_ls_adder, check_msg(
        "check_pipeline_register_middle_values"
    )
    assert (
        signal_uint(dut.gen_register_middle.cross_carry) == exp_cross_carry
    ), check_msg("check_pipeline_register_middle_values")
    await cc_triggers.FallingEdge(dut.clk)
    assert signal2int(dut.out) == tb.model(**inputs), check_msg(
        "check_pipeline_register_middle_values"
    )


@cocotb.test()
async def check_pipeline_registers(dut):
    tb = IntAdderTreeNode(dut)

    signal2int = signal_int if tb.SIGN_EXT else signal_uint

    await tb.reset()
    if not tb.REGISTER_OUTPUT:
        return
    inputs_1 = tb.generate_inputs(random=True)
    dut.a.value = inputs_1["a"]
    dut.b.value = inputs_1["b"]
    await cc_triggers.FallingEdge(dut.clk)
    inputs_2 = tb.generate_inputs(random=True)
    dut.a.value = inputs_2["a"]
    dut.b.value = inputs_2["b"]
    if tb.REGISTER_MIDDLE:
        await cc_triggers.FallingEdge(dut.clk)
        assert signal2int(dut.out) == tb.model(**inputs_1), check_msg(
            "check_pipeline_registers"
        )
        await cc_triggers.FallingEdge(dut.clk)
        assert signal2int(dut.out) == tb.model(**inputs_2), check_msg(
            "check_pipeline_registers"
        )
    else:
        assert signal2int(dut.out) == tb.model(**inputs_1), check_msg(
            "check_pipeline_registers"
        )
        await cc_triggers.FallingEdge(dut.clk)
        assert signal2int(dut.out) == tb.model(**inputs_2), check_msg(
            "check_pipeline_registers"
        )


def generate_random_params(sign_ext: bool):
    params = {"IN_BITS": randint(2, 64) if sign_ext else randint(1, 64)}
    return params


def infer_out_bits(in_bits: int):
    return in_bits + 1


def pytest_int_adder_tree_node():
    NUM_RANDOM_TESTS = 5
    param_list = [
        {
            "IN_BITS": 4,
            "OUT_BITS": 5,
            "SIGN_EXT": 0,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
        },
        {
            "IN_BITS": 4,
            "OUT_BITS": 5,
            "SIGN_EXT": 1,
            "REGISTER_MIDDLE": 0,
            "REGISTER_OUTPUT": 0,
        },
        {
            "IN_BITS": 4,
            "OUT_BITS": 6,
            "SIGN_EXT": 0,
            "REGISTER_MIDDLE": 1,
            "REGISTER_OUTPUT": 0,
        },
        {
            "IN_BITS": 4,
            "OUT_BITS": 6,
            "SIGN_EXT": 1,
            "REGISTER_MIDDLE": 1,
            "REGISTER_OUTPUT": 0,
        },
        {
            "IN_BITS": 4,
            "OUT_BITS": 6,
            "SIGN_EXT": 0,
            "REGISTER_MIDDLE": 1,
            "REGISTER_OUTPUT": 1,
        },
        {
            "IN_BITS": 4,
            "OUT_BITS": 6,
            "SIGN_EXT": 1,
            "REGISTER_MIDDLE": 1,
            "REGISTER_OUTPUT": 1,
        },
    ]
    for _ in range(NUM_RANDOM_TESTS):
        random_p_signed = generate_random_params(sign_ext=True)
        random_p_unsigned = generate_random_params(sign_ext=False)

        for sign_ext in [0, 1]:
            for register_middle in [0, 1]:
                for register_output in [0, 1]:
                    if sign_ext:
                        random_p = random_p_signed | {
                            "OUT_BITS": infer_out_bits(random_p_signed["IN_BITS"]),
                            "SIGN_EXT": 1,
                            "REGISTER_MIDDLE": register_middle,
                            "REGISTER_OUTPUT": register_output,
                        }
                    else:
                        random_p = random_p_unsigned | {
                            "OUT_BITS": infer_out_bits(random_p_unsigned["IN_BITS"]),
                            "SIGN_EXT": 0,
                            "REGISTER_MIDDLE": register_middle,
                            "REGISTER_OUTPUT": register_output,
                        }
                    param_list.append(random_p)

    # cocotb 1.8.1 does not support accessing the instance/signal in generate - endgenerate block
    # use icarus verilog instead
    # related PR: https://github.com/cocotb/cocotb/pull/3624
    lqer_runner(param_list)


if __name__ == "__main__":
    pytest_int_adder_tree_node()
