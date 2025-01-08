// ------------------------------------ // 
// Automatically Generated RGF instance // 
// ------------------------------------ // 

example_rgf i_example_rgf ( 
   // General // 
   // ------- //
   .clk(clk),
   .rst_n(rst_n),
   
   // HW IF to RGF // 
   // ------------ //
   .example_rgf_frame_dims_n_col(example_rgf_frame_dims_n_col), // example_rgf_frame_dims_n_col: HW read port , output(16b)
   .example_rgf_frame_dims_n_row(example_rgf_frame_dims_n_row), // example_rgf_frame_dims_n_row: HW read port , output(16b)
   .example_rgf_general_cfg_clk_en(example_rgf_general_cfg_clk_en), // example_rgf_general_cfg_clk_en: HW read port , output(1b)
   .example_rgf_general_cfg_rgb_mode(example_rgf_general_cfg_rgb_mode), // example_rgf_general_cfg_rgb_mode: HW read port , output(1b)
   .example_rgf_loc_sts_col_ptr(example_rgf_loc_sts_col_ptr), // example_rgf_loc_sts_col_ptr: HW read port , output(16b)
   .example_rgf_loc_sts_col_ptr_hw_next(example_rgf_loc_sts_col_ptr_hw_next), // example_rgf_loc_sts_col_ptr: HW write port , input(16b)
   .example_rgf_loc_sts_row_ptr(example_rgf_loc_sts_row_ptr), // example_rgf_loc_sts_row_ptr: HW read port , output(16b)
   .example_rgf_loc_sts_row_ptr_hw_next(example_rgf_loc_sts_row_ptr_hw_next), // example_rgf_loc_sts_row_ptr: HW write port , input(16b)

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
