/*
 * Register File Module
 * 8 registers (R0-R7), 16-bit width
 * R0 is hardwired to 0
 * Supports Internal Forwarding (Solve WB hazard)
 */

module register_file(
    input  wire        clk,
    input  wire        rst,
    input  wire        reg_write,           // Write enable
    input  wire [2:0]  read_reg1,           // Read register 1 address
    input  wire [2:0]  read_reg2,           // Read register 2 address
    input  wire [2:0]  write_reg,           // Write register address
    input  wire [15:0] write_data,          // Data to write
    output wire [15:0] read_data1,          // Data from register 1
    output wire [15:0] read_data2,          // Data from register 2
    output wire [15:0] dbg_r1,              // Debug: R1 value
    output wire [15:0] dbg_r2               // Debug: R2 value
);

    reg [15:0] registers [0:7];

    integer i;
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) begin
                registers[i] <= 16'h0000;
            end
        end else begin
            if (reg_write && write_reg != 3'b000) begin
                registers[write_reg] <= write_data;
            end
            registers[0] <= 16'h0000;
        end
    end

    // Internal forwarding on reads
    assign read_data1 = (read_reg1 == 3'b000) ? 16'h0000 :
                        (reg_write && (read_reg1 == write_reg)) ? write_data :
                        registers[read_reg1];

    assign read_data2 = (read_reg2 == 3'b000) ? 16'h0000 :
                        (reg_write && (read_reg2 == write_reg)) ? write_data :
                        registers[read_reg2];

    assign dbg_r1 = registers[1];
    assign dbg_r2 = registers[2];

endmodule
