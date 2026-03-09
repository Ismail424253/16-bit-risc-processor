/*
 * Defines Header File
 * Common definitions and parameters for the RISC processor
 */

`ifndef DEFINES_VH
`define DEFINES_VH

// ==================== Opcode Definitions ====================
`define OP_ADD  4'h0    // R-Type: Add
`define OP_SUB  4'h1    // R-Type: Subtract
`define OP_AND  4'h2    // R-Type: Logical AND
`define OP_OR   4'h3    // R-Type: Logical OR
`define OP_SLT  4'h4    // R-Type: Set Less Than
`define OP_SLL  4'h5    // R-Type: Shift Left Logical
`define OP_SRL  4'h6    // R-Type: Shift Right Logical
`define OP_ADDI 4'h7    // I-Type: Add Immediate
`define OP_LW   4'h8    // I-Type: Load Word
`define OP_SW   4'h9    // I-Type: Store Word
`define OP_BEQ  4'hA    // I-Type: Branch if Equal
`define OP_BNE  4'hB    // I-Type: Branch if Not Equal
`define OP_J    4'hC    // J-Type: Jump
`define OP_JAL  4'hD    // J-Type: Jump and Link
`define OP_JR   4'hE    // R-Type: Jump Register
`define OP_NOP  4'hF    // No Operation

// ==================== ALU Control Codes ====================
`define ALU_ADD  4'h0
`define ALU_SUB  4'h1
`define ALU_AND  4'h2
`define ALU_OR   4'h3
`define ALU_SLT  4'h4
`define ALU_SLL  4'h5
`define ALU_SRL  4'h6

// ==================== Register Definitions ====================
`define REG_R0  3'b000  // Always 0
`define REG_R1  3'b001
`define REG_R2  3'b010
`define REG_R3  3'b011
`define REG_R4  3'b100
`define REG_R5  3'b101
`define REG_R6  3'b110
`define REG_R7  3'b111  // Link register for JAL

// ==================== Control Signal Values ====================
// MemToReg values
`define MEM_TO_REG_ALU  2'b00   // Select ALU result
`define MEM_TO_REG_MEM  2'b01   // Select memory data
`define MEM_TO_REG_PC   2'b10   // Select PC+1 (for JAL)

// RegDst values
`define REG_DST_RT      2'b00   // Select rt (I-Type)
`define REG_DST_RD      2'b01   // Select rd (R-Type)
`define REG_DST_R7      2'b10   // Select R7 (JAL)

// Forwarding control values
`define FWD_NONE        2'b00   // No forwarding
`define FWD_MEM_WB      2'b01   // Forward from MEM/WB
`define FWD_EX_MEM      2'b10   // Forward from EX/MEM

// ==================== Memory Sizes ====================
`define IMEM_SIZE       256     // Instruction memory: 256 words
`define DMEM_SIZE       256     // Data memory: 256 words
`define REGFILE_SIZE    8       // Register file: 8 registers
`define DATA_WIDTH      16      // Data width: 16 bits
`define ADDR_WIDTH      8       // Address width: 8 bits

// ==================== Instruction Format Bit Positions ====================
// 16-bit instruction format: [opcode(4)][field1(3)][field2(3)][field3(6)]

// Opcode field
`define OPCODE_MSB      15
`define OPCODE_LSB      12

// R-Type: [opcode(4)][rs(3)][rt(3)][rd(3)][shamt(3)]
`define R_RS_MSB        11
`define R_RS_LSB        9
`define R_RT_MSB        8
`define R_RT_LSB        6
`define R_RD_MSB        5
`define R_RD_LSB        3
`define R_SHAMT_MSB     2
`define R_SHAMT_LSB     0

// I-Type: [opcode(4)][rs(3)][rt(3)][immediate(6)]
`define I_RS_MSB        11
`define I_RS_LSB        9
`define I_RT_MSB        8
`define I_RT_LSB        6
`define I_IMM_MSB       5
`define I_IMM_LSB       0

// J-Type: [opcode(4)][address(12)]
`define J_ADDR_MSB      11
`define J_ADDR_LSB      0

`endif // DEFINES_VH

