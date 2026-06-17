import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer, with_timeout


@cocotb.test()
async def test_pwm_generator_behavior(dut):
    """Test PWM generator behavior and ensure GL simulation cannot hang."""

    # Start clock
    clock = Clock(dut.clk, 20, unit="ns")
    cocotb.start_soon(clock.start())

    # Initialize inputs
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    if hasattr(dut, "ena"):
        dut.ena.value = 1

    # Allow reset values to settle
    await Timer(100, unit="ns")

    # Release reset
    await with_timeout(
        FallingEdge(dut.clk),
        1,
        "us"
    )

    dut.rst_n.value = 1

    await with_timeout(
        ClockCycles(dut.clk, 5),
        1,
        "us"
    )

    # ------------------------------------------------------------------
    # Test 1: Normal PWM operation
    # ------------------------------------------------------------------

    enable = 1
    raw_period = 8
    invert = 0

    ui_val = (invert << 5) | (raw_period << 1) | enable

    raw_duty = 4
    uio_val = raw_duty

    await with_timeout(
        FallingEdge(dut.clk),
        1,
        "us"
    )

    dut.ui_in.value = ui_val
    dut.uio_in.value = uio_val

    await with_timeout(
        ClockCycles(dut.clk, 20),
        5,
        "us"
    )

    # Basic sanity checks
    assert dut.uo_out.value.is_resolvable, "uo_out contains X/Z values"

    # ------------------------------------------------------------------
    # Test 2: Period clamp behavior
    # ------------------------------------------------------------------

    unsafe_period = 1

    ui_val_clamp = (invert << 5) | (unsafe_period << 1) | enable

    await with_timeout(
        FallingEdge(dut.clk),
        1,
        "us"
    )

    dut.ui_in.value = ui_val_clamp

    await with_timeout(
        ClockCycles(dut.clk, 10),
        5,
        "us"
    )

    assert dut.uo_out.value.is_resolvable, \
        "uo_out contains X/Z after clamp test"

    # ------------------------------------------------------------------
    # Test 3: Disable PWM
    # ------------------------------------------------------------------

    enable = 0
    ui_val_disable = (invert << 5) | (raw_period << 1) | enable

    await with_timeout(
        FallingEdge(dut.clk),
        1,
        "us"
    )

    dut.ui_in.value = ui_val_disable

    await with_timeout(
        ClockCycles(dut.clk, 10),
        5,
        "us"
    )

    assert dut.uo_out.value.is_resolvable, \
        "uo_out contains X/Z after disable test"

    dut._log.info("PWM gate-level test completed successfully")
