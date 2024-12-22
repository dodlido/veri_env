// ------------------------------------------------------------------------------- // 
//                                                                                 // 
// al_w2n.v                                                                        //
//                                                                                 // 
// Description:                                                                    //
// 1. this module is a wide-to-narrow aligner                                      //
// 2. wide side is upstream, narrow side is downstream                             //
// 3. aligner advances if us_vld is active and ds_rdy is active                    //
// 4. aligner generates read requests from upstream via us_rd_rqst                 //
//    * aligner assumes data is ready for use @ next cycle unless valid is low     //
// 5. upstream can generate a last-valid-select control bit to choose where        //
//    to wrap around for each individual packet                                    //
//                                                                                 // 
// Requirments:                                                                    //
// 1. DAT_IN_W % DAT_OUT_W = 0                                                     // 
// 2. DAT_OUT_W must be a power of 2                                               //                                
//                                                                                 // 
// ------------------------------------------------------------------------------- // 

module al_w2n #(
   parameter  int DAT_IN_W  =                       32 , // input data width [bits]
   parameter  int DAT_OUT_W =                        8 , // output data width [bits]
   localparam int AL_SEL_W  = $clog2(DAT_IN_W/DAT_OUT_W) // Aligner select control width [bits] 
)(
   // General // 
   // ------- // 
   input  logic                 clk             , // clock signal 
   input  logic                 rst_n           , // async reset active low

   // Up-Stream Controls // 
   // ------------------ // 
   input  logic                 us_vld          , // up-stream valid indicator
   input  logic [AL_SEL_W -1:0] us_last_vld_sel , // up-stream last valid select, 0-based
   output logic                 us_rd_rqst      , // read request from up-stream 

   // Down-Stream Controls // 
   // -------------------- // 
   input  logic                 ds_rdy          , // down-stream ready for next data packet
   output logic                 ds_vld          , // down-stream valid indicator 

   // Data // 
   // ---- // 
   input  logic [DAT_IN_W -1:0] us_dat          , // data from up-stream
   output logic [DAT_OUT_W-1:0] ds_dat            // data to down-stream
);

// Local Parameters // 
// ---------------- //
localparam int AL_SHIFT   = $clog2(DAT_OUT_W) ; 
localparam int PART_SEL_W = $clog2(DAT_IN_W ) ; 

// Internal Wires //
// -------------- //
logic                  al_sel_inc_cond ; 
logic                  al_sel_wrap_cond ; 
logic [AL_SEL_W  -1:0] al_sel_next ; 
logic [PART_SEL_W-1:0] part_sel_lsb ; 

// Internal Registers //
// ------------------ // 
logic [AL_SEL_W  -1:0] al_sel_curr ; 

// Internal Logic //
// -------------- //
assign al_sel_inc_cond = us_vld & ds_rdy ;

cnt_cfg_lim #(.CNT_W(AL_SEL_W)) i_cnt_cfg_lim (
   .clk     (clk              ), 
   .rst_n   (rst_n            ),
   .lim     (us_last_vld_sel  ),
   .inc     (al_sel_inc_cond  ),
   .clr     (1'b0             ),
   .count   (al_sel_curr      ),
   .done    (al_sel_wrap_cond )
);

assign part_sel_lsb = {al_sel_curr, AL_SHIFT'(0)} ; // Shift current count by AL_SHIFT to get to current LSbit 

// Output Logic // 
// ------------ // 
assign us_rd_rqst = al_sel_wrap_cond ; 
assign ds_vld = us_vld ; 
assign ds_dat = us_dat[part_sel_lsb +: DAT_OUT_W] ; 




endmodule

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  veri_env                       |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2024-12-23                     |//
//| 4. Version  :  v2.0.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
