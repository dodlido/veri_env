//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                                                                    |//
//| ~~ cnt_cfg_lim ~~                                                                  |//
//|                                                                                    |//
//| Top-level description:                                                             |//
//|    1. Count with a configurable limit                                              |//
//|                                                                                    |//
//| Features:                                                                          |//
//|    1. Configurable limit (lim)                                                     |//
//|    2. increment signal active high (inc)                                           |//
//|    3. soft reset, clear count value (clr)                                          |//
//|    4. Done pulse, active high (done)                                               |//
//|                                                                                    |//
//| Requirements:                                                                      |//
//|    1. CNT_W <= 32                                                                  |//
//|    1. lim width in bits = CNT_W                                                    |//
//|                                                                                    |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//

module cnt_cfg_lim #(
    parameter                  CNT_W =                          4 , // Counter width in bits
    localparam bit [CNT_W-1:0] ZERO  =              {CNT_W{1'b0}} , // Counter 0 val
    localparam bit [CNT_W-1:0] ONE   = {{(CNT_W-1){1'b0}},{1'b1}}   // Counter 1 val
) (
    // General // 
    input wire [      0:0] clk   , // Clock signal
    input wire [      0:0] rst_n , // Async reset, active low
    // input Control // 
    input wire [CNT_W-1:0] lim   , // Counter limit
    input wire [      0:0] inc   , // Increment counter
    input wire [      0:0] clr   , // Clear counter
    // Outputs // 
    output reg [CNT_W-1:0] count , // Counter value
    output reg [      0:0] done    // Counter reached LIM, pulse
);

// Internal wires & logic // 
// ---------------------- // 

// Wires // 
wire [      0:0] wrap_cond   ; // Count reached limit
wire [CNT_W-1:0] count_next  ; // Next value of count

// Logic // 
assign wrap_cond  = count == lim              ; // Count == lim
assign done       = inc & wrap_cond           ; // done pulse
assign count_next = clr & inc  ?         ONE  : // clear & increment    ==> go straight to 1
                    clr | done ?         ZERO : // clear or wrap around ==> go to 0
                    inc        ? count + ONE  : // regular inc          ==> +1
                                 count        ; // o.w                  ==> keep state

// FFs // 
// --- // 
base_reg #(.DAT_W(CNT_W)) i_base_reg (
   .clk     (clk        ), 
   .rst_n   (rst_n      ),
   .en      (1'b1       ),
   .data_in (count_next ),
   .data_out(count      )
);

endmodule

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  veri_env                       |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2024-12-24                     |//
//| 4. Version  :  v2.1.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
