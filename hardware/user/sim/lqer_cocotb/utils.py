import sys
from os import PathLike
from pathlib import Path
import re
import logging

import numpy as np
import torch
from torch import Tensor
from numpy import ndarray
from cocotb import handle as cc_handle


logger = logging.getLogger(__name__)


class SimTimeScale:
    def __init__(
        self,
        unit: tuple[int, str] = (1, "ns"),
        precision: tuple[int, str] = (1, "ps"),
    ) -> None:
        for time in [unit, precision]:
            assert isinstance(time, tuple) and len(time) == 2
            assert isinstance(time[0], int) and isinstance(time[1], str)
        self._unit = unit
        self._precision = precision

    def __repr__(self) -> str:
        return f"Timescale({self._unit[0]}{self._unit[1]}/{self.precision[0]}{self.precision[1]})"

    def __str__(self) -> str:
        return f"{self._unit[0]}{self._unit[1]}/{self.precision[0]}{self.precision[1]}"

    @property
    def unit(self) -> tuple[int, str]:
        return self._unit

    @property
    def precision(self) -> tuple[int, str]:
        return self._precision

    def load_directive(self, directive: PathLike | str) -> None:
        directive = Path(directive)
        with open(directive, "r") as f:
            lines = f.readlines()
        matched = False
        for line in lines:
            if "`timescale" in line:
                match = re.search(r"`timescale\s+(\d+)(\w+)\s+/\s+(\d+)(\w+)", line)
                if match:
                    self._unit = (int(match.group(1)), match.group(2))
                    self._precision = (int(match.group(3)), match.group(4))
                    matched = True
                    break
        if not matched:
            raise ValueError(f"Invalid timescale directive: {directive}")

        logger.info(f"Loaded timescale directive: {self}")

    @classmethod
    def from_directive(cls, directive: PathLike | str) -> "SimTimeScale":
        timescale = cls()
        timescale.load_directive(directive)
        return timescale


def signed_extend(value: int | ndarray | Tensor, bits: int) -> int | ndarray | Tensor:
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


def unsigned_extend(value: int | ndarray | Tensor, bits: int) -> int | ndarray | Tensor:
    if isinstance(value, Tensor):
        assert value.dtype in [torch.int8, torch.int16, torch.int32, torch.int64]
    elif isinstance(value, ndarray):
        assert value.dtype in [np.int8, np.int16, np.int32, np.int64]
    elif isinstance(value, int):
        pass
    else:
        raise TypeError(f"Unsupported type: {type(value)}")

    mask = (1 << bits) - 1
    extended = value & mask
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


def signal_uint(signal) -> int:
    return signal.value.integer


def signal_int(signal) -> int:
    return signal.value.signed_integer


def signal_binstr(signal) -> str:
    return signal.value.binstr


def array1d_uint(signal) -> list[int]:
    return [x.integer for x in signal.value]


def array1d_int(signal) -> list[int]:
    return [x.signed_integer for x in signal.value]


def array1d_binstr(signal) -> list[str]:
    return [x.binstr for x in signal.value]
