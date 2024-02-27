`timescale 1us / 1ps
/*
  Module:       register_slice
  Description:  A register array holding DATA_WIDTH bits. When clk_en is 0, output RESET_VALUE.
*/

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
        // verilator lint_off WIDTHTRUNC
        data_reg = RESET_VALUE;
        // verilator lint_on WIDTHTRUNC
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
    always_ff @(posedge clk) begin
        if (rst) begin
            // verilator lint_off WIDTHTRUNC
            data_reg <= RESET_VALUE;
            // verilator lint_on WIDTHTRUNC
        end else begin
            data_reg <= data_next;
        end
    end

    // next state logic
    assign data_out = data_reg;
endmodule
