/*
  Module:       register_slice
  Description:  A register array holding DATA_WIDTH bits. When clk_en is 0, output RESET_VALUE.
*/

`include "timescale.svh"

module register_slice #(
    parameter int DATA_WIDTH  = 1,
    parameter int RESET_VALUE = 0
) (
    input  logic                  clk,
    input  logic                  clk_en,
    input  logic                  rst,
    // input and output
    input  logic [DATA_WIDTH-1:0] data_in,
    output logic [DATA_WIDTH-1:0] data_out
);
    /*
    data_out = clk_en? data_next: RESET_VALUE
    */
    logic [DATA_WIDTH-1:0] data_reg, data_next;

    initial begin
        data_reg = RESET_VALUE[DATA_WIDTH-1:0];
    end

    // next state logic
    always_comb begin : next_state
        if (clk_en == 1'b1) begin
            data_next = data_in;
        end else begin
            data_next = data_reg;
        end
    end

    // register state transfer
    always @(posedge clk) begin
        if (rst) begin
            // verilator lint_off WIDTHEXPAND
            // verilator lint_off WIDTHTRUNC
            data_reg <= RESET_VALUE;
            // verilator lint_on WIDTHTRUNC
            // verilator lint_on WIDTHEXPAND
        end else begin
            data_reg <= data_next;
        end
    end

    // next state logic
    assign data_out = data_reg;
endmodule
