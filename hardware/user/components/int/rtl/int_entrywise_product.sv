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
    input  logic signed [A_WIDTH-1:0] data_in_a [A_DIM_0_B_DIM_0],
    input  logic                      valid_in_a,
    output logic                      ready_in_a,
    input  logic signed [B_WIDTH-1:0] data_in_b [A_DIM_0_B_DIM_0],
    input  logic                      valid_in_b,
    output logic                      ready_in_b,

    // Ouptut array
    output logic signed [OutWidth-1:0] data_out [A_DIM_0_B_DIM_0],
    output logic                       valid_out,
    input  logic                       ready_out
);

    logic [OutWidth-1:0] product[A_DIM_0_B_DIM_0];

    for (genvar i = 0; i < A_DIM_0_B_DIM_0; i++) begin : gen_entrywise_product
        int_multiply #(
            .A_WIDTH(A_WIDTH),
            .B_WIDTH(B_WIDTH)
        ) int_mult_inst (
            .a  (data_in_a[i]),
            .b  (data_in_b[i]),
            .out(product[i])
        );
    end

    logic product_valid, product_ready;
    join2 #() join2_inst (
        .valid_in_a(valid_in_a),
        .ready_in_a(ready_in_a),
        .valid_in_b(valid_in_b),
        .ready_in_b(ready_in_b),
        .valid_out (product_valid),
        .ready_out (product_ready)
    );

    // pipeline register
    // flatten product for skid buffer
    logic [$bits(product)-1:0] flat_product, flat_data_out;
    for (genvar i = 0; i < A_DIM_0_B_DIM_0; i++) begin : gen_flat_product_for_join
        assign flat_product[(i+1)*OutWidth-1:i*OutWidth] = product[i];
    end
    skid_buffer #(
        .DATA_WIDTH          ($bits(product)),
        .CIRCULAR_BUFFER_MODE(0)
    ) skid_buffer_inst (
        .clk      (clk),
        .rst      (rst),
        .data_in  (flat_product),
        .valid_in (product_valid),
        .ready_in (product_ready),
        .data_out (flat_data_out),
        .valid_out(valid_out),
        .ready_out(ready_out)
    );
    // unflatten/rewire skid_buffer output to data_out
    for (genvar i = 0; i < A_DIM_0_B_DIM_0; i++) begin : gen_output_riwire
        assign data_out[i] = flat_data_out[(i+1)*OutWidth-1:i*OutWidth];
    end

endmodule


