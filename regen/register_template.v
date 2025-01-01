// RGF: {RGF_NAME}, REG: {REG_NAME}, REG_ADD: {REG_HEX_ADD}, FLD_NAME: {FLD_NAME}, FLD_BITS {FLD_ENDBIT}:{FLD_OFFSET} // 

// Internal Wires // 
logic                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_write_access ; // SW has write access condition
logic                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_write_access ; // HW has write access condition
logic                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_we           ; // SW write enable
logic                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_we_int       ; // internal HW write enable
logic                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_latch           ; // latch on to 1's (for interrupts)
logic [{FLD_WIDTH}-1:0] {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_next         ; // next value from SW side
logic [{FLD_WIDTH}-1:0] {RGF_NAME}_{REG_NAME}_{FLD_NAME}_next            ; // actual next value for field
{MASK_HW_RD} logic [{FLD_WIDTH}-1:0] {RGF_NAME}_{REG_NAME}_{FLD_NAME}    ; // actual next value for field

// Control Logic // 
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_write_access = {FLD_SW_WR} ; // SW write access is taken from field attribites
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_write_access = {FLD_HW_WR} ; // HW write access is taken from field attribites
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_we = (|(pstrb_mask[{FLD_OFFSET}+:{FLD_WIDTH}])) & (paddr=={REG_ADD}) & ((apb_sts_curr==APB_WRITE) | ({LATCH} & apb_sts_curr==APB_READ)) ; // FSM is @ Write State AND register address is selected
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_latch = {LATCH} & (|({RGF_NAME}_{REG_NAME}_{FLD_NAME})) ; // Latch on to 1's --> interrupt functionality
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_we_int = {FLD_HW_WE_INT} & ~{RGF_NAME}_{REG_NAME}_{FLD_NAME}_latch; // Internal HW we, can be an external port or 1'b1
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_next = pwdata[{FLD_OFFSET}+:{FLD_WIDTH}] & pstrb_mask[{FLD_OFFSET}+:{FLD_WIDTH}] ; // next value of SW is masked with APB's pstrb
assign {RGF_NAME}_{REG_NAME}_{FLD_NAME}_next = {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_write_access & {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_we     ? {RGF_NAME}_{REG_NAME}_{FLD_NAME}_sw_next : // write SW value
{MASK_HW_WR}                                   {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_we_int & {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_write_access ? {RGF_NAME}_{REG_NAME}_{FLD_NAME}_hw_next : // write HW value
                                                                                                                                               {RGF_NAME}_{REG_NAME}_{FLD_NAME}         ; // keep current state

// FF // 
always_ff @(posedge clk) begin
    if (!rst_n) begin // reset
        {RGF_NAME}_{REG_NAME}_{FLD_NAME} <= {FLD_RST_VAL} ; 
    end
    else begin // sample next
        {RGF_NAME}_{REG_NAME}_{FLD_NAME} <= {RGF_NAME}_{REG_NAME}_{FLD_NAME}_next ; 
    end
end

// RGF: {RGF_NAME}, REG: {REG_NAME}, REG_ADD: {REG_HEX_ADD}, FLD_NAME: {FLD_NAME}, FLD_BITS {FLD_ENDBIT}:{FLD_OFFSET} //
