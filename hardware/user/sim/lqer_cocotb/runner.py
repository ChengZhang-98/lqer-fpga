from os import getenv
from pathlib import Path
import shutil
import re
import logging
import inspect
import toml

from cocotb.runner import get_runner, get_results
from .utils import SimTimeScale

logger = logging.getLogger(__name__)


LQER_COMPONENT_DIR = Path(__file__).parents[2].joinpath("components").resolve()
LQER_COMPONENT_DEPENDENCY_TOML = LQER_COMPONENT_DIR.joinpath(
    "dependency_registry.toml"
).resolve()
LQER_COMPONENT_INCLUDES = LQER_COMPONENT_DIR.joinpath("includes").resolve()
assert LQER_COMPONENT_DIR.exists(), f"Invalid component directory: {LQER_COMPONENT_DIR}"
assert (
    LQER_COMPONENT_DEPENDENCY_TOML.exists()
), f"Invalid dependency registry: {LQER_COMPONENT_DEPENDENCY_TOML}"
assert (
    LQER_COMPONENT_INCLUDES.exists()
), f"Invalid includes directory: {LQER_COMPONENT_INCLUDES}"

with open(LQER_COMPONENT_DEPENDENCY_TOML, "r") as f:
    LQER_COMPONENT_DEPENDENCY = toml.load(f)


def solve_dependency(entry: str) -> list[str]:
    """
    recursively solve the dependency of the entry by looking up LQER_COMPONENT_DEPENDENCY
    """

    def _solve_dependency(entry: str, visited: set[str]) -> list[str]:
        visited.add(entry)
        dependencies = LQER_COMPONENT_DEPENDENCY[entry]
        for dep in dependencies:
            _solve_dependency(dep, visited)
        return list(visited)

    entries = _solve_dependency(entry, set())
    entries = [Path(LQER_COMPONENT_DIR).joinpath(Path(entry)) for entry in entries]
    for entry in entries:
        assert entry.exists(), f"Invalid component path: {entry}"
    entries = [entry.as_posix() for entry in entries]
    return entries


def lqer_runner(
    module_param_list: list[dict[str, int]] = [dict()],
    extra_build_args: list[str] = [],
    waves: bool = True,
    seed: int = 42,
    simulator: str = "questa",
):
    assert isinstance(module_param_list, list)

    testbench_py = Path(inspect.stack()[1].filename).resolve()  # path to <module>_tb.py
    # print([x.filename for x in inspect.stack()])

    module_name = testbench_py.stem.removesuffix("_tb")
    dut_sv = (
        testbench_py.parents[1] / "rtl" / f"{testbench_py.stem.removesuffix('_tb')}.sv"
    )  # path to <module>.sv
    assert dut_sv.exists(), f"Failed to find DUT at {dut_sv}"
    dut_entry = dut_sv.as_posix().removeprefix(LQER_COMPONENT_DIR.as_posix() + "/")
    sv_sources = solve_dependency(dut_entry)
    build_dir = testbench_py.parents[0] / "build" / module_name

    if build_dir.exists():
        shutil.rmtree(build_dir)

    includes = [LQER_COMPONENT_INCLUDES]

    # Set and run the simulator

    match simulator:
        case "verilator":
            build_args = [
                # Simulation Optimisation
                "-prof-c",
                "--stats",
                "--trace",
                # "--trace-fst", # vscode extension does not support fst
                "--trace-structs",
                "-O0",
                # "-Wno-fatal",
                # "-Wno-lint",
                # "-Wno-style",
                # "--timescale-override",
                # str(default_sim_timescale),  # depends on cocotb version
                *extra_build_args,
            ]
            test_args = []
        case "icarus":
            build_args = [
                # Simulation Optimisation
                "-s",
                module_name,
                *extra_build_args,
            ]
            test_args = []
        case "questa":
            build_args = [
                *extra_build_args,
            ]
            test_args = []
        case _:
            raise ValueError(f"Invalid simulator: {simulator}")

    total_tests = 0
    total_fails = 0

    for i, module_params in enumerate(module_param_list):
        logger.info("========================================")
        logger.info(f"Running test {i+1}/{len(module_param_list)}")
        logger.info("========================================")

        test_build_dir = build_dir / f"test_{i}"
        runner = get_runner(simulator)
        runner.build(
            verilog_sources=sv_sources,
            includes=includes,
            hdl_toplevel=module_name,
            build_args=build_args,
            parameters=module_params,
            build_dir=test_build_dir,
        )

        results_xml = runner.test(
            test_module=testbench_py.stem,
            hdl_toplevel=module_name,
            seed=seed,
            results_xml=f"results.xml",
            waves=waves,
            test_args=test_args,
        )
        num_tests, num_fails = get_results(results_xml)
        total_tests += num_tests
        total_fails += num_fails

    logger.info("Test Summary")
    logger.info(f"    PASSED / TOTAL: {total_tests - total_fails} / {total_tests}")
    if total_fails > 0:
        logger.error(f"    FAILED / TOTAL: {total_fails} / {total_tests}")
    else:
        logger.info(f"    FAILED / TOTAL: {total_fails} / {total_tests}")

    return total_fails
