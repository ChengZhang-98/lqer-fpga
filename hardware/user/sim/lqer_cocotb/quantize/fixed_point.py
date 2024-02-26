from .utils import clamp, round
import numpy as np
import torch


def quantize_to_fixed_point(
    x: int | float | np.ndarray | torch.Tensor,
    width: int,
    frac_width: int,
    is_signed: bool = True,
    rounding="truncate",
):
    """
    Args:

    rounding:
        - "round": Round to the nearest integer.
        - "floor": Round towards negative infinity.
        - "ceil": Round towards positive infinity.
        - "trunc": Round towards zero.
    """
    if is_signed:
        max_val = 2 ** (width - 1) - 1
        min_val = -(2 ** (width - 1))
    else:
        max_val = 2**width - 1
        min_val = 0

    x = round(x * 2**frac_width, rounding=rounding)
    x = clamp(x, min_val, max_val)
    return x
