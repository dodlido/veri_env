import cocotb
from cocotb.triggers import FallingEdge, Timer, RisingEdge
from cocotb.clock import Clock

@cocotb.test()
async def my_test(dut):
   cocotb.start_soon(Clock(dut.clk, 1, units="ns").start())
   for _ in range(10):
      await RisingEdge(dut.clk)