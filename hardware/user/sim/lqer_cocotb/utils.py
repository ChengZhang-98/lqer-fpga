import sys

import numpy as np
import torch
from torch import Tensor
from numpy import ndarray
from cocotb import handle as cc_handle


def sign_extend(value: int | ndarray | Tensor, bits: int) -> int | ndarray | Tensor:
    if isinstance(value, Tensor):
        assert value.dtype in [torch.int8, torch.int16, torch.int32, torch.int64]
    elif isinstance(value, ndarray):
        assert value.dtype in [np.int8, np.int16, np.int32, np.int64]
    elif isinstance(value, int):
        pass
    else:
        raise TypeError(f"Unsupported type: {type(value)}")

    sign_bit = 1 << (bits - 1)
    extended = (value & (sign_bit - 1)) - (value & sign_bit)
    return extended


def signed_to_unsigned(value: int | ndarray | Tensor, bits: int) -> int | ndarray | Tensor:
    if isinstance(value, torch.Tensor):
        assert value.dtype in [torch.int8, torch.int16, torch.int32, torch.int64]
    elif isinstance(value, np.ndarray):
        assert value.dtype in [np.int8, np.int16, np.int32, np.int64]
    elif isinstance(value, int):
        pass
    mask = (1 << bits) - 1
    unsigned = value & mask
    return unsigned


def floor_rounding(value, in_frac_width, out_frac_width):
    if in_frac_width > out_frac_width:
        return value >> (in_frac_width - out_frac_width)
    elif in_frac_width < out_frac_width:
        return value << (in_frac_width - out_frac_width)
    return value


# utils for handle signals


def signal_integer(signal: cc_handle.NonHierarchyObject) -> int:
    return signal.value.integer


def signal_signed_integer(signal: cc_handle.NonHierarchyObject) -> int:
    return signal.value.signed_integer


def signal_binary_str(signal: cc_handle.NonHierarchyObject) -> str:
    return signal.value.binstr
