# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: MIT
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge
from cocotb.clock import Clock, Timer
from cocotb.regression import TestFactory

# CS is pin 2
# DS is pin 3
# RW is pin 4

PS2_CLK = 0
PS2_DATA = 1
CS = 2
DS = 3
RW = 4

class BusAccumulator:
    """A class to accumulate values from the bus."""
    def __init__(self, bus, value=0):
        self.value = value
        self.bus = bus

    def set_bit(self, bit):
        """Accumulate a value."""
        self.value = (1 << bit) | self.value

    def clear_bit(self, bit):
        """Clear a value."""
        self.value = ~(1 << bit) & self.value

    def get(self):
        """Get the accumulated value."""
        return self.value
    
    def set_bus(self):
        """Set the accumulated value."""
        self.bus.value = self.value

def read_dtack(dut):
    """Read the DTACK signal from the device."""
    return dut.uo_out.value & 1

async def wait_int(dut):
    """Read the Interrupt signal from the device."""
    
    while not dut.uo_out.value & 2:
        await Edge(dut.uo_out)


async def setup_test(dut):
    """Common setup for each test: resetting the device and starting the clock."""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())  # Start a 10us period clock

    b = BusAccumulator(dut.ui_in)
    b.set_bit(PS2_CLK)
    b.set_bit(PS2_DATA)
    b.set_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    b.set_bus()

    # Reset the device
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)  # Wait for a clock edge
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)  # Wait for another clock edge to ensure clear reset
    await RisingEdge(dut.clk)  # Wait for another clock edge to ensure clear reset


async def read_reg(dut):
    """Read the BusDevice register."""
    await RisingEdge(dut.clk) # S0
    b = BusAccumulator(dut.ui_in)
    b.set_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    b.set_bus()

    await RisingEdge(dut.clk) # S2 

    b.clear_bit(CS)
    b.clear_bit(DS)
    b.set_bus()

    await RisingEdge(dut.clk) # S4
    await FallingEdge(dut.clk) # S5
    
    if hasattr(dut.user_project, 'dtack'):
        assert dut.user_project.dtack.value == 0, "Inernal DTACK not low"
    assert read_dtack(dut) == 0, f"DTACK should be low. {dut.uo_out.value}"
    
    #while read_dtack(dut):
    #    await FallingEdge(dut.clk) # Wait Cycle

    await FallingEdge(dut.clk) # S7

    b.set_bit(CS)
    b.set_bit(DS)
    b.set_bus()

    assert dut.uio_oe.value == 0xFF, f"OE should be high. {dut.uo_out.value}"

    result = dut.uio_out.value

    await RisingEdge(dut.clk) # S0' 

    await FallingEdge(dut.clk) # S1'

    assert read_dtack(dut) == 1, f"DTACK should return high. {dut.uo_out.value}"

    return result


async def write_reg(dut, value):
    print(f"Write reg {value}, {dut.uo_out.value}")
    assert read_dtack(dut) == 1, f"DTACK should be high. {dut.uo_out.value}"

    await RisingEdge(dut.clk) # S0 
    # clear state from any previous test
    b = BusAccumulator(dut.ui_in)
    b.set_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    b.set_bus()

    await RisingEdge(dut.clk) # S2

    # Set up write operation
    b.clear_bit(RW)
    b.clear_bit(CS)
    b.set_bus()

    await FallingEdge(dut.clk) # S3
    dut.uio_in.value = 0x55  # Example data to write

    await RisingEdge(dut.clk) # S4

    b.clear_bit(DS)
    b.set_bus()

    await FallingEdge(dut.clk) # S5 check DTACK went low, otherwise wait state would be added

    assert read_dtack(dut) == 0, f"DTACK should be low. {dut.uo_out.value}"

    await RisingEdge(dut.clk) # S6

    await FallingEdge(dut.clk) # S7 clean up CS, DS and RW

    b.set_bit(RW)
    b.set_bit(CS)
    b.set_bit(DS)
    b.set_bus()

    await FallingEdge(dut.clk) # S1' check dtack is cleared

    assert read_dtack(dut) == 1, f"DTACK should be high after write. {dut.uo_out.value}"


@cocotb.test()
async def write_test(dut):
    """Test writing to the BusDevice register."""
    await setup_test(dut)

    await write_reg(dut, 0x55)

    # Check if data_rdy is asserted and the output matches the input
    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.bus.data_rdy.value == 1, "Data ready should be asserted."
        assert dut.user_project.bus.write_reg.value == 0x55, "Data written to the register does not match the input."


@cocotb.test()
async def read_test(dut):
    """Test reading from the BusDevice register."""
    await setup_test(dut)

    # Pre-load the register with a value to read
    if hasattr(dut.user_project, 'ps2_data_bus'):
        dut.user_project.ps2_data_bus.value = 0xAA  # Preload register

        res = await read_reg(dut)

        # Check if the read value is correctly driven onto the bus
        assert res == 0xAA, "The read value does not match the expected."


async def send_bit(bus, bit):
    """Send a single bit over PS2. Clock is controlled manually."""
    if bit:
        bus.set_bit(PS2_DATA)
    else:
        bus.clear_bit(PS2_DATA)
    bus.clear_bit(PS2_CLK)
    bus.set_bus()

    await Timer(10, units='us')  # Low time
    
    bus.set_bit(PS2_CLK)
    bus.set_bus()

    await Timer(10, units='us')  # High time

async def send_ps2_byte(dut, bus, byte):
    """Send a byte over PS2, including start, parity, and stop bits."""

    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.decoder.state.value == 0, f"Expected state 0, got {dut.user_project.decoder.state.value}"

    # Start bit (0)
    await send_bit(bus, 0)

    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.decoder.state.value == 2, f"Expected state 2, got {dut.user_project.decoder.state.value}"

    # Data bits (LSB first)
    parity = 0
    for i in range(8):
        bit = (byte >> i) & 1
        await send_bit(bus, bit)
        parity ^= bit  # Compute parity (odd)

        if hasattr(dut.user_project, 'ps2_data_bus'):
            if i == 7:
                assert dut.user_project.decoder.state.value == 3, f"Expected state 3, got {dut.user_project.decoder.state.value}"
            else:
                assert dut.user_project.decoder.state.value == 2, f"Expected state 2 on bit {i}, got {dut.user_project.decoder.state.value}"

    # Parity bit (odd parity)
    await send_bit(bus, parity)

    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.decoder.state.value == 4, f"Expected state 4, got {dut.user_project.decoder.state.value}"

    # Stop bit (1)
    await send_bit(bus, 1)

    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.decoder.state.value == 0, f"Expected state 0, got {dut.user_project.decoder.state.value}"

@cocotb.test()
async def ps2_test(dut):
    """Test reading from the BusDevice register."""
    await setup_test(dut)

    bus = BusAccumulator(dut.ui_in)
    bus.set_bit(PS2_CLK)
    bus.set_bit(PS2_DATA)
    bus.set_bus()

    await Timer(1, units='ms')  # Wait a bit before starting

    test_byte = 0x78

    # Send a byte, for example 0x55
    await send_ps2_byte(dut, bus, test_byte)

    if hasattr(dut.user_project, 'ps2_data_bus'):
        assert dut.user_project.ps2_data_bus.value == test_byte, f"Expected {test_byte}, got {dut.user_project.ps2_data_bus.value}"

    # Wait for the interrupt signal to be asserted
    await wait_int(dut)

    # Read the value from the register
    value = await read_reg(dut)

    print(f"Read value: {value}")

    assert value == test_byte, f"Expected {test_byte}, got {value}"


# Create a test factory to handle running both the write and read tests
#test_factory = TestFactory(test_function=write_test)
#test_factory.add_option("test_function", [write_test, read_test])
#test_factory.generate_tests()
