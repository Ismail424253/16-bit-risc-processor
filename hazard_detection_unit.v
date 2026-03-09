/*
 * Hazard Detection Unit
 * Detects load-use hazards and generates stall signals
 * Monitors ID/EX stage for LW instructions that create data dependencies
 */

module hazard_detection_unit(
    input wire id_ex_mem_read,      // ID/EX stage is doing a load
    input wire [2:0] id_ex_rt,      // Destination register of load
    input wire [2:0] if_id_rs,      // Source register 1 in decode stage
    input wire [2:0] if_id_rt,      // Source register 2 in decode stage
    input wire [3:0] if_id_opcode,  // Opcode of instruction in decode stage
    output reg stall,               // Stall signal (freeze IF and ID stages)
    output reg if_id_write,         // IF/ID register write enable
    output reg pc_write             // PC write enable
);

    // Opcode definitions for checking instruction type - CORRECTED to match Python backend
    localparam OP_LW   = 4'h0;  // 0b0000 - Load Word
    localparam OP_SW   = 4'h1;  // 0b0001 - Store Word
    localparam OP_ADD  = 4'h2;  // 0b0010 - Add
    localparam OP_SUB  = 4'h3;  // 0b0011 - Subtract
    localparam OP_AND  = 4'h4;  // 0b0100 - Bitwise AND
    localparam OP_OR   = 4'h5;  // 0b0101 - Bitwise OR
    localparam OP_SLT  = 4'h6;  // 0b0110 - Set Less Than
    localparam OP_SLL  = 4'h7;  // 0b0111 - Shift Left Logical
    localparam OP_SRL  = 4'h8;  // 0b1000 - Shift Right Logical
    localparam OP_ADDI = 4'h9;  // 0b1001 - Add Immediate
    localparam OP_BEQ  = 4'hA;  // 0b1010 - Branch if Equal
    localparam OP_BNE  = 4'hB;  // 0b1011 - Branch if Not Equal
    localparam OP_JR   = 4'hE;  // 0b1110 - Jump Register
    
    always @(*) begin
        // Default: no stall
        stall = 1'b0;
        if_id_write = 1'b1;
        pc_write = 1'b1;
        
        // Detect load-use hazard
        if (id_ex_mem_read && id_ex_rt != 3'b000) begin
            case (if_id_opcode)
                // R-type: check both rs and rt
                OP_ADD, OP_SUB, OP_AND, OP_OR, OP_SLT: begin
                    if (id_ex_rt == if_id_rs || id_ex_rt == if_id_rt) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;  // Freeze IF/ID
                        pc_write = 1'b0;     // Freeze PC
                    end
                end
                
                // Shift: check rt only
                OP_SLL, OP_SRL: begin
                    if (id_ex_rt == if_id_rt) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;
                        pc_write = 1'b0;
                    end
                end
                
                // ADDI: check rs
                OP_ADDI: begin
                    if (id_ex_rt == if_id_rs) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;
                        pc_write = 1'b0;
                    end
                end
                
                // Branch: check both rs and rt
                OP_BEQ, OP_BNE: begin
                    if (id_ex_rt == if_id_rs || id_ex_rt == if_id_rt) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;
                        pc_write = 1'b0;
                    end
                end
                
                // LW/SW: check base register (rs)
                OP_LW, OP_SW: begin
                    if (id_ex_rt == if_id_rs) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;
                        pc_write = 1'b0;
                    end
                end
                
                // JR: check rs
                OP_JR: begin
                    if (id_ex_rt == if_id_rs) begin
                        stall = 1'b1;
                        if_id_write = 1'b0;
                        pc_write = 1'b0;
                    end
                end
                
                default: begin
                    // No hazard
                end
            endcase
        end
    end

endmodule

