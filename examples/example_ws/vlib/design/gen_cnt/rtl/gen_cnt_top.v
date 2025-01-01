//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                                                                    |//
//| ~~ gen_cnt_top.v ~~                                                                |//
//|                                                                                    |//
//| Top-level description:                                                             |//
//|    1. Counter with a configurable limit                                            |//
//|                                                                                    |//
//| Features:                                                                          |//
//|    1. Configurable limit (lim)                                                     |//
//|    2. increment signal active high (inc)                                           |//
//|    3. decrement signal active high (dec)                                           |//
//|    4. clear count value (clr)                                                      |//
//|                                                                                    |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//

module gen_cnt_top #(
    parameter  CNT_W = 4   // Counter width in bits
) (
    // General // 
    // ------- //
    input  logic [      0:0] clk   , // Clock signal
    input  logic [      0:0] rst_n , // sync reset, active low

    // Input Controls // 
    // -------------- //
    input  logic [CNT_W-1:0] lim   , // Counter limit
    input  logic [      0:0] inc   , // Increment counter
    input  logic [      0:0] dec   , // Decrement counter
    input  logic [      0:0] clr   , // Clear counter

    // Output Count // 
    // ------------ //
    output logic [CNT_W-1:0] count   // Counter value
);

// Wires // 
logic             msk_inc     ; // masked increment condition
logic             msk_dec     ; // masked decrement condition
logic             wrap_cond   ; // Count reached limit
logic [CNT_W-1:0] count_next  ; // Next value of count

// Logic // 
assign msk_inc = inc & ~dec ; 
assign msk_dec = dec & ~inc ; 
assign wrap_cond  = (count==lim) & msk_inc ; // Count == limit
assign count_next = clr | wrap_cond ? CNT_W'(0) : msk_inc ? count + CNT_W'(1) : msk_dec ? count - CNT_W'(1) : count ; 

// count FFs // 
always_ff @( posedge clk) begin 
    if (!rst_n) begin
        count <= CNT_W'(0) ; // Reset count 
    end
    else begin
        count <= count_next ; // Sample next
    end
end

endmodule

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  vlib                           |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2024-12-30                     |//
//| 4. Version  :  v0.6.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
