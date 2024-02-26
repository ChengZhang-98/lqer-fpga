`timescale 1ns / 1ps
/*
Module:         int_entrywise_product
Description:    Entrywise (elementwise) product of two input fixed-point arrays a and b.
                No rounding is performed.
Parameters:
                A_WIDTH:        The width of the input array a elements.
                B_WIDTH:        The width of the input array b elements.
                A_DIM_0_B_DIM_0: The number of elements in the input array a, (= the number of elements in the input array b)
*/
module int_entrywise_product #(
    parameter  int A_WIDTH         = 8,
    parameter  int B_WIDTH         = 8,
    // the number of elements in the input array a,
    // (= the number of elements in the input array b)
    parameter  int A_DIM_0_B_DIM_0 = 8,
    localparam int OutWidth        = A_WIDTH + B_WIDTH
) (
    input logic clk,
    input logic rst,

    // Input arrays
    input logic signed [A_WIDTH-1:0] a[A_DIM_0_B_DIM_0],
    input logic a_valid,
    input logic a_ready,
    input logic signed [B_WIDTH-1:0] b[A_DIM_0_B_DIM_0],
    input logic b_valid,
    input logic b_ready,

    // Ouptut array
    output logic signed [OutWidth-1:0] out[A_DIM_0_B_DIM_0],
    output logic out_valid,
    input logic out_ready
);

  logic [OutWidth-1:0] product[A_DIM_0_B_DIM_0];

  for (genvar i = 0; i < A_DIM_0_B_DIM_0; i++) begin : gen_entrywise_product
    int_multiply #(
        .A_WIDTH(A_WIDTH),
        .B_WIDTH(B_WIDTH)
    ) int_mult_inst (
        .a  (a[i]),
        .b  (b[i]),
        .out(product[i])
    );
  end

endmodule


