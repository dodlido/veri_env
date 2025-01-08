//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                                                                    |//
//| ~~ gen_fifo_ctrl.v ~~                                                              |//
//|                                                                                    |//
//| Top-level description:                                                             |//
//|    1. Basic FIFO control                                                           |//
//|                                                                                    |//
//| Features:                                                                          |//
//|    1. Parameterized fifo depth (DEPTH)                                             |//
//|    2. Read and write pointers as address management                                |//
//|    3. full, empty and count as status output                                       |//
//|                                                                                    |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//

module gen_fifo_ctrl_top #(
    parameter  DEPTH = 16            , // FIFO depth 
    localparam PTR_W = $clog2(DEPTH) , // Pointers width [bits]
    localparam CNT_W = PTR_W + 1       // Counter width [bits]
) (
    // General // 
    // ------- // 
    input  logic [      0:0] clk        , // Clock signal 
    input  logic [      0:0] rst_n      , // Async reset, active low

    // Configurations //
    // -------------- // 
    input  logic [CNT_W-1:0] cfg_af_th  , // almost-full threshold, anything including and above this value will assert sts_af
    input  logic [CNT_W-1:0] cfg_ae_th  , // almost-empty threshold, anything including and below this value will assert sts_ae

    // Input Controls // 
    // -------------- //
    input  logic [      0:0] clr        , // Clear FIFO, reset all pointers to 0
    input  logic [      0:0] push       , // Write enable active high
    input  logic [      0:0] pop        , // Output enable active high

    // Output Controls // 
    // --------------- //
    output logic [PTR_W-1:0] rd_ptr     , // Read pointer
    output logic [PTR_W-1:0] wr_ptr     , // Write pointer

    // Output Statuses //
    // --------------- //
    output logic [CNT_W-1:0] sts_count  , // FIFO count
    output logic [      0:0] sts_full   , // FIFO full
    output logic [      0:0] sts_af     , // FIFO almost-full
    output logic [      0:0] sts_ae     , // FIFO almost-empty
    output logic [      0:0] sts_empty  , // FIFO empty
    output logic [      0:0] err_ovfl   , // error - overflow detected
    output logic [      0:0] err_udfl     // error - underflow detected
);

// Internal wires // 
// -------------- // 
logic rd_ptr_inc_cond ; 
logic wr_ptr_inc_cond ; 

// Statuses // 
// -------- //
assign sts_full  = (sts_count == CNT_W'(DEPTH)) ; // Full logic
assign sts_af    = (sts_count >= cfg_af_th)     ; // Almost full logic
assign sts_ae    = (sts_count <= cfg_ae_th)     ; // Almost empty logic
assign sts_empty = (sts_count == CNT_W'(0))     ; // Empty logic
assign err_ovfl  = push & sts_full              ; // Push on empty
assign err_udfl  = pop & sts_empty              ; // Pop on empty

// Read Pointer //
// ------------ //
assign rd_ptr_inc_cond = pop & ~sts_empty ; // increase read pointer if pop and not empty
gen_cnt_top #(.CNT_W(PTR_W)) i_rd_ptr_cnt (
   // General //
   // ------- //
   .clk   (clk            ), // i1       , clock signal
   .rst_n (rst_n          ), // i1       , sync reset
   // Input Controls //
   // -------------- // 
   .lim   (PTR_W'(DEPTH-1)), // i1       , limit
   .inc   (rd_ptr_inc_cond), // i1       , increment 
   .dec   (1'b0           ), // NC
   .clr   (clr            ), // i1       , clear
   // Output Count //
   // ------------ //
   .count (rd_ptr         )  // o(CNT_W) , count value
);

// Write Pointer //
// ------------- //
assign wr_ptr_inc_cond = push & ~sts_full ; // increase read pointer if pop and not empty
gen_cnt_top #(.CNT_W(PTR_W)) i_wr_ptr_cnt (
   // General //
   // ------- //
   .clk   (clk            ), // i1       , clock signal
   .rst_n (rst_n          ), // i1       , sync reset
   // Input Controls //
   // -------------- // 
   .lim   (PTR_W'(DEPTH-1)), // i1       , limit
   .inc   (wr_ptr_inc_cond), // i1       , increment 
   .dec   (1'b0           ), // NC
   .clr   (clr            ), // i1       , clear
   // Output Count //
   // ------------ //
   .count (wr_ptr         )  // o(CNT_W) , count value
);

// Count // 
// ----- // 
gen_cnt_top #(.CNT_W(CNT_W)) i_count_cnt (
   // General //
   // ------- //
   .clk   (clk            ), // i1       , clock signal
   .rst_n (rst_n          ), // i1       , sync reset
   // Input Controls //
   // -------------- // 
   .lim   (CNT_W'(DEPTH  )), // i1       , limit
   .inc   (wr_ptr_inc_cond), // i1       , increment 
   .dec   (rd_ptr_inc_cond), // NC
   .clr   (clr            ), // i1       , clear
   // Output Count //
   // ------------ //
   .count (sts_count      )  // o(CNT_W) , count value
);

endmodule

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  veri_env                       |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2025-01-09                     |//
//| 4. Version  :  v4.2.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
