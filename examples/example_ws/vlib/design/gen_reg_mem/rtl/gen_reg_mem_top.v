//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                                                                    |//
//| ~~ gen_reg_mem_top.v ~~                                                            |//
//|                                                                                    |//
//| Top-level description:                                                             |//
//|    1. Single-port register based memory                                            |//
//|                                                                                    |//
//| Features:                                                                          |//
//|    1. Parameterized delays:                                                        |//
//|       a. DLY_USER2MEM - number of cycles delay from user controls to mem instance  |//
//|       b. DLY_USER2MEM - number of cycles delay from mem instance to user data out  |//
//|    2. Parameterized dimensions:                                                    |//
//|       a. DAT_W - number of bits per memory word                                    |//
//|       b. DEPTH - number of memory words                                            |//
//|       c. ADD_W - address width in bits, defaults to log2(DEPTH)                    |//
//|    3. Options:                                                                     |//
//|       a. LOW_PWR_OPT - low power option, if active data is valid-dependent.        |//
//|                        o.w, data is free-flowing                                   |//
//|       b. BIT_EN      - bit-enable option, if active memory write data is the result|//
//|                        of bit-wise and operation between dat_in and bit_sel        |//
//|                        o.w, bit-sel is ignored                                     |//
//|                                                                                    |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//

module gen_reg_mem_top #(
    // Memory dimensions // 
    parameter int       DAT_W        =             8 , // data width in bits 
    parameter int       DEPTH        =            32 , // Memory depth (number of words)
    parameter int       ADD_W        = $clog2(DEPTH) , // Address width in bits
    // Delay parameters // 
    parameter int       DLY_USER2MEM = 0             , // User to memory delay in cycles
    parameter int       DLY_MEM2USER = 0             , // Memory to user delay in cycles
    // Option parameters // 
    parameter bit [0:0] LOW_PWR_OPT  = 1'b1          , // Low power mode option
    parameter bit [0:0] BIT_EN_OPT   = 1'b0            // Bit-enable mechanism option
)(
    // General // 
    input  logic [      0:0] clk     , // clock signal
    input  logic [      0:0] rst_n   , // Async reset, active low
    // Input control // 
    input  logic [      0:0] cs      , // Chip-select 
    input  logic [      0:0] wen     , // Write enable
    input  logic [ADD_W-1:0] add     , // Address  
    // Input data // 
    input  logic [DAT_W-1:0] dat_in  , // Input data
    input  logic [DAT_W-1:0] bit_sel , // bit-select
    // Output data // 
    output logic [DAT_W-1:0] dat_out   // Output data
);

// Internal wires declaration // 
logic            [      0:0] masked_wr                ; 
logic            [      0:0] masked_rd                ;
logic            [DAT_W-1:0] mem_dat_in               ;
logic [DEPTH-1:0][DAT_W-1:0] mem_dat_in_post_bit_sel  ;
logic            [ADD_W-1:0] mem_add                  ;
logic            [      0:0] mem_wr                   ;
logic            [      0:0] mem_cs                   ;
logic            [DAT_W-1:0] mem_dat_out              ;
logic [DEPTH-1:0][DAT_W-1:0] mem_array                ; 
logic [DEPTH-1:0]            mem_wen_vec              ;

// Mask write and read with master enable // 
assign masked_wr =  wen & cs ; 
assign masked_rd = ~wen & cs ; 

// Generate data input from user side // 
generate
   if (BIT_EN_OPT) begin: gen_bit_en_cond // BIT_EN_OPT is on, propagate bit_sel
      wire [DAT_W-1:0] mem_bit_sel ; 
      gen_pipe_top #(.DEPTH(DLY_USER2MEM), .DAT_W(2*DAT_W+ADD_W+1), .LOW_PWR_OPT(LOW_PWR_OPT)) i0_ctrl_pipe (
         .clk      (clk                                          ),
         .rst_n    (rst_n                                        ),
         .dat_in   ({bit_sel    , dat_in    , add    , masked_wr}),
         .vld_in   (cs                                           ),
         .dat_out  ({mem_bit_sel, mem_dat_in, mem_add, mem_wr   }),
         .vld_out  (mem_cs                                       )
      ); 
   end
   else begin: gen_bit_dis_cond // BIT_EN_OPT is off, don't propagate bit_sel
      gen_pipe_top #(.DEPTH(DLY_USER2MEM), .DAT_W(DAT_W+ADD_W+1), .LOW_PWR_OPT(LOW_PWR_OPT)) i1_ctrl_pipe (
         .clk      (clk                             ),
         .rst_n    (rst_n                           ),
         .dat_in   ({dat_in    , add    , masked_wr}),
         .vld_in   (cs                              ),
         .dat_out  ({mem_dat_in, mem_add, mem_wr   }),
         .vld_out  (mem_cs                          )
      ); 
   end
endgenerate

// Generate internal storage // 
genvar ADD_IDX, BIT_IDX ; 
generate
   for (ADD_IDX = 0; ADD_IDX<DEPTH; ADD_IDX++) begin : gen_mem_loop

      // Generate post-bit-select data // 
      if (BIT_EN_OPT) begin: gen_bit_sel_dat_en_cond
         for (BIT_IDX=0; BIT_IDX<DAT_W; BIT_IDX++) begin: gen_bit_sel_dat_en_loop
            assign mem_dat_in_post_bit_sel[ADD_IDX][BIT_IDX] = mem_bit_sel[BIT_IDX] ? mem_dat_in[BIT_IDX] : mem_array[ADD_IDX][BIT_IDX] ; 
         end
      end
      else begin: gen_bit_sel_dat_dis_cond
         assign mem_dat_in_post_bit_sel[ADD_IDX] = mem_dat_in ; 
      end

      // Write enable for each individual memory cell // 
      assign mem_wen_vec[ADD_IDX] = (ADD_IDX[ADD_W-1:0]==mem_add) & mem_wr ; 
 
      // Generate DAT_W FFs instance per cell //
      always_ff @(posedge clk) 
         if (!rst_n) 
            mem_array[ADD_IDX] <= DAT_W'(0) ; 
         else if (mem_wen_vec[ADD_IDX])
            mem_array[ADD_IDX] <= mem_dat_in_post_bit_sel[ADD_IDX] ; 
   end
endgenerate

// MUX output data from RAM 
assign mem_dat_out = mem_array[mem_add] ;  

// Generate output data-path pipe // 
gen_pipe_top #(.DEPTH(DLY_MEM2USER), .DAT_W(DAT_W), .LOW_PWR_OPT(LOW_PWR_OPT)) out_pipe (
    .clk      (clk        ),
    .rst_n    (rst_n      ),
    .dat_in   (mem_dat_out),
    .vld_in   (mem_cs     ),
    .dat_out  (dat_out    ),
    .vld_out  (           )  // NC
); 

endmodule

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  vlib                           |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2024-12-30                     |//
//| 4. Version  :  v0.6.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
