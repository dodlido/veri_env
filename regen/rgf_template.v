module {RGF_NAME} #(
   // Parameters // 
   // ---------- // 
   parameter DAT_W  = {RGF_REG_WIDTH} , 
   parameter ADD_W  = {RGF_ADD_WIDTH} , 
   parameter STRB_W = $clog2(DAT_W/8)
) (
   // General //
   // ------- //
   input logic clk ,
   input logic rst_n , 
   // HW IF to registers //
   // ------------------ // 
   {HW_RGF_PORTS}
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
{RGF_CONTENT}

// Output Mux // 
// ---------- // 
always_comb begin
   case (paddr) 
   {OUTPUT_MUX}
   endcase
end

endmodule
