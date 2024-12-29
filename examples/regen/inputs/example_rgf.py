# imports - creating a block with the blk script will make
# sure you get syntax highlighting and autocompletion
# when using code editors that offer those features
import os
import sys
tools_dir = os.environ['tools_dir']
sys.path.append(tools_dir)
from regen.reg_classes import *

# Configuration Fields
clk_en = CfgField(name='clk_en', description='clock enable', width=1)           # The permissions are set automatically since this is a CfgField subclass
rgb_mode = CfgField(name='rgb_mode', description='RGB mode enable', width=1)    # The offset is not handled here, the infrastructure does that for you if you want
n_col = CfgField(name='n_col', description='number of pixels in row', width=16) # Reset val defaults to 0
n_row = CfgField(name='n_row', description='number of rows in frame', width=16) 

# Configuration Registers 
frame_dims = Register('frame_dims', 'frame dimensions register', fields=[n_col, n_row])    # composing a register is simply a matter of listing all fields you want
general_cfg = Register('general_cfg', 'general configurations', fields=[clk_en, rgb_mode]) # here, not all bits are occupied, this is OK and will not cost any redundant FFs

# Status Fields
col_ptr = StsField(name='col_ptr', description='pointer to current pixel in row', width=16) # This is a status field, permissions are set automatically
row_ptr = StsField(name='row_ptr', description='pointer to current row number', width=16)   

# Status Registers 
loc_sts = Register(name='loc_sts', description='current location in frame', fields=[col_ptr, row_ptr]) # Offseting the fields is done automatically if you don't want to handle that

# Register File
example_rgf = RegFile(name='example_rgf', description='example register file', registers=[frame_dims, general_cfg, loc_sts]) # Declaring a regfile
# This declaration is a must in all Regen descriptions. the regfile name must match that of the script
# The address space is handled automatically if you don't want to hard set it, addresses are assumed to be Byte-address

