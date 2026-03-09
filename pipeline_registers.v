/*
 * Pipeline Register Modules
 * Stores data between pipeline stages
 */

// ==================== IF/ID Pipeline Register ====================
module if_id_register(
    input wire clk,
    input wire rst,
    input wire stall,               // Stall signal (freeze this register)
    input wire flush,               // Flush signal (clear this register)
    input wire [15:0] if_instruction,
    input wire [7:0] if_pc,
    output reg [15:0] id_instruction,
    output reg [7:0] id_pc,
    output reg valid
);

    always @(posedge clk or posedge rst) begin
        if (rst || flush) begin
            id_instruction <= 16'h0000;
            id_pc <= 8'h00;
            valid <= 1'b0;
        end else if (!stall) begin
            id_instruction <= if_instruction;
            id_pc <= if_pc;
            valid <= 1'b1;
        end
        // If stall, keep current values
    end

endmodule

// ==================== ID/EX Pipeline Register ====================
module id_ex_register(
    input wire clk,
    input wire rst,
    input wire flush,               // Flush signal
    
    // Control signals
    input wire id_reg_write,
    input wire id_mem_write,
    input wire id_mem_read,
    input wire [1:0] id_mem_to_reg,  // 2-bit
    input wire id_alu_src,
    input wire [1:0] id_reg_dst,     // 2-bit (NEW)
    input wire id_branch,
    input wire id_jump,
    input wire id_jump_reg,
    input wire [3:0] id_alu_control,
    
    // Data signals
    input wire [15:0] id_read_data1,
    input wire [15:0] id_read_data2,
    input wire [15:0] id_sign_ext_imm,
    input wire [2:0] id_rs,
    input wire [2:0] id_rt,
    input wire [2:0] id_rd,
    input wire [2:0] id_shamt,
    input wire [7:0] id_pc,
    input wire [11:0] id_jump_addr,
    input wire [3:0] id_opcode,
    
    // Outputs
    output reg ex_reg_write,
    output reg ex_mem_write,
    output reg ex_mem_read,
    output reg [1:0] ex_mem_to_reg,  // 2-bit
    output reg ex_alu_src,
    output reg [1:0] ex_reg_dst,     // 2-bit (NEW)
    output reg ex_branch,
    output reg ex_jump,
    output reg ex_jump_reg,
    output reg [3:0] ex_alu_control,
    output reg [15:0] ex_read_data1,
    output reg [15:0] ex_read_data2,
    output reg [15:0] ex_sign_ext_imm,
    output reg [2:0] ex_rs,
    output reg [2:0] ex_rt,
    output reg [2:0] ex_rd,
    output reg [2:0] ex_shamt,
    output reg [7:0] ex_pc,
    output reg [11:0] ex_jump_addr,
    output reg [3:0] ex_opcode,
    output reg valid
);

    always @(posedge clk or posedge rst) begin
        if (rst || flush) begin
            ex_reg_write <= 1'b0;
            ex_mem_write <= 1'b0;
            ex_mem_read <= 1'b0;
            ex_mem_to_reg <= 2'b00;
            ex_alu_src <= 1'b0;
            ex_reg_dst <= 2'b00;
            ex_branch <= 1'b0;
            ex_jump <= 1'b0;
            ex_jump_reg <= 1'b0;
            ex_alu_control <= 4'h0;
            ex_read_data1 <= 16'h0000;
            ex_read_data2 <= 16'h0000;
            ex_sign_ext_imm <= 16'h0000;
            ex_rs <= 3'b000;
            ex_rt <= 3'b000;
            ex_rd <= 3'b000;
            ex_shamt <= 3'b000;
            ex_pc <= 8'h00;
            ex_jump_addr <= 12'h000;
            ex_opcode <= 4'h0;
            valid <= 1'b0;
        end else begin
            ex_reg_write <= id_reg_write;
            ex_mem_write <= id_mem_write;
            ex_mem_read <= id_mem_read;
            ex_mem_to_reg <= id_mem_to_reg;
            ex_alu_src <= id_alu_src;
            ex_reg_dst <= id_reg_dst;
            ex_branch <= id_branch;
            ex_jump <= id_jump;
            ex_jump_reg <= id_jump_reg;
            ex_alu_control <= id_alu_control;
            ex_read_data1 <= id_read_data1;
            ex_read_data2 <= id_read_data2;
            ex_sign_ext_imm <= id_sign_ext_imm;
            ex_rs <= id_rs;
            ex_rt <= id_rt;
            ex_rd <= id_rd;
            ex_shamt <= id_shamt;
            ex_pc <= id_pc;
            ex_jump_addr <= id_jump_addr;
            ex_opcode <= id_opcode;
            valid <= 1'b1;
        end
    end

endmodule

// ==================== EX/MEM Pipeline Register ====================
module ex_mem_register(
    input wire clk,
    input wire rst,
    
    // Control signals
    input wire ex_reg_write,
    input wire ex_mem_write,
    input wire ex_mem_read,
    input wire [1:0] ex_mem_to_reg,  // 2-bit
    input wire [1:0] ex_reg_dst,     // 2-bit (NEW)
    
    // Data signals
    input wire [15:0] ex_alu_result,
    input wire [15:0] ex_write_data,
    input wire [2:0] ex_write_reg,  // GÜNCELLEND İ: ex_rd yerine ex_write_reg (seçilmiş hedef)
    input wire [7:0] ex_pc,         // EKLENDİ: JAL için PC taşıma
    input wire ex_zero,
    
    // Outputs
    output reg mem_reg_write,
    output reg mem_mem_write,
    output reg mem_mem_read,
    output reg [1:0] mem_mem_to_reg,  // 2-bit
    output reg [1:0] mem_reg_dst,     // 2-bit (NEW)
    output reg [15:0] mem_alu_result,
    output reg [15:0] mem_write_data,
    output reg [2:0] mem_write_reg,  // GÜNCELLEND İ: mem_rd yerine mem_write_reg
    output reg [7:0] mem_pc,         // EKLENDİ: JAL için PC taşıma
    output reg mem_zero,
    output reg valid
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            mem_reg_write <= 1'b0;
            mem_mem_write <= 1'b0;
            mem_mem_read <= 1'b0;
            mem_mem_to_reg <= 2'b00;
            mem_reg_dst <= 2'b00;
            mem_alu_result <= 16'h0000;
            mem_write_data <= 16'h0000;
            mem_write_reg <= 3'b000;  // GÜNCELLEND İ
            mem_pc <= 8'h00;
            mem_zero <= 1'b0;
            valid <= 1'b0;
        end else begin
            mem_reg_write <= ex_reg_write;
            mem_mem_write <= ex_mem_write;
            mem_mem_read <= ex_mem_read;
            mem_mem_to_reg <= ex_mem_to_reg;
            mem_reg_dst <= ex_reg_dst;
            mem_alu_result <= ex_alu_result;
            mem_write_data <= ex_write_data;
            mem_write_reg <= ex_write_reg;  // GÜNCELLEND İ
            mem_pc <= ex_pc;
            mem_zero <= ex_zero;
            valid <= 1'b1;
        end
    end

endmodule

// ==================== MEM/WB Pipeline Register ====================
module mem_wb_register(
    input wire clk,
    input wire rst,
    
    // Control signals
    input wire mem_reg_write,
    input wire [1:0] mem_mem_to_reg,  // 2-bit
    input wire [1:0] mem_reg_dst,     // 2-bit (NEW)
    
    // Data signals
    input wire [15:0] mem_read_data,
    input wire [15:0] mem_alu_result,
    input wire [2:0] mem_write_reg,  // GÜNCELLEND İ: mem_rd yerine mem_write_reg
    input wire [7:0] mem_pc,         // EKLENDİ: JAL için PC taşıma
    
    // Outputs
    output reg wb_reg_write,
    output reg [1:0] wb_mem_to_reg,  // 2-bit
    output reg [1:0] wb_reg_dst,     // 2-bit (NEW)
    output reg [15:0] wb_read_data,
    output reg [15:0] wb_alu_result,
    output reg [2:0] wb_write_reg,   // GÜNCELLEND İ: wb_rd yerine wb_write_reg
    output reg [7:0] wb_pc,          // EKLENDİ: JAL için PC taşıma
    output reg valid
);

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            wb_reg_write <= 1'b0;
            wb_mem_to_reg <= 2'b00;
            wb_reg_dst <= 2'b00;
            wb_read_data <= 16'h0000;
            wb_alu_result <= 16'h0000;
            wb_write_reg <= 3'b000;  // GÜNCELLEND İ
            wb_pc <= 8'h00;
            valid <= 1'b0;
        end else begin
            wb_reg_write <= mem_reg_write;
            wb_mem_to_reg <= mem_mem_to_reg;
            wb_reg_dst <= mem_reg_dst;
            wb_read_data <= mem_read_data;
            wb_alu_result <= mem_alu_result;
            wb_write_reg <= mem_write_reg;  // GÜNCELLEND İ
            wb_pc <= mem_pc;
            valid <= 1'b1;
        end
    end

endmodule

