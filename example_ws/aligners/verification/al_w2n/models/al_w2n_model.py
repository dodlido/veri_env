from typing import Tuple

def al_w2n_model(us_vld: bool, us_last_vld_sel: int, ds_rdy: bool, us_dat: int, curr_sel: int, dat_out_w: int) -> Tuple[bool, bool, int, int]:
    
    # DS valid is simply US valid
    ds_vld = us_vld 

    # Next select and read request
    if ds_rdy and us_vld: # Advance aligner IFF both downstream ready and upstream vld
        us_rd_rqst = us_last_vld_sel==curr_sel
        next_sel = 0 if us_rd_rqst else curr_sel + 1 
    else: # otherwise keep current select
        next_sel = curr_sel
        us_rd_rqst = False

    # Output Data
    mask = 2 ** dat_out_w - 1 # mask is 0xFF for DAT_OUT_W = 8 
    ds_dat = ((us_dat >> (curr_sel*dat_out_w)) & mask)

    return us_rd_rqst, ds_vld, ds_dat, next_sel

