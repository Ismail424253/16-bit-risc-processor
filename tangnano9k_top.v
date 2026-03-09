module tangnano9k_top (
    input  wire       clk_27m,
    input  wire       btn1_n,     // active-low
    output wire [5:0] led         // active-low LEDs
);

    wire rst = ~btn1_n;

    // 27 MHz -> CPU clock ~1 Hz (posedge each ~1s)
    reg [23:0] div_cnt = 24'd0;
    reg        clk_cpu = 1'b0;

    always @(posedge clk_27m or posedge rst) begin
        if (rst) begin
            div_cnt <= 24'd0;
            clk_cpu <= 1'b0;
        end else begin
            if (div_cnt == 24'd13_500_000 - 1) begin
                div_cnt <= 24'd0;
                clk_cpu <= ~clk_cpu;
            end else begin
                div_cnt <= div_cnt + 1'b1;
            end
        end
    end

    wire [7:0]  pc_out;
    wire [15:0] instruction_out;
    wire        stall_out;
    wire [31:0] cycle_count;
    wire [15:0] dbg_r1;
    wire [15:0] dbg_r2;

    processor_top u_cpu (
        .clk             (clk_cpu),
        .rst             (rst),
        .pc_out          (pc_out),
        .instruction_out (instruction_out),
        .stall_out       (stall_out),
        .cycle_count     (cycle_count),
        .dbg_r1          (dbg_r1),
        .dbg_r2          (dbg_r2)
    );

    // LED'de R2'nin alt 6 bitini göster (aktif-low)
    assign led = ~dbg_r2[5:0];

endmodule
