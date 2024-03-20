/*
Module      :simple_matmul
Description :This module does a matrix multiply of two input matrices a and b, and stores the result in out.

             The dimensions of the input matrices are specified by the parameters M, N, and K:
             (M, N) * (N, K) = (M, K)

             Python equivalent: out = a @ b
*/

`include "timescale.svh"

module simple_matmul #(
    // Dimensions
    parameter int M              = 2,
    parameter int N              = 2,
    parameter int K              = 2,
    // Input fixed-point formats
    parameter int A_WIDTH        = 8,
    parameter int A_FRAC_WIDTH   = 1,
    parameter int B_WIDTH        = 8,
    parameter int B_FRAC_WIDTH   = 1,
    // Output fixed-point format
    // if ROUND_OUPTUT is set to 0,
    // then (OUT_WIDTH, OUT_FRAC_WIDTH) must match accumulator widths
    parameter int ROUND_OUPTUT   = 1,
    parameter int OUT_WIDTH      = 16,
    parameter int OUT_FRAC_WIDTH = 1
) (
    input logic clk,
    input logic rst

    // Input matrices, row-major order


    // Input matrices, row-major order


    // Output matrix, row-major order
);



endmodule
