import cocotb
from cocotb.triggers import FallingEdge, Timer, RisingEdge
from cocotb.clock import Clock
import random
import sys
import cocotb
from cocotb.clock import Clock
import cocotb.regression
import cocotb.utils
from cocotb.triggers import RisingEdge
import logging
from cocotb.log import SimTimeContextFilter, SimColourLogFormatter, SimLogFormatter

strm_hdlr = logging.StreamHandler(sys.stdout)
strm_hdlr.addFilter(SimTimeContextFilter())
strm_hdlr.setFormatter(SimColourLogFormatter())
file_hdlr = logging.FileHandler('run.log')
file_hdlr.addFilter(SimTimeContextFilter())
file_hdlr.setFormatter(SimLogFormatter())
cocotb.logging.getLogger().handlers = [strm_hdlr, file_hdlr]

work_dir = "{WORK_DIR}"
iterations = int({ITERATIONS})

# Port list reading
def get_ports_lists():
    clk_list, rst_list, input_list, output_list, panic_list = [], [], [], [], []
    with open(work_dir + '/port_description/clks.txt', 'r') as file:
        for name in file:
            clk_list.append(name.rstrip('\n'))
    with open(work_dir + '/port_description/resets.txt', 'r') as file:
        for name in file:
            rst_list.append(name.rstrip('\n'))
    with open(work_dir + '/port_description/inputs.txt', 'r') as file:
        for name in file:
            input_list.append(name.rstrip('\n'))
    with open(work_dir + '/port_description/outputs.txt', 'r') as file:
        for name in file:
            output_list.append(name.rstrip('\n'))
    with open(work_dir + '/port_description/panics.txt', 'r') as file:
        for name in file:
            panic_list.append(name.rstrip('\n'))
    return clk_list, rst_list, input_list, output_list, panic_list

# Reset coroutine
async def reset_dut(dut, rst_list, clk):
    for rst in rst_list:
        # signal = getattr(dut, '\'' + rst + '\'')
        # signal <= 0 
        dut._id(rst, extended=False).value = 0 
    for _ in range(10):
        await RisingEdge(dut._id(clk, extended=False))
    for rst in rst_list:
        # signal = getattr(dut, rst)
        # signal <= 1
        dut._id(rst, extended=False).value = 1 
        dut._id(rst, extended=False)._log.debug('Reset complete')

# Initialize Clocks
async def drive_clocks(dut, clk_list):
    for clk in clk_list:
        cocotb.start_soon(Clock(dut._id(clk, extended=False), 1, units="ns").start())

# Initialize inputs
async def drive_inputs(dut, input_list, init=False):
    for _input in input_list:
        signal = dut._id(_input, extended=False)
        if not init:
            signal_width = len(signal)
            signal_max_val = 2 ** signal_width - 1
            dut._id(_input, extended=False).value = random.randint(0, signal_max_val) 
        else:
            dut._id(_input, extended=False).value = 0 

# Assert panics
async def assert_panics(dut, panic_list):
    for panic in panic_list:
        assert dut._id(panic, extended=False), f'Found panic signal named {panic} asserted high'

@cocotb.test()
async def my_test(dut):

    # 0. Read port lists
    clk_list, rst_list, input_list, output_list, panic_list = get_ports_lists()

    # 1. Initialize Clocks and Reset DUT:
    if clk_list:
        cocotb.start_soon(drive_clocks(dut, clk_list))
        cocotb.start_soon(drive_inputs(dut, input_list, True))
        await reset_dut(dut, rst_list, clk_list[0])

        # 2. Main Loop:
        for _ in range(iterations):
        
            # 2.1 Drive Inputs
            cocotb.start_soon(drive_inputs(dut, input_list, False))

            # 2.2 Assert Panics
            cocotb.start_soon(assert_panics(dut, panic_list))

            # 2.3 Wait
            await RisingEdge(dut._id(clk_list[0], extended=False))

