# MASE BUGS

Possible bugs in MASE SystemVerilog components.

-  `fixed_point_multi.sv`: input signed?

Possible bugs in MASE Cocotb:

- `StreamingMonitor`: does not handle signed value. (`/workspace/machop/mase_cocotb/interfaces/streaming.py`)
- `StreamingDriver`: change input signal value even if the valid signal is low. (`/workspace/machop/mase_cocotb/interfaces/streaming.py`)