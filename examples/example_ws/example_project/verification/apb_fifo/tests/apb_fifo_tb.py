import json
from pathlib import Path
from collections import deque
import cocotb
from cocotb.wavedrom import trace
from cocotb.clock import Clock
import cocotb.utils
from cocotb_bus.bus import Bus
from cocotb.triggers import RisingEdge, ClockCycles
import random
from regen.apb_infra import *

# Written Values Queue
expected_q = deque(maxlen=8)

# Load Register File Dictionary
def load_registers_dict(json_path: Path):
    with open(json_path, 'r') as file:
        return json.load(file)
rgf_dict = load_registers_dict('/home/etay-sela/design/veri_home/example_ws/example_project/verification/apb_fifo/registers/apb_fifo_rgf.json')

# simple print callback
def print_transaction(transaction: APBTransaction):
    transaction.print()

# scoreboard FIFO's status
def check_sts(transaction: APBTransaction):
    
    # status field names definitions
    status_fields = ['apb_fifo_rgf_sts_sts_full', 'apb_fifo_rgf_sts_sts_af', 'apb_fifo_rgf_sts_sts_ae', 'apb_fifo_rgf_sts_sts_empty', 'apb_fifo_rgf_cnt_sts_count']

    # check expected values for all statuses
    global expected_q
    status_expected_values = [len(expected_q)==8, len(expected_q)>=6, len(expected_q)<=2, len(expected_q)==0, len(expected_q)]
    
    # check if current transaction is a read transaction and of a status field
    if transaction.field_name in status_fields and not transaction.write:
        
        # find the expected value
        expected_val = int(status_expected_values[status_fields.index(transaction.field_name)])

        # compare the expected value to the read value
        read_value = transaction.fld_data
        
        assert expected_val==read_value , f'Error: expected {expected_val} for field {transaction.field_name} but got {read_value}'

# probe data callback
def check_dat(transaction: APBTransaction):
    global expected_q

    # Write FIFO
    if transaction.field_name=='apb_fifo_rgf_dat_dat_in_fld' and transaction.write:
        expected_q.append(transaction)
    
    # Read FIFO 
    elif transaction.field_name=='apb_fifo_rgf_dat_dat_out_fld' and not transaction.write:
        expected_trns = expected_q.popleft()

        assert expected_trns.fld_data==transaction.fld_data, f'Error: expected data {expected_trns.fld_data} but found {transaction.fld_data}'

# Reset DUT coro
async def reset_dut(clock, rst_n, cycles):
    rst_n.value = 0
    for _ in range(cycles):
        await RisingEdge(clock)
    rst_n.value = 1
    rst_n._log.debug("Reset complete")

# Configurations coro
async def cfg_fifo(apb_drv: APBMasterDriver, clock):
    af_th_wr_trns = APBTransaction('apb_fifo_rgf_cfg_cfg_af_th', rgf_dict, 6, True)
    ae_th_wr_trns = APBTransaction('apb_fifo_rgf_cfg_cfg_ae_th', rgf_dict, 2, True)
    await apb_drv._driver_send(af_th_wr_trns)
    await apb_drv._driver_send(ae_th_wr_trns)
    await ClockCycles(clock, 4)

# Drive random data
async def drive_rand_dat(apb_drv: APBMasterDriver, clock):
    rand_dat = random.randint(0, 15)
    dat_in_trns = APBTransaction('apb_fifo_rgf_dat_dat_in_fld', rgf_dict, rand_dat, True)
    await apb_drv._driver_send(dat_in_trns)
    await ClockCycles(clock, 2)

# Read all status registers from the FIFO
async def read_sts(apb_drv: APBMasterDriver, clock):
    
    # wait for all data writes and reads to propagte to the FIFO
    await ClockCycles(clock, 10)

    # status field names definitions
    status_fields = ['apb_fifo_rgf_sts_sts_full', 'apb_fifo_rgf_sts_sts_af', 'apb_fifo_rgf_sts_sts_ae', 'apb_fifo_rgf_sts_sts_empty', 'apb_fifo_rgf_cnt_sts_count']
    
    # post requests to read all status fields
    for fld in status_fields:
        trns = APBTransaction(fld, rgf_dict, None, False)
        await apb_drv._driver_send(trns)
    
    # wait for all requests to be over
    await ClockCycles(clock, 10)

# Read data out fields
async def read_dat(apb_drv: APBMasterDriver, clock):
    field_name = 'apb_fifo_rgf_dat_dat_out_fld'
    trns = APBTransaction(field_name, rgf_dict, None, False)
    await apb_drv._driver_send(trns)
    await ClockCycles(clock, 2)

# Main test
@cocotb.test()
async def basic_test(dut):

    # Start clock
    await cocotb.start(Clock(dut.clk, 1, 'ns').start())

    # Define Driver and Monitor
    apb_drv = APBMasterDriver(dut, 'rgf', dut.clk)
    apb_mon = APBMonitor(dut, 'rgf', dut.clk, rgf_dict, bus_width=32)
    apb_mon.add_callback(print_transaction)
    apb_mon.add_callback(check_sts) # callback to compare between expected statuses and statuses read over APB
    apb_mon.add_callback(check_dat) # callback to compare between expected output data and received data over APB

    # Wait for reset DUT to complete
    await reset_dut(dut.clk, dut.rst_n, 10)

    # Wait for Configuration sequence to complete
    await cfg_fifo(apb_drv, dut.clk) # almost-empty threhosld = 2, almost-full threshold = 6

    # Read statuses
    await read_sts(apb_drv, dut.clk) # Read all statuses

    # Post Random Data
    check_points = [1,5,7]
    for i in range(8):
        await drive_rand_dat(apb_drv, dut.clk) # Drive random input data
        if i in check_points: # in expected status changes:
            await read_sts(apb_drv, dut.clk) # read all statuses
    
    # Read Data
    for i in range(8):
        await read_dat(apb_drv, dut.clk) # Read data from FIFO
        if i in check_points: # in expected status changes:
            await read_sts(apb_drv, dut.clk) # read all statuses

# Example Write 
@cocotb.test()
async def examples(dut):
    # Start clock
    await cocotb.start(Clock(dut.clk, 1, 'ns').start())

    # Define Driver and Monitor
    apb_drv = APBMasterDriver(dut, 'rgf', dut.clk)
    apb_mon = APBMonitor(dut, 'rgf', dut.clk, rgf_dict, bus_width=32)
    apb_mon.add_callback(print_transaction)
    apb_mon.add_callback(check_sts) # callback to compare between expected statuses and statuses read over APB
    apb_mon.add_callback(check_dat) # callback to compare between expected output data and received data over APB

    # Trace signals
    fifo_in_if = Bus(dut, 'fifo', ['push', 'dat_in'])
    fifo_out_if = Bus(dut, 'fifo', ['pop', 'dat_out'])
    with trace(apb_drv.bus, fifo_in_if, dut.fifo_sts_count, clk=dut.clk) as waves:
        await ClockCycles(dut.clk, 1)
        await drive_rand_dat(apb_drv, dut.clk) # Drive random input data
        await ClockCycles(dut.clk, 3)
        j = waves.dumpj()
        
    # Write json content
    with open('write_transaction.json', 'w') as file:
        file.write(j)
    
    with trace(apb_drv.bus, fifo_out_if, dut.fifo_sts_count, clk=dut.clk) as waves:
        await ClockCycles(dut.clk, 1)
        await read_dat(apb_drv, dut.clk) # Drive random input data
        await ClockCycles(dut.clk, 3)
        j = waves.dumpj()
        
    # Write json content
    with open('read_transaction.json', 'w') as file:
        file.write(j)
