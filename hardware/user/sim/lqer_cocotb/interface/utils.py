from cocotb.binary import BinaryValue


def binary_value_to_integer(bin_val: BinaryValue) -> int:
    return bin_val.integer


def binary_value_to_signed_integer(bin_val: BinaryValue) -> int:
    return bin_val.signed_integer


def binary_value_to_binstr(bin_val: BinaryValue) -> str:
    return bin_val.binstr
