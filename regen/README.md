# Regen - register description language

## About 
The regen language is designed to be an easy and robust way for the designer to describe registers.
The goal is to achieve a single 'ground-truth' register description for each block that is easy to export to any desired format and easy to interface with for both SW and HW teams.

## Features
1. Register files are described in a python code.
2. verilog, html, json files are all generated automatically from the python code. Use the ['reg' script](../regen.py) to get any of the described outputs.
3. The verilog file is not needed for simulation, the translation process happens on the fly and appended to your filelist during the compilation process.
4. The verilog file contains:
   1. A register file, with all the described registers
   2. An APB slave
   3. An APB IF for the SW to write register values to
   4. HW IF containg all the relevant ports for the HW to interact with
5. Integrating an instance of the register file to the design is automatic.
6. Infrastructure to write and read registers over APB, refering to different fields by name without having to handle addresses and strobes:
   1. APB Transaction - base transaction class that translates a field name to an APB transaction in terms of addres and strobe.
   2. APB Driver - drives different transactions
   3. APB Monitor - monitors an APB bus for valid transactions
7. Different type of attributes are built-in with endless other possibilities:
   1. Configuration fields - SW write and read, HW read only
   2. Status fields - HW write SW read
   3. Interrupts - sticky bits with interrupt aggregation 
   4. SW write and SW read pulses - to notify the HW of changes in desired fields

## Classes
The language presents the following classes:
1. AccessPermissions - defines the access permissions of anything. Attributes:
   1. sw_rd, bool - SW read permissions
   2. sw_wr, bool - SW write permissions
   3. hw_rd, bool - HW read permissions
   4. hw_wr, bool - HW write permissions
2. Field - a field is a collection of bits. Attributes:
   1. name       , str               - the field's name
   2. description, str               - the field's description
   3. permissions, AccessPermissions - the field's access permissions
   4. width      , int               - the field's width in bits
   5. offset     , int               - the field's offset within a register
   6. reset_val  , int               - the field's reset value
   7. we         , bool              - whether the field gets an external HW write-enable bit
      1. CfgField - a subclass of Field, (HW RD, SW WR+RD) permissions
      2. StsField - a subclass of Field, (HW WR, SW RD) permissions
      3. SWPulseWRField - a subclass of Field, (HW RD, SW WR+RD), HW is provided a pulse for every SW write event.
      4. SWPulseRDField - a subclass of Field, (HW WR, SW RD), HW is provided a pulse for every SW read event.
3. Address - address within the register file. single attribute - byte_address.
4. Register - a collection of fields. Attributes:
   1. name          , str             - the register's name
   2. description   , str             - the register's description
   3. width         , int             - the register's width in bits
   4. address       , Address         - the register's address within a register file
   5. fields        , List[Field]     - a list of the fields in the register
   6. occupied_bmap , ndarray(width,) - a bitmap of occupied bits within the register  
5.  RegFile - a collection of registers. Attributes:
  1. name           , str            - the regfile's name
   2. description    , str            - the regfile's description
   3. registers      , List[Register] - a list of the registers in the regfile
   4. runnig_address , Address        - a pointer to the next non-occupied address in the register map
   5. rgf_addr_width , int            - address space width in bits
   6. rgf_reg_width  , int            - regfile register width, determined by the widest register

## Usage in Design 

1. The register description script should be placed under the 'regs' subfolder of the block.
   ```bash
    ╰─ tree blk 
    blk
    ├── misc
    │   └── blk.cfg
    ├── regs
    │   └── blk_rgf.py
    └── rtl
        └── blk_top.v
   ```
2. The register description script should be reffered to in the relevant view in the config under the "regs" section.
   ```config
    [rtl]
        design:
            top=blk_top
        regs:
            regs/blk_rgf.py
        file:
            rtl/blk_top.v
    ;
   ```
3. In the script, define a single RegFile, with a name matching the script name, by building it from: Fields --> Registers --> RegFile:
   ```python
   # 0. Some imports, you get this for free :)
    import os
    import sys
    tools_dir = os.environ["tools_dir"]
    sys.path.append(tools_dir)
    from regen.reg_classes import *

    # 1. Define Fields
    fld = Field('fld', 'field')

    # 2. Aggregate Fields to Registers
    reg = Register('reg', 'register', fields=[fld])

    # 3. Aggregate all Registers to a single RegFile
    blk_rgf = RegFile('blk_rgf', 'block regfile', registers=[reg])
   ```
4. There is no need to define offsets (unless you want to), the infrasturcture will handle that for you automatically
5. There is no need to handle addresses manualy (again, unless you want to)
6. An example can be found [here](../examples/example_ws/example_project/design/apb_fifo/regs/apb_fifo_rgf.py)

## Usage in Verification

The apb_infra.py script implements some basic functions and classes to allow the testbench to integrate smoothly with the register file:
1. APBTransaction - APB Transaction Class
   1. gets field's full name + data if this is a write transaction
   2. Looks up the register dictionary to find the field's address and strobe
   3. Converts the field's address + strobe + (data) to a traditional APB transaction
   4. Defines print function and overrides the __eq__ function
3. APBMasterDriver - APB Master Driver Class
   1. Drive new transactions by calling the _driver_send() function
   2. New transactions are appended to a transaction queue
   3. If the transaction queue transitions from empty to not-empty, a _tx_pipe coro is forked, trying to drive all transactions in queue over the APB bus
4. APBMonitor - APB Monitor Class
   1. Listen to the APB bus for valid transactions
An example of a testbench utilizing all of those can be found [here](../examples/example_ws/example_project/verification/apb_fifo/tests/apb_fifo_tb.py)

