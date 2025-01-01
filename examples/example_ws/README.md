# Example Workspace

This is an example workspace put in place to demonstrate some of the features of the environment.

## vlib Project

The vlib project contains some of the common blocks I generally use, namely:
1. gen_cnt - a generic counter with a configurable limit and increment, decrement and clear controls
2. gen_pipe - a generic delay pipe with a parameterizable amount of delay as well as 2 flavours:
    * Low power option - data is valid dependent
    * Low area option - data is free-running
3. gen_fifo_ctrl - a generic FIFO control with almost-full and almost-empty configurable thresholds
4. gen_reg_mem - register-based memory array with parameterizable delays (to and from the memory) and a bit-enable option

The reader is welcome to go through the directory and use the config syntax and file-system structure as reference.

## APB FIFO

### About
The project example_proj contains one block: apb_fifo. It is a FIFO that offers the user an APB interface for:
1. Configuring the FIFO
2. Writing to the FIFO
3. Reading from the FIFO
4. Checking FIFO statuses

### Environment Features In-Use
The block was written to demonstrate some of the environment features:
1. Utilizing the 'blk' script to create the block structure.
2. Utilizing different blocks:
    1. Uses vlib/design/gen_fifo_ctrl 'rtl' view as the main FIFO's control.
    2. Uses vlib/design/gen_reg_mem 'rtl' view as the main FIFO's storage.
3. Utilizing the 'regen' register-description language to describe the FIFO's register-file
4. Utilizing the 'enst' script to automatically instantiate top-level modules of children in the FIFO's RTL.
5. Utilizing the homemade cocotb APB infrastructure made to easily drive and monitor transactions to simulate the DUT.

### Workflow
Here is a brief description of the workflow I used to create this project:
#### Design
1. Used the 'blk' script to create the skeleton of the block.
2. Edited the [configuration file](./example_project/design/apb_fifo/misc/apb_fifo.cfg) to include the children blocks I would like to use.
3. Wrote the [register-file](./example_project/design/apb_fifo/regs/apb_fifo_rgf.py) in the 'regen' langauge.
4. Used the 'regen' script to append the register-file instance to the [top-level module](./example_project/design/apb_fifo/rtl/apb_fifo_top.v) of the design.
5. Used the 'enst' script to append the gen_fifo_ctrl and gen_reg_mem instances to the design.
6. Some minor top-level integration - connecting the internal wires between the different moduels and the external APB interface to the register-file.
    * Note that this is both where I started and where I finished with the RTL coding of the entire thing (excluding the already coded children)
#### Verification
1. Used the 'regen' script to get a [json file](./example_project/verification/apb_fifo/registers/apb_fifo_rgf.json) describing the register file in a manner that the pre-made APB infrastructure can easily parse.
2. Wrote a [simple, naive test](./example_project/verification/apb_fifo/tests/apb_fifo_tb.py) to demonstrate loading and unloading the FIFO while stopping every once in a while to check the statuses and making sure that the read data matches the expected data (that was previously written).

### Examples 
Some images and code snippets

#### Writing a register for the input and output data
For an input data register we should want 2 things:
1. A register that matches the width of the input data
2. A register that lets the HW know when SW writes to it, this can be used as the FIFO's push signal
Luckily, both of those features are implemented in the SWPulseWRField Class of the 'regen' language:
```python
dat_in_fld = SWPulseWRField('dat_in_fld', 'FIFO\'s input data', width=4) # regen generates a pulse when this is written, the pulse is used by the HW as the FIFO's push signal
```
Similarly, for the output data, we should want a register that can notify the HW when it is read, this can be used as the FIFO's pop signal.
Again, lucky us, this feature is built-in to the 'regen' language:
```python
dat_out_fld = SWPulseRDField('dat_out_fld', 'FIFO\'s output data', width=4) # regen generates a pulse when this is read, the pulse is used by the HW as the FIFO's pop signal
```
All that is left for us to do is aggregate both of those fields to a register:
```python
dat_reg = Register('dat', 'data register', 32, [dat_in_fld, dat_out_fld])
```
And the 'regen' will provide the HW with an interface as follows:
```verilog
   .apb_fifo_rgf_dat_dat_in_fld                (fifo_dat_in     ), // fifo_rgf_dat_dat_in_fld: HW read port , output(4b)
   .apb_fifo_rgf_dat_dat_in_fld_sw_wr_pulse    (fifo_push_c1    ), // fifo_rgf_dat_dat_in_fld: SW wrote this field, pulse, active high , output(1b)
   .apb_fifo_rgf_dat_dat_out_fld_hw_next       (fifo_dat_out    ), // fifo_rgf_dat_dat_out_fld: HW write port , input(4b)
   .apb_fifo_rgf_dat_dat_out_fld_sw_rd_pulse   (fifo_pop        ), // fifo_rgf_dat_dat_out_fld: SW read this field, pulse, active high , output(1b)
```
* Note that the 'apb_fifo_rgf_dat_dat_in_fld_sw_wr_pulse' is used as 'fifo_push_c1' which is an early-by-1-cycle version of 'fifo_push' as the FIFO samples the field in the register file and not the APB's pwdata directly.

#### Instantiating child modules
The 'enst' and 'regen' script make integration easy, fun and orderly. 
Instantiating any of the child blocks was a matter of a simple bash command:
```bash
╰─ enst -son vlib/design/gen_fifo_ctrl -v rtl -dst rtl/apb_fifo_top.v
```
* This parses the configuration file located in the current block (-w, -p, -b flags are inffered by the cwd)
* It takes the view of the block specified in -v, and looks for a child block specified in -son
* Then, it checks what is the view this child should be used as according to the configuration file and appends the top level module of this view to the file specified in -dst
Running this command appended the gen_fifo_ctrl_top module in rtl/apb_fifo_top.v:
```verilog
gen_fifo_ctrl_top #(
   .DEPTH(FIFO_DEPTH)
) i_gen_fifo_ctrl_top (
   // General // 
   .clk       (clk           ), // i, 0:0   X logic  , Clock signal
   .rst_n     (rst_n         ), // i, 0:0   X logic  , Async reset. active low
   // Configurations //
   .cfg_af_th (fifo_af_th    ), // i, PTR_W X logic  , almost-full threshold. anything including and above this value will assert sts_af
   .cfg_ae_th (fifo_ae_th    ), // i, PTR_W X logic  , almost-empty threshold. anything including and below this value will assert sts_ae
   // Input Controls // 
   .clr       (fifo_clr      ), // i, 0:0   X logic  , Clear FIFO. reset all pointers to 0
   .push      (fifo_push     ), // i, 0:0   X logic  , Write enable active high
   .pop       (fifo_pop      ), // i, 0:0   X logic  , Output enable active high
   // Output Controls // 
   .rd_ptr    (fifo_rd_ptr   ), // o, PTR_W X logic  , Read pointer
   .wr_ptr    (fifo_wr_ptr   ), // o, PTR_W X logic  , Write pointer
   // Output Statuses //
   .sts_count (fifo_sts_count), // o, CNT_W X logic  , FIFO count
   .sts_full  (fifo_sts_full ), // o, 0:0   X logic  , FIFO full
   .sts_af    (fifo_sts_af   ), // o, 0:0   X logic  , FIFO almost-full
   .sts_ae    (fifo_sts_ae   ), // o, 0:0   X logic  , FIFO almost-empty
   .sts_empty (fifo_sts_empty), // o, 0:0   X logic  , FIFO empty
   .err_ovfl  (fifo_ovfl     ), // o, 0:0   X logic  , error - overflow detected
   .err_udfl  (fifo_udfl     )  // o, 0:0   X logic  , error - underflow detected
);
```
Similarly, you can use regen to append the register-file instance to your top-level module

#### Verification - interacting with the registerfile
Interaction with the register-file is done by-field-name:
1. Use regen to get a [json file](./example_project/verification/apb_fifo/registers/apb_fifo_rgf.json) that describes the register file
   ```bash
   reg -v rtl -json -o registers
   ```
2. Load the json file into your script
    ```python
    def load_registers_dict(json_path: Path):
    with open(json_path, 'r') as file:
        return json.load(file)
    rgf_dict = load_registers_dict('/home/etay-sela/design/veri_home/example_ws/example_project/verification/apb_fifo/registers/apb_fifo_rgf.json')
    ```
3. Instantiate the APBMasterDriver and APBMonitor, providing the register file description:
   ```python
    apb_drv = APBMasterDriver(dut, 'rgf', dut.clk)
    apb_mon = APBMonitor(dut, 'rgf', dut.clk, rgf_dict, bus_width=32)
   ```
   * This is the place to add callbacks to the APBMonitor using apb_mon.add_callback(some_function). For example, you could use the built-in APBTransaction.print() method to get this result printed out to the terminal:
    ```bash
    ------------------------------------------------------------------------------------------------------------------------
    APB Transaction - Started at 164 ns

    Field:      apb_fifo_rgf_dat_dat_out_fld
    Address:    0x00000014
    Strobe:     0b0010
    Direction:  READ
    Reg Data:   0x00000B00 
    Field Data: 0xB 
    ------------------------------------------------------------------------------------------------------------------------
    ```
4. Easily drive transactions to different fields in the design by name:
    ```python
    # Drive random data
    async def drive_rand_dat(apb_drv: APBMasterDriver, clock):
        
        # randomize the data
        rand_dat = random.randint(0, 15)
        
        # Create an APB transaction by naming the desired field, choosing the Write option and provideing data if write
        trns = APBTransaction('apb_fifo_rgf_dat_dat_in_fld', rgf_dict, data=rand_dat, write=True)
        
        # Supply the created transaction to driver, it will take care of it
        await apb_drv._driver_send(trns)

    # Read data out fields
    async def read_dat(apb_drv: APBMasterDriver, clock):
        
        # Create an APB transaction by naming the desired field, choosing the Write option and provideing data if write
        trns = APBTransaction('apb_fifo_rgf_dat_dat_out_fld', rgf_dict, data=None, write=False)
        
        # Supply the created transaction to driver, it will take care of it
        await apb_drv._driver_send(trns)
        
    ```

    #### Simulation and Waves
    Simulating the design is as simple as:
    ```bash
    sim -v rtl
    ```
    No need to assemble a filelist, translate the regen language to verilog, take care of makefiles and pyrunners for the cocotb test, all of that happens for you on the background. At the end of the simulation you get the a log that shows where the results are:
    
    You could use the --waves flag to open the created .vcd file using GTKWave. However, I traced some of the main functionality using cocotb's built-in wavedrom-signal-tracer. Here are the results:
    ##### APB Write
    [apb_write_transaction_waves](../images/apb_fifo_wr_transaction.png)
    ##### APB Read
    [apb_read_transaction_waves](../images/apb_fifo_rd_transaction.png)

