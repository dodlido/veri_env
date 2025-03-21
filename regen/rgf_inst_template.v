// ------------------------------------ // 
// Automatically Generated RGF instance // 
// ------------------------------------ // 

{RGF_NAME} i_{RGF_NAME} ( 
   // General // 
   // ------- //
   .clk(clk),
   .rst_n(rst_n),
   
   // HW IF to RGF // 
   // ------------ //
{RGF_PORTS}
   // APB IF // 
   // ------ //
   .paddr(paddr),
   .pprot(pprot),
   .psel(psel),
   .penable(penable),
   .pwrite(pwrite),
   .pwdata(pwdata),
   .pstrb(pstrb),
   .pwakeup(pwakeup),
   .pready(pready),
   .prdata(prdata),
   .pslverr(pslverr)
);

// ------------------------------------ // 
// Automatically Generated RGF instance // 
// ------------------------------------ // 

//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
//|                                               |//
//| 1. Project  :  veri_env                       |//
//| 2. Author   :  Etay Sela                      |//
//| 3. Date     :  2025-01-09                     |//
//| 4. Version  :  v4.2.0                         |//
//|                                               |//
//|~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|//
