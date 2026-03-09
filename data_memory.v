/*
 * Data Memory Module (byte-addressable, FPGA-friendly)
 * - Two 8-bit banks: even/odd bytes (little-endian)
 * - 16-bit word accesses are auto-aligned (address[0] ignored)
 * - Combinational read, synchronous write
 */

module data_memory(
    input  wire        clk,
    input  wire        mem_write,
    input  wire        mem_read,
    input  wire [7:0]  address,      // byte address
    input  wire [15:0] write_data,   // 16-bit store data
    output wire [15:0] read_data     // 16-bit load data
);

    // word index (auto alignment): address[0] ignored
    wire [6:0] word_index = address[7:1];

    // Total capacity here: 128 words * 2 bytes = 256 bytes address space (0x00..0xFF aligned words)
    // even_bytes[word_index] holds byte at aligned address (..0)
    // odd_bytes[word_index]  holds byte at aligned address+1 (..1)
    reg [7:0] even_bytes [0:127];
    reg [7:0] odd_bytes  [0:127];

    integer i;
    initial begin
        for (i = 0; i < 128; i = i + 1) begin
            even_bytes[i] = 8'h00;
            odd_bytes[i]  = 8'h00;
        end
    end

    // Synchronous write (store 16-bit little-endian)
    always @(posedge clk) begin
        if (mem_write) begin
            even_bytes[word_index] <= write_data[7:0];    // low byte
            odd_bytes[word_index]  <= write_data[15:8];   // high byte
        end
    end

    // Combinational read (load 16-bit little-endian)
    // Write-through bypass: if same cycle mem_write+mem_read, show write_data
    assign read_data = (mem_read) ?
                        (mem_write ? write_data : {odd_bytes[word_index], even_bytes[word_index]})
                       : 16'h0000;

endmodule

