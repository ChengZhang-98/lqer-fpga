import math
import torch
import numpy as np


def lqer_clamp(
    value: int | float | np.ndarray | torch.Tensor,
    min_value: int | float,
    max_value: int | float,
) -> int | float | np.ndarray | torch.Tensor:
    """
    Clamp a value within a range.

    Args:
        value: The value to be clamped.
        min_value: The minimum value of the range.
        max_value: The maximum value of the range.

    Returns:
        The clamped value.
    """
    if isinstance(value, (int, float)):
        return max(min(value, max_value), min_value)
    elif isinstance(value, np.ndarray):
        return np.clip(value, min_value, max_value)
    elif isinstance(value, torch.Tensor):
        return torch.clamp(value, min_value, max_value)
    else:
        raise TypeError(f"Unsupported type: {type(value)}")


def lqer_round(
    value: int | float | np.ndarray | torch.Tensor,
    rounding: str = "round",
) -> int | float | np.ndarray | torch.Tensor:
    """
    Round a value to the nearest integer.

    ---
    Args:

    value: The value to be rounded.
    rounding: The rounding method. It can be one of the following:

        - "round" | "nearest": Round to the nearest integer.
        - "floor": Round towards negative infinity.
        - "ceil": Round towards positive infinity.
        - "trunc": Round towards zero.

    Returns:
        The rounded value.
    """
    if rounding in ["round", "nearest"]:
        if isinstance(value, (int, float)):
            return int(value + math.copysign(0.5, value))
        elif isinstance(value, np.ndarray):
            return np.round(value)
        elif isinstance(value, torch.Tensor):
            return torch.round(value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
    elif rounding == "floor":
        if isinstance(value, (int, float)):
            return math.floor(value)
        elif isinstance(value, np.ndarray):
            return np.floor(value)
        elif isinstance(value, torch.Tensor):
            return torch.floor(value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
    elif rounding == "ceil":
        if isinstance(value, (int, float)):
            return math.ceil(value)
        elif isinstance(value, np.ndarray):
            return np.ceil(value)
        elif isinstance(value, torch.Tensor):
            return torch.ceil(value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
    elif rounding == "trunc":
        if isinstance(value, (int, float)):
            return math.trunc(value)
        elif isinstance(value, np.ndarray):
            return np.trunc(value)
        elif isinstance(value, torch.Tensor):
            return torch.trunc(value)
        else:
            raise TypeError(f"Unsupported type: {type(value)}")
    else:
        raise ValueError(f"Unsupported rounding method: {rounding}")


def lqer_cast_to_int(x: int | float | np.ndarray | torch.Tensor):
    if isinstance(x, int):
        return x
    elif isinstance(x, float):
        return round(x)
    elif isinstance(x, np.ndarray):
        return x.astype(int)
    elif isinstance(x, torch.Tensor):
        return x.int()
    else:
        raise TypeError(f"Unsupported type: {type(x)}")
