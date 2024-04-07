# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.clock import Clock
from cocotb.regression import TestFactory

# CS is pin 2
# DS is pin 3
# RW is pin 4

CS = 2
DS = 3
RW = 4

class BusAccumulator:
    """A class to accumulate values from the bus."""
    def __init__(self, value=0):
        self.value = value

    def set_bit(self, bit):
        """Accumulate a value."""
        self.value = (1 << bit) | self.value

    def clear_bit(self, bit):
        """Clear a value."""
        self.value = ~(1 << bit) & self.value

    def get(self):
        """Get the accumulated value."""
        return self.value

def read_dtack(dut):
    """Read the DTACK signal from the device."""
    return dut.uo_out.value & 0x01

async def setup_test(dut):
    """Common setup for each test: resetting the device and starting the clock."""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())  # Start a 10us period clock

    dut.ui_in.value = 0  # Set all inputs low

    # Reset the device
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)  # Wait for a clock edge
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)  # Wait for another clock edge to ensure clear reset

@cocotb.test()
async def write_test(dut):
    """Test writing to the BusDevice register."""
    await setup_test(dut)

    assert read_dtack(dut) == 1, f"DTACK should be high. {dut.uo_out.value}"

    # Set up write operation
    b = BusAccumulator()
    b.clear_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    dut.ui_in.value = b.get()  # Set the control signals
    dut.uio_in.value = 0x55  # Example data to write

    await RisingEdge(dut.clk)

    assert dut.ui_in.value == 0x0c, f"CS and DS should start high. got {dut.ui_in.value}"
    assert dut.uio_in.value == 0x55, f"data bus not setup. got {dut.uio_in.value}"

    # Perform the write operation
    await RisingEdge(dut.clk)

    assert read_dtack(dut) == 0, f"DTACK should be low. {dut.uo_out.value}"

    # Check if data_rdy is asserted and the output matches the input
    assert dut.user_project.bus.data_rdy.value == 1, "Data ready should be asserted."
    assert dut.user_project.bus.write_reg.value == 0x55, "Data written to the register does not match the input."

    b.clear_bit(CS)
    b.clear_bit(DS)
    dut.ui_in.value = b.get()  # Set the control signals
    await RisingEdge(dut.clk)


@cocotb.test()
async def read_test(dut):
    """Test reading from the BusDevice register."""
    await setup_test(dut)

    # Pre-load the register with a value to read
    dut.user_project.ps2_data_bus.value = 0xAA  # Preload register
    await RisingEdge(dut.clk)

    b = BusAccumulator()
    b.set_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    dut.ui_in.value = b.get()  # Set the control signals

    # Perform the read operation
    await RisingEdge(dut.clk)

    b.clear_bit(CS)
    b.clear_bit(DS)
    dut.ui_in.value = b.get()  # Set the control signals

    await RisingEdge(dut.clk)

    # Check if the read value is correctly driven onto the bus
    assert dut.uio_out.value == 0xAA, "The read value does not match the expected."

# Create a test factory to handle running both the write and read tests
#test_factory = TestFactory(test_function=write_test)
#test_factory.add_option("test_function", [write_test, read_test])
#test_factory.generate_tests()
