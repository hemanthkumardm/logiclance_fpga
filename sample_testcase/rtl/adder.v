module adder (
    input wire clk,
    input wire [31:0] a,
    input wire [31:0] b,
    output reg [31:0] sum
);
    always @(posedge clk) begin
        sum <= a + b;
    end
endmodule
