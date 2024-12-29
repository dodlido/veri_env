module example_rgf #(
   // Parameters // 
   // ---------- // 
   parameter DAT_W  = 32 , 
   parameter ADD_W  = 3 , 
   parameter STRB_W = $clog2(DAT_W/8)
) (
   // General //
   // ------- //
   input logic clk ,
   input logic rst_n , 

   // HW IF to registers //
   // ------------------ // 
   output logic [16-1:0] example_rgf_frame_dims_n_col, // example_rgf_frame_dims_n_col: HW read port
   output logic [16-1:0] example_rgf_frame_dims_n_row, // example_rgf_frame_dims_n_row: HW read port
   output logic [1-1:0] example_rgf_general_cfg_clk_en, // example_rgf_general_cfg_clk_en: HW read port
   output logic [1-1:0] example_rgf_general_cfg_rgb_mode, // example_rgf_general_cfg_rgb_mode: HW read port
   output logic [16-1:0] example_rgf_loc_sts_col_ptr, // example_rgf_loc_sts_col_ptr: HW read port
   input  logic [16-1:0] example_rgf_loc_sts_col_ptr_hw_next, // example_rgf_loc_sts_col_ptr: HW write port
   output logic [16-1:0] example_rgf_loc_sts_row_ptr, // example_rgf_loc_sts_row_ptr: HW read port
   input  logic [16-1:0] example_rgf_loc_sts_row_ptr_hw_next, // example_rgf_loc_sts_row_ptr: HW write port
   
   // APB IF // 
   // ------ //
   input  logic [ADD_W -1:0] paddr   ,
   input  logic [3     -1:0] pprot   , 
   input  logic              psel    ,
   input  logic              penable ,
   input  logic              pwrite  ,
   input  logic [DAT_W -1:0] pwdata  ,
   input  logic [STRB_W-1:0] pstrb   ,
   input  logic              pwakeup ,
   output logic              pready  ,
   output logic [DAT_W -1:0] prdata  ,
   output logic              pslverr 
);
    
// Local Parameters and Type Definitions //
// ------------------------------------- // 
localparam STRB_N = int'(DAT_W/8) ; 
typedef enum bit [1:0] {APB_IDLE=2'h0, APB_WRITE=2'h1, APB_READ=2'h2} apb_sts_e;

// Top Level Internal Wires // 
// ------------------------ // 
logic [DAT_W-1:0] pstrb_mask ; 
apb_sts_e apb_sts_next ; 

// Top Level Registers // 
// ------------------- // 
apb_sts_e apb_sts_curr ; 

// Top Level Logic // 
// --------------- // 
// Next state logic // 
always_comb begin
   case (apb_sts_curr)
      APB_IDLE: begin 
         if (psel & pwrite)
            apb_sts_next = APB_WRITE ; 
         else if (psel)
            apb_sts_next = APB_READ  ; 
         else
            apb_sts_next = APB_IDLE ; 
      end
      APB_READ: begin
         if (pready & penable)
            apb_sts_next = APB_IDLE ; 
         else 
            apb_sts_next = APB_READ ; 
      end
      APB_WRITE: begin
         if (pready & penable)
            apb_sts_next = APB_IDLE ; 
         else 
            apb_sts_next = APB_WRITE ; 
      end 
   endcase
end
always_ff @(posedge clk) if (!rst_n) apb_sts_curr <= APB_IDLE ; else apb_sts_curr <= apb_sts_next ; 
// Output Controls // 
always_comb begin // TODO: add slave error logic
   case (apb_sts_curr)
      APB_IDLE: begin 
         pready = 1'b0 ; 
         pslverr = 1'b0 ; 
      end
      APB_READ: begin
         pready = 1'b1 ; 
         pslverr = 1'b0 ; 
      end
      APB_WRITE: begin
         pready = 1'b1 ; 
         pslverr = 1'b0 ; 
      end
   endcase
end
// PSTRB mask // 
genvar STRB_IDX ; 
generate
for (STRB_IDX=0; STRB_IDX<STRB_N; STRB_IDX++) begin: gen_strb_mask
   assign pstrb_mask[(STRB_IDX*8)+:8] = pstrb[STRB_IDX];
end
endgenerate

// Register File //
// ------------- //
// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: frame_dims, REG_ADD: 0x0, FLD_NAME: n_col, FLD_BITS 15:0 // 

// Internal Wires // 
logic             example_rgf_frame_dims_n_col_sw_write_access ; // SW has write access condition
logic             example_rgf_frame_dims_n_col_hw_write_access ; // HW has write access condition
logic             example_rgf_frame_dims_n_col_sw_we           ; // SW write enable
logic             example_rgf_frame_dims_n_col_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_frame_dims_n_col_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_frame_dims_n_col_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_frame_dims_n_col_sw_write_access = 1'b1 ; // SW write access is taken from field attribites
assign example_rgf_frame_dims_n_col_hw_write_access = 1'b0 ; // HW write access is taken from field attribites
assign example_rgf_frame_dims_n_col_sw_we = (paddr==ADD_W'(0)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_frame_dims_n_col_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_frame_dims_n_col_sw_next = pwdata[0+:16] & pstrb_mask[0+:16] ; // next value of SW is masked with APB's pstrb
assign example_rgf_frame_dims_n_col_next = example_rgf_frame_dims_n_col_sw_write_access & example_rgf_frame_dims_n_col_sw_we     ? example_rgf_frame_dims_n_col_sw_next : // write SW value
//                                   example_rgf_frame_dims_n_col_hw_we_int & example_rgf_frame_dims_n_col_hw_write_access ? example_rgf_frame_dims_n_col_hw_next : // write HW value
                                                                                                                                               example_rgf_frame_dims_n_col         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_frame_dims_n_col <= 16'h0 ; 
    end
    else begin // sample next
        example_rgf_frame_dims_n_col <= example_rgf_frame_dims_n_col_next ; 
    end
end

// RGF: example_rgf, REG: frame_dims, REG_ADD: 0x0, FLD_NAME: n_col, FLD_BITS 15:0 //
// ------------------------------------------------------------------------------------------------------------------ //


// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: frame_dims, REG_ADD: 0x0, FLD_NAME: n_row, FLD_BITS 31:16 // 

// Internal Wires // 
logic             example_rgf_frame_dims_n_row_sw_write_access ; // SW has write access condition
logic             example_rgf_frame_dims_n_row_hw_write_access ; // HW has write access condition
logic             example_rgf_frame_dims_n_row_sw_we           ; // SW write enable
logic             example_rgf_frame_dims_n_row_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_frame_dims_n_row_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_frame_dims_n_row_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_frame_dims_n_row_sw_write_access = 1'b1 ; // SW write access is taken from field attribites
assign example_rgf_frame_dims_n_row_hw_write_access = 1'b0 ; // HW write access is taken from field attribites
assign example_rgf_frame_dims_n_row_sw_we = (paddr==ADD_W'(0)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_frame_dims_n_row_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_frame_dims_n_row_sw_next = pwdata[16+:16] & pstrb_mask[16+:16] ; // next value of SW is masked with APB's pstrb
assign example_rgf_frame_dims_n_row_next = example_rgf_frame_dims_n_row_sw_write_access & example_rgf_frame_dims_n_row_sw_we     ? example_rgf_frame_dims_n_row_sw_next : // write SW value
//                                   example_rgf_frame_dims_n_row_hw_we_int & example_rgf_frame_dims_n_row_hw_write_access ? example_rgf_frame_dims_n_row_hw_next : // write HW value
                                                                                                                                               example_rgf_frame_dims_n_row         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_frame_dims_n_row <= 16'h0 ; 
    end
    else begin // sample next
        example_rgf_frame_dims_n_row <= example_rgf_frame_dims_n_row_next ; 
    end
end

// RGF: example_rgf, REG: frame_dims, REG_ADD: 0x0, FLD_NAME: n_row, FLD_BITS 31:16 //
// ------------------------------------------------------------------------------------------------------------------ //



logic [32-1:0] example_rgf_frame_dims ;
assign example_rgf_frame_dims = {example_rgf_frame_dims_n_col, example_rgf_frame_dims_n_row};


// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: general_cfg, REG_ADD: 0x20, FLD_NAME: clk_en, FLD_BITS 0:0 // 

// Internal Wires // 
logic             example_rgf_general_cfg_clk_en_sw_write_access ; // SW has write access condition
logic             example_rgf_general_cfg_clk_en_hw_write_access ; // HW has write access condition
logic             example_rgf_general_cfg_clk_en_sw_we           ; // SW write enable
logic             example_rgf_general_cfg_clk_en_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_general_cfg_clk_en_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_general_cfg_clk_en_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_general_cfg_clk_en_sw_write_access = 1'b1 ; // SW write access is taken from field attribites
assign example_rgf_general_cfg_clk_en_hw_write_access = 1'b0 ; // HW write access is taken from field attribites
assign example_rgf_general_cfg_clk_en_sw_we = (paddr==ADD_W'(4)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_general_cfg_clk_en_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_general_cfg_clk_en_sw_next = pwdata[0+:1] & pstrb_mask[0+:1] ; // next value of SW is masked with APB's pstrb
assign example_rgf_general_cfg_clk_en_next = example_rgf_general_cfg_clk_en_sw_write_access & example_rgf_general_cfg_clk_en_sw_we     ? example_rgf_general_cfg_clk_en_sw_next : // write SW value
//                                   example_rgf_general_cfg_clk_en_hw_we_int & example_rgf_general_cfg_clk_en_hw_write_access ? example_rgf_general_cfg_clk_en_hw_next : // write HW value
                                                                                                                                               example_rgf_general_cfg_clk_en         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_general_cfg_clk_en <= 1'h0 ; 
    end
    else begin // sample next
        example_rgf_general_cfg_clk_en <= example_rgf_general_cfg_clk_en_next ; 
    end
end

// RGF: example_rgf, REG: general_cfg, REG_ADD: 0x20, FLD_NAME: clk_en, FLD_BITS 0:0 //
// ------------------------------------------------------------------------------------------------------------------ //


// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: general_cfg, REG_ADD: 0x20, FLD_NAME: rgb_mode, FLD_BITS 8:8 // 

// Internal Wires // 
logic             example_rgf_general_cfg_rgb_mode_sw_write_access ; // SW has write access condition
logic             example_rgf_general_cfg_rgb_mode_hw_write_access ; // HW has write access condition
logic             example_rgf_general_cfg_rgb_mode_sw_we           ; // SW write enable
logic             example_rgf_general_cfg_rgb_mode_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_general_cfg_rgb_mode_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_general_cfg_rgb_mode_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_general_cfg_rgb_mode_sw_write_access = 1'b1 ; // SW write access is taken from field attribites
assign example_rgf_general_cfg_rgb_mode_hw_write_access = 1'b0 ; // HW write access is taken from field attribites
assign example_rgf_general_cfg_rgb_mode_sw_we = (paddr==ADD_W'(4)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_general_cfg_rgb_mode_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_general_cfg_rgb_mode_sw_next = pwdata[8+:1] & pstrb_mask[8+:1] ; // next value of SW is masked with APB's pstrb
assign example_rgf_general_cfg_rgb_mode_next = example_rgf_general_cfg_rgb_mode_sw_write_access & example_rgf_general_cfg_rgb_mode_sw_we     ? example_rgf_general_cfg_rgb_mode_sw_next : // write SW value
//                                   example_rgf_general_cfg_rgb_mode_hw_we_int & example_rgf_general_cfg_rgb_mode_hw_write_access ? example_rgf_general_cfg_rgb_mode_hw_next : // write HW value
                                                                                                                                               example_rgf_general_cfg_rgb_mode         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_general_cfg_rgb_mode <= 1'h0 ; 
    end
    else begin // sample next
        example_rgf_general_cfg_rgb_mode <= example_rgf_general_cfg_rgb_mode_next ; 
    end
end

// RGF: example_rgf, REG: general_cfg, REG_ADD: 0x20, FLD_NAME: rgb_mode, FLD_BITS 8:8 //
// ------------------------------------------------------------------------------------------------------------------ //



logic [32-1:0] example_rgf_general_cfg ;
assign example_rgf_general_cfg = {example_rgf_general_cfg_clk_en, example_rgf_general_cfg_rgb_mode};


// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: loc_sts, REG_ADD: 0x40, FLD_NAME: col_ptr, FLD_BITS 15:0 // 

// Internal Wires // 
logic             example_rgf_loc_sts_col_ptr_sw_write_access ; // SW has write access condition
logic             example_rgf_loc_sts_col_ptr_hw_write_access ; // HW has write access condition
logic             example_rgf_loc_sts_col_ptr_sw_we           ; // SW write enable
logic             example_rgf_loc_sts_col_ptr_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_loc_sts_col_ptr_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_loc_sts_col_ptr_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_loc_sts_col_ptr_sw_write_access = 1'b0 ; // SW write access is taken from field attribites
assign example_rgf_loc_sts_col_ptr_hw_write_access = 1'b1 ; // HW write access is taken from field attribites
assign example_rgf_loc_sts_col_ptr_sw_we = (paddr==ADD_W'(8)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_loc_sts_col_ptr_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_loc_sts_col_ptr_sw_next = pwdata[0+:16] & pstrb_mask[0+:16] ; // next value of SW is masked with APB's pstrb
assign example_rgf_loc_sts_col_ptr_next = example_rgf_loc_sts_col_ptr_sw_write_access & example_rgf_loc_sts_col_ptr_sw_we     ? example_rgf_loc_sts_col_ptr_sw_next : // write SW value
                                     example_rgf_loc_sts_col_ptr_hw_we_int & example_rgf_loc_sts_col_ptr_hw_write_access ? example_rgf_loc_sts_col_ptr_hw_next : // write HW value
                                                                                                                                               example_rgf_loc_sts_col_ptr         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_loc_sts_col_ptr <= 16'h0 ; 
    end
    else begin // sample next
        example_rgf_loc_sts_col_ptr <= example_rgf_loc_sts_col_ptr_next ; 
    end
end

// RGF: example_rgf, REG: loc_sts, REG_ADD: 0x40, FLD_NAME: col_ptr, FLD_BITS 15:0 //
// ------------------------------------------------------------------------------------------------------------------ //


// ------------------------------------------------------------------------------------------------------------------ //
// RGF: example_rgf, REG: loc_sts, REG_ADD: 0x40, FLD_NAME: row_ptr, FLD_BITS 31:16 // 

// Internal Wires // 
logic             example_rgf_loc_sts_row_ptr_sw_write_access ; // SW has write access condition
logic             example_rgf_loc_sts_row_ptr_hw_write_access ; // HW has write access condition
logic             example_rgf_loc_sts_row_ptr_sw_we           ; // SW write enable
logic             example_rgf_loc_sts_row_ptr_hw_we_int       ; // internal HW write enable
logic [DAT_W-1:0] example_rgf_loc_sts_row_ptr_sw_next         ; // next value from SW side
logic [DAT_W-1:0] example_rgf_loc_sts_row_ptr_next            ; // actual next value for field

// Control Logic // 
assign example_rgf_loc_sts_row_ptr_sw_write_access = 1'b0 ; // SW write access is taken from field attribites
assign example_rgf_loc_sts_row_ptr_hw_write_access = 1'b1 ; // HW write access is taken from field attribites
assign example_rgf_loc_sts_row_ptr_sw_we = (paddr==ADD_W'(8)) & (apb_sts_curr==APB_WRITE) ; // FSM is @ Write State AND register address is selected
assign example_rgf_loc_sts_row_ptr_hw_we_int = 1'b1 ; // Internal HW we, can be an external port or 1'b1
assign example_rgf_loc_sts_row_ptr_sw_next = pwdata[16+:16] & pstrb_mask[16+:16] ; // next value of SW is masked with APB's pstrb
assign example_rgf_loc_sts_row_ptr_next = example_rgf_loc_sts_row_ptr_sw_write_access & example_rgf_loc_sts_row_ptr_sw_we     ? example_rgf_loc_sts_row_ptr_sw_next : // write SW value
                                     example_rgf_loc_sts_row_ptr_hw_we_int & example_rgf_loc_sts_row_ptr_hw_write_access ? example_rgf_loc_sts_row_ptr_hw_next : // write HW value
                                                                                                                                               example_rgf_loc_sts_row_ptr         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        example_rgf_loc_sts_row_ptr <= 16'h0 ; 
    end
    else begin // sample next
        example_rgf_loc_sts_row_ptr <= example_rgf_loc_sts_row_ptr_next ; 
    end
end

// RGF: example_rgf, REG: loc_sts, REG_ADD: 0x40, FLD_NAME: row_ptr, FLD_BITS 31:16 //
// ------------------------------------------------------------------------------------------------------------------ //



logic [32-1:0] example_rgf_loc_sts ;
assign example_rgf_loc_sts = {example_rgf_loc_sts_col_ptr, example_rgf_loc_sts_row_ptr};




// Output Mux // 
// ---------- // 
always_comb begin
   case (paddr) 
   ADD_W'(0): prdata = example_rgf_frame_dims ;
   ADD_W'(4): prdata = example_rgf_general_cfg ;
   ADD_W'(8): prdata = example_rgf_loc_sts ;
   
   endcase
end

endmodule
