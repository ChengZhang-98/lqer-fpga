`timescale 1ns / 1ps

module skid_buffer #(
    parameter int DATA_WIDTH          = 8,
    parameter int CICULAR_BUFFER_MODE = 0
) (
    input  logic                  clk,
    input  logic                  rst,
    // input
    input  logic [DATA_WIDTH-1:0] data_in,
    input  logic                  valid_in,
    output logic                  ready_in,
    // output
    output logic [DATA_WIDTH-1:0] data_out,
    output logic                  valid_out,
    input  logic                  ready_out
);

endmodule
