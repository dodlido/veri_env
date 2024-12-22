import cocotb
from cocotb.triggers import FallingEdge, Timer, RisingEdge
from cocotb.clock import Clock
import os
import random
import sys
from pathlib import Path
import math
from typing import Tuple

# Parameters
iterations = 2 ** 8 
dat_out_w = 8 
dat_in_w = 32
last_vld_sel_stop = int(dat_in_w / dat_out_w - 1)
us_dat_stop = int(2 ** dat_in_w - 1)

# Import model
if cocotb.simulator.is_running():
    from models.al_w2n_model import al_w2n_model

# Reset coroutine
async def reset_dut(rst_n, clk, cycles):
    rst_n.value = 0
    for _ in range(cycles):
        await RisingEdge(clk)
    rst_n.value = 1
    rst_n._log.debug("Reset complete")

# Inittialize inputs
async def init_dut(dut):
    dut.us_vld.value, dut.us_last_vld_sel.value, dut.us_dat.value = 0, 0, random.randint(0,us_dat_stop)
    dut.ds_rdy.value = 0 

# Drive uptream inputs coroutine
async def drive_us(dut, rnd_vld_sel: bool=False):
    vld = bool(random.randint(0,1))
    if rnd_vld_sel:
        last_vld_sel = random.randint(0, last_vld_sel_stop) if dut.us_rd_rqst.value else dut.us_last_vld_sel.value
    else:
        last_vld_sel = last_vld_sel_stop
    dat = random.randint(0, us_dat_stop) if dut.us_rd_rqst.value else dut.us_dat.value
    dut.us_vld.value, dut.us_last_vld_sel.value, dut.us_dat.value = vld, last_vld_sel, dat 

# Drive downstream coroutine 
async def drive_ds(dut):
    rdy = bool(random.randint(0,1))
    dut.ds_rdy.value = rdy 

@cocotb.test()
async def my_test(dut):

    model_curr_sel = 0 # initialize internal variable for model
    # Start clock and reset testbench
    cocotb.start_soon(Clock(dut.clk, 1, units="ns").start())
    cocotb.start_soon(init_dut(dut))
    await reset_dut(dut.rst_n, dut.clk, 2)

    #
    for _ in range(iterations):
        
        # Drive Inputs
        cocotb.start_soon(drive_us(dut))
        cocotb.start_soon(drive_ds(dut))

        # Get Expected Outputs
        exp_us_rd_rqst, exp_ds_vld, exp_ds_dat, model_curr_sel = al_w2n_model(dut.us_vld.value, dut.us_last_vld_sel.value, dut.ds_rdy.value, dut.us_dat.value, model_curr_sel, dat_out_w)

        # Assertions
        assert dut.us_rd_rqst.value == exp_us_rd_rqst, f'found mismatch in upstream read request:\n\tEXP: {exp_us_rd_rqst}\n\tACT: {dut.us_rd_rqst.value}'
        assert dut.ds_vld.value == exp_ds_vld, f'found mismatch in downstream valid indicator:\n\tEXP: {exp_ds_vld}\n\tACT: {dut.ds_vld.value}'
        assert dut.ds_dat.value == exp_ds_dat, f'found mismatch in downstream data:\n\tEXP: {exp_ds_dat}\n\tACT: {dut.ds_dat.value}'

        await RisingEdge(dut.clk)
