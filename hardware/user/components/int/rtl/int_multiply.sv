`timescale 1ns / 1ps
/*
    Module:         int_multiply
    Description:    Multiplies two input signed fixed-point numbers a and b, and outputs the signed product.
                    No rounding is performed.
*/
module int_multiply #(
    parameter int A_WIDTH = 8,
    parameter int B_WIDTH = 8
) (
    input logic signed [A_WIDTH-1:0] a,
    input logic signed [B_WIDTH-1:0] b,
    output logic signed [A_WIDTH+B_WIDTH-1:0] out
);
    assign out = a * b;
endmodule
