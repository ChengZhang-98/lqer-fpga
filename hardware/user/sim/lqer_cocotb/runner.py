from os import getenv
from pathlib import Path
import shutil
import re
import logging
import inspect
from typing import Any
import torch
import toml

from cocotb.runner import get_runner, get_results


logger = logging.getLogger(__name__)


LQER_COMPONENT_DIR = Path(__file__).parents[2] / "components"
LQER_COMPONENT_DEPENDENCY_TOML = LQER_COMPONENT_DIR / "dependency_registry.toml"
assert LQER_COMPONENT_DIR.exists(), f"Invalid component directory: {LQER_COMPONENT_DIR}"
assert (
    LQER_COMPONENT_DEPENDENCY_TOML.exists()
), f"Invalid dependency registry: {LQER_COMPONENT_DEPENDENCY_TOML}"
with open(LQER_COMPONENT_DEPENDENCY_TOML, "r") as f:
    LQER_COMPONENT_DEPENDENCY = toml.load(f)


def lqer_runner(
    module_param_list: list[dict[str, int]] = [dict()],
    extra_build_args: list[str] = [],
    trace: bool = False,
    seed: int = None,
    build_jobs: int = 8,
):
    assert isinstance(module_param_list, list)

    tb_py = inspect.stack()[1].filename
    matches = re.search(r"components/(\w+)/test/(\w+)_tb.py", tb_py)
    assert matches, f"Invalid testbench path: {tb_py}"
    group, module = matches.groups()

    group_path = LQER_COMPONENT_DIR / group
    module_path = group_path / "rtl" / f"{module}.sv"
    testbench_path = group_path / "test" / f"{module}_tb.py"
    build_dir = group_path / "test" / "build" / module

    # example:
    #   module:           int_multiply
    #   group_path:       /workspace/lqer-fpga/hardware/user/components/int
    #   module_path:   /workspace/lqer-fpga/hardware/user/components/int/rtl/int_multiply.sv
    #   testbench_path:   /workspace/lqer-fpga/hardware/user/components/int/test/int_multiply_tb.py
    #   build_dir:        /workspace/lqer-fpga/hardware/user/components/int/test/build/int_multiply

    assert group_path.exists(), f"Invalid group path: {group_path}"
    assert module_path.exists(), f"Invalid component path: {module_path}"
    assert testbench_path.exists(), f"Invalid testbench path: {testbench_path}"
    if build_dir.exists():
        shutil.rmtree(build_dir)

    dependencies = LQER_COMPONENT_DEPENDENCY[f"{group}/{module}"]
    includes = [LQER_COMPONENT_DIR / dep / "rtl" for dep in dependencies]

    # Set and run the simulator
    simulator_name = getenv("SIM", "verilator")
    total_tests = 0
    total_fails = 0

    for i, module_params in enumerate(module_param_list):
        logger.info("========================================")
        logger.info(f"Running test {i+1}/{len(module_param_list)}")
        logger.info("========================================")

        test_build_dir = build_dir / f"test_{i}"

        runner = get_runner(simulator_name)
        runner.build(
            verilog_sources=[module_path],
            includes=includes,
            hdl_toplevel=module,
            build_args=[
                # Verilator linter is overly strict.
                # Too many errors
                # These errors are in later versions of verilator
                # "-Wno-GENUNNAMED",
                # "-Wno-WIDTHEXPAND",
                # "-Wno-WIDTHTRUNC",
                # "-Wno-PINCONNECTEMPTY",
                # Simulation Optimisation
                "-Wno-UNOPTFLAT",
                "-prof-c",
                "--stats",
                # Signal trace in dump.fst
                *(["--trace-fst", "--trace-structs"] if trace else []),
                "--trace",
                # "-trace-depth",
                "-O0",
                "-build-jobs",
                f"{build_jobs}",
                "-Wno-fatal",
                "-Wno-lint",
                "-Wno-style",
                *extra_build_args,
            ],
            parameters=module_params,
            build_dir=test_build_dir,
        )

        runner.test(
            hdl_toplevel=module,
            test_module=testbench_path.stem,
            seed=seed,
            results_xml=f"results.xml",
        )
        num_tests, num_fails = get_results(test_build_dir / "results.xml")
        total_tests += num_tests
        total_fails += num_fails

    logger.info("Test Summary")
    logger.info(f"    PASSED / TOTAL: {total_tests - total_fails} / {total_tests}")
    if total_fails > 0:
        logger.warning(f"    FAILED / TOTAL: {total_fails} / {total_tests}")
    else:
        logger.info(f"    FAILED / TOTAL: {total_fails} / {total_tests}")

    return total_fails
