// 
// apb_fifo_top.v 
//

module apb_fifo_top #(
   // Parameters // 
   // ---------- //
   parameter int  APB_ADD_W  =  5                , // APB's address bus width [bits]
   parameter int  APB_DAT_W  = 32                , // APB's data bus width [bits]
   parameter int  APB_STRB_W = int'(APB_DAT_W/8) , // APB's strobe bus width [bits] 
   parameter int  FIFO_DEPTH =  8                , // FIFO's depth
   parameter int  FIFO_DAT_W =  4                , // FIFO's data width [bits]
   localparam int FIFO_ADD_W = $clog2(FIFO_DEPTH)  // FIFO's address width [bits]
)(
  // General Signals //
  // --------------- //
  input  logic                  clk         , // clock signal
  input  logic                  rst_n       , // active low reset

  // APB IF to register file //
  // ----------------------- // 
  input  logic [APB_ADD_W -1:0] rgf_paddr   ,
  input  logic [3         -1:0] rgf_pprot   , 
  input  logic                  rgf_psel    ,
  input  logic                  rgf_penable ,
  input  logic                  rgf_pwrite  ,
  input  logic [APB_DAT_W -1:0] rgf_pwdata  ,
  input  logic [APB_STRB_W-1:0] rgf_pstrb   ,
  input  logic                  rgf_pwakeup ,
  output logic                  rgf_pready  ,
  output logic [APB_DAT_W -1:0] rgf_prdata  ,
  output logic                  rgf_pslverr ,

  // Interrupts //
  // ---------- //
  output logic                  fifo_err_intr 
  // Error interrupt in case of either overflow or underflow, can connect to some external CPU 
);

// Internal Wires //
// -------------- //
// FIFO controls //
logic                  fifo_push_c1   ; 
logic                  fifo_push      ; 
logic                  fifo_pop       ; 
logic                  fifo_clr       ; 
// FIFO statuses //
logic                  fifo_sts_full  ; 
logic                  fifo_sts_af    ; 
logic                  fifo_sts_ae    ; 
logic                  fifo_sts_empty ; 
logic [FIFO_ADD_W  :0] fifo_sts_count ; 
// FIFO interrupts // 
logic                  fifo_ovfl      ; 
logic                  fifo_udfl      ;
// FIFO configurations // 
logic [FIFO_ADD_W  :0] fifo_af_th     ; 
logic [FIFO_ADD_W  :0] fifo_ae_th     ; 
// FIFO address busses //
logic [FIFO_ADD_W-1:0] fifo_add       ; 
logic [FIFO_ADD_W-1:0] fifo_rd_ptr    ; 
logic [FIFO_ADD_W-1:0] fifo_wr_ptr    ; 
// FIFO data busses // 
logic [FIFO_DAT_W-1:0] fifo_dat_in    ; 
logic [FIFO_DAT_W-1:0] fifo_dat_out   ; 

assign fifo_add = fifo_push ? fifo_wr_ptr : fifo_rd_ptr ; 

// --------------------------------------------------------- //
// the below instance was generated automatically by enst.py //

gen_reg_mem_top #(
   .DAT_W(FIFO_DAT_W),
   .DEPTH(FIFO_DEPTH),
   .ADD_W(FIFO_ADD_W)
) i_gen_reg_mem_top (
   // General // 
   .clk     (clk            ), // i, 0:0   X logic  , clock signal
   .rst_n   (rst_n          ), // i, 0:0   X logic  , Async reset. active low
   // Input control // 
   .cs      (1'b1           ), // i, 0:0   X logic  , Chip-select
   .wen     (fifo_push      ), // i, 0:0   X logic  , Write enable
   .add     (fifo_add       ), // i, ADD_W X logic  , Address
   // Input data // 
   .dat_in  (fifo_dat_in    ), // i, DAT_W X logic  , Input data
   .bit_sel (FIFO_DAT_W'(0) ), // i, DAT_W X logic  , bit-select
   // Output data // 
   .dat_out (fifo_dat_out   )  // o, DAT_W X logic  , Output data
);

// the above instance was generated automatically by enst.py //
// --------------------------------------------------------- //

// --------------------------------------------------------- //
// the below instance was generated automatically by enst.py //

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

// the above instance was generated automatically by enst.py //
// --------------------------------------------------------- //

// ------------------------------------ // 
// Automatically Generated RGF instance // 
// ------------------------------------ // 

apb_fifo_rgf i_apb_fifo_rgf ( 
   // General // 
   // ------- //
   .clk                                        (clk             ),
   .rst_n                                      (rst_n           ),
   
   // HW IF to RGF // 
   // ------------ //
   .apb_fifo_rgf_cfg_cfg_af_th                 (fifo_af_th      ), // fifo_rgf_cfg_cfg_af_th: HW read port , output(3b)
   .apb_fifo_rgf_cfg_cfg_ae_th                 (fifo_ae_th      ), // fifo_rgf_cfg_cfg_ae_th: HW read port , output(3b)
   .apb_fifo_rgf_sts_sts_full_hw_next          (fifo_sts_full   ), // fifo_rgf_sts_sts_full: HW write port , input(1b)
   .apb_fifo_rgf_sts_sts_af_hw_next            (fifo_sts_af     ), // fifo_rgf_sts_sts_af: HW write port , input(1b)
   .apb_fifo_rgf_sts_sts_ae_hw_next            (fifo_sts_ae     ), // fifo_rgf_sts_sts_ae: HW write port , input(1b)
   .apb_fifo_rgf_sts_sts_empty_hw_next         (fifo_sts_empty  ), // fifo_rgf_sts_sts_empty: HW write port , input(1b)
   .apb_fifo_rgf_cnt_sts_count_hw_next         (fifo_sts_count  ), // fifo_rgf_cnt_sts_count: HW write port , input(4b)
   .apb_fifo_rgf_cntrl_fifo_clr                (                ), // fifo_rgf_cntrl_fifo_clr: HW read port , output(1b)
   .apb_fifo_rgf_cntrl_fifo_clr_sw_wr_pulse    (fifo_clr        ), // fifo_rgf_cntrl_fifo_clr: SW wrote this field, pulse, active high , output(1b)
   .apb_fifo_rgf_intr_fifo_ovfl_hw_next        (fifo_ovfl       ), // fifo_rgf_intr_fifo_ovfl: HW write port , input(1b)
   .apb_fifo_rgf_intr_fifo_udfl_hw_next        (fifo_udfl       ), // fifo_rgf_intr_fifo_udfl: HW write port , input(1b)
   .apb_fifo_rgf_dat_dat_in_fld                (fifo_dat_in     ), // fifo_rgf_dat_dat_in_fld: HW read port , output(4b)
   .apb_fifo_rgf_dat_dat_in_fld_sw_wr_pulse    (fifo_push_c1    ), // fifo_rgf_dat_dat_in_fld: SW wrote this field, pulse, active high , output(1b)
   .apb_fifo_rgf_dat_dat_out_fld_hw_next       (fifo_dat_out    ), // fifo_rgf_dat_dat_out_fld: HW write port , input(4b)
   .apb_fifo_rgf_dat_dat_out_fld_sw_rd_pulse   (fifo_pop        ), // fifo_rgf_dat_dat_out_fld: SW read this field, pulse, active high , output(1b)
   .apb_fifo_rgf___intr                        (fifo_err_intr   ), // fifo_rgf__: agrregation of interrups in regfile , output(1b)

   // APB IF // 
   // ------ //
   .paddr                                      (rgf_paddr       ),
   .pprot                                      (rgf_pprot       ),
   .psel                                       (rgf_psel        ),
   .penable                                    (rgf_penable     ),
   .pwrite                                     (rgf_pwrite      ),
   .pwdata                                     (rgf_pwdata      ),
   .pstrb                                      (rgf_pstrb       ),
   .pwakeup                                    (rgf_pwakeup     ),
   .pready                                     (rgf_pready      ),
   .prdata                                     (rgf_prdata      ),
   .pslverr                                    (rgf_pslverr     )
);

// ------------------------------------ // 
// Automatically Generated RGF instance // 
// ------------------------------------ // 

always_ff @(posedge clk)
   if (!rst_n)
      fifo_push <= 1'b0 ;
   else
      fifo_push <= fifo_push_c1 ; 

endmodule
