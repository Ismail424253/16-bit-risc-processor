module instruction_memory(
    input  wire [7:0]  address,
    output wire [15:0] instruction
);

    reg [15:0] memory [0:255];
    integer i;

    initial begin
        for (i = 0; i < 256; i = i + 1) begin
            memory[i] = 16'hF000; // NOP
        end
        $readmemh("program.hex", memory);
    end

    assign instruction = memory[address];

endmodule
