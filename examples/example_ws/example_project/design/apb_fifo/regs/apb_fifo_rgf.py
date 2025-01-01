import os
import sys
tools_dir = os.environ["tools_dir"]
sys.path.append(tools_dir)
from regen.reg_classes import *

# Configurable Thresholds #
cfg_af_th_fld = CfgField('cfg_af_th', 'FIFO\'s almost full configuration, specified in number of [entries]. sts_af is asserted if the FIFO count is equal or greater than this', width=4)
cfg_ae_th_fld = CfgField('cfg_ae_th', 'FIFO\'s almost empty configuration, specified in number of [entries]. sts_ae is asserted if the FIFO count is equal or smaller than this', width=4)
cfg_reg = Register('cfg', 'configuration register', 32, [cfg_af_th_fld, cfg_ae_th_fld])

# Full and Empty Statuses # 
sts_full_fld = StsField('sts_full', 'FIFO\'s full status', width=1)
sts_af_fld = StsField('sts_af', 'FIFO\'s almost full status', width=1)
sts_ae_fld = StsField('sts_ae', 'FIFO\'s almost empty status', width=1)
sts_empty_fld = StsField('sts_empty', 'FIFO\'s empty status', width=1)
sts_reg = Register('sts', 'Status register', 32, [sts_full_fld, sts_af_fld, sts_ae_fld, sts_empty_fld])

# Current Count #
sts_cnt_fld = StsField('sts_count', 'FIFO\'s count status', width=4)
cnt_reg = Register('cnt', 'FIFO\'s count', 32, [sts_cnt_fld])

# FIFO controls # 
fifo_clr_fld = SWPulseWRField('fifo_clr', 'FIFO\'s clear, resets the FIFO pointers and counters, automatically generates a pulse to the HW when you write this field', width=1)
cntrl_reg = Register('cntrl', 'FIFO\'s controls', 32, [fifo_clr_fld])

# FIFO interrupts # 
fifo_ovfl = IntrField('fifo_ovfl', 'FIFO\'s overflow interrupt')
fifo_udfl = IntrField('fifo_udfl', 'FIFO\'s underflow interrupt')
intr_reg = Register('intr', 'Interrupt register', 32, [fifo_ovfl, fifo_udfl])

# FIFO data # 
dat_in_fld = SWPulseWRField('dat_in_fld', 'FIFO\'s input data', width=4) # regen generates a pulse when this is written, the pulse is used by the HW as the FIFO's push signal
dat_out_fld = SWPulseRDField('dat_out_fld', 'FIFO\'s output data', width=4) # regen generates a pulse when this is read, the pulse is used by the HW as the FIFO's pop signal
dat_reg = Register('dat', 'data register', 32, [dat_in_fld, dat_out_fld])

# RegFile #
apb_fifo_rgf = RegFile('apb_fifo_rgf', 'FIFO register file', [cfg_reg, sts_reg, cnt_reg, cntrl_reg, intr_reg, dat_reg])
