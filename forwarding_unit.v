/*
 * Forwarding Unit
 * Detects data hazards and generates forwarding control signals
 * Forwards data from EX/MEM and MEM/WB stages to EX stage
 */

module forwarding_unit(
    // EX/MEM stage signals
    input wire ex_mem_reg_write,
    input wire [2:0] ex_mem_rd,
    
    // MEM/WB stage signals
    input wire mem_wb_reg_write,
    input wire [2:0] mem_wb_rd,
    
    // ID/EX stage signals
    input wire [2:0] id_ex_rs,
    input wire [2:0] id_ex_rt,
    
    // Forwarding control outputs
    output reg [1:0] forward_a,  // Forwarding control for operand A
    output reg [1:0] forward_b   // Forwarding control for operand B
);

    /*
     * Forwarding control values:
     * 00 = No forwarding (use register file data)
     * 01 = Forward from MEM/WB stage
     * 10 = Forward from EX/MEM stage
     */
    
    always @(*) begin
        // Default: no forwarding
        forward_a = 2'b00;
        forward_b = 2'b00;
        
        // ========== Forwarding for operand A (rs) ==========
        
        // EX/MEM forwarding (priority)
        if (ex_mem_reg_write && 
            (ex_mem_rd != 3'b000) && 
            (ex_mem_rd == id_ex_rs)) begin
            forward_a = 2'b10;
        end
        // MEM/WB forwarding
        else if (mem_wb_reg_write && 
                 (mem_wb_rd != 3'b000) && 
                 (mem_wb_rd == id_ex_rs)) begin
            forward_a = 2'b01;
        end
        
        // ========== Forwarding for operand B (rt) ==========
        
        // EX/MEM forwarding (priority)
        if (ex_mem_reg_write && 
            (ex_mem_rd != 3'b000) && 
            (ex_mem_rd == id_ex_rt)) begin
            forward_b = 2'b10;
        end
        // MEM/WB forwarding
        else if (mem_wb_reg_write && 
                 (mem_wb_rd != 3'b000) && 
                 (mem_wb_rd == id_ex_rt)) begin
            forward_b = 2'b01;
        end
    end

endmodule

