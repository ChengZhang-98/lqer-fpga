from .utils import lqer_clamp, lqer_round, lqer_cast_to_int
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
        - "round" | "nearest": Round to the nearest integer.
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

    x = lqer_round(x * 2**frac_width, rounding=rounding)
    x = lqer_clamp(x, min_val, max_val)
    x = lqer_cast_to_int(x)
    return x
