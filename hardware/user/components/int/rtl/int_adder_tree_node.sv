`include "timescale.svh"

module int_adder_tree_node #(
    parameter int IN_BITS         = 16,
    parameter int OUT_BITS        = 17,
    parameter int SIGN_EXT        = 1,
    parameter int REGISTER_MIDDLE = 0,
    parameter int REGISTER_OUTPUT = 1
) (
    input  logic                clk,
    input  logic                rst,
    input  logic [ IN_BITS-1:0] a,
    input  logic [ IN_BITS-1:0] b,
    output logic [OUT_BITS-1:0] out
);
    // for the placement of the midway pipeline registers
    localparam int LSWidth = OUT_BITS / 2;
    localparam int MSWidth = OUT_BITS - LSWidth;

    logic [OUT_BITS-1:0] a_ext, b_ext;

    // sign extension
    generate
        if (SIGN_EXT != 0) begin : gen_sign_extension
            assign a_ext = {{(OUT_BITS - IN_BITS) {a[IN_BITS-1]}}, a};
            assign b_ext = {{(OUT_BITS - IN_BITS) {b[IN_BITS-1]}}, b};
        end else begin : gen_no_sign_extension
            assign a_ext = {{(OUT_BITS - IN_BITS) {1'b0}}, a};
            assign b_ext = {{(OUT_BITS - IN_BITS) {1'b0}}, b};
        end
    endgenerate

    // addition
    logic [OUT_BITS-1:0] sum;
    generate
        /*
        When (REGISTER_MIDDLE !=0) is true,
        Enable pipeline in the middle of the adder chain

        Pipeline the carry in addition
        by splitting addition operator into most significant (MS) part and least significant part (LS)

        REGISTER_MIDDLE == 1
            a/b: xxxxx_xxxx
                 ----- ----
                 MS    LS

            Pipeline Stage 1: calculate LS_a + LS_b and the carry bit
                reg_ls_adder <= {1'b0,LS_a} + {1'b0,LS_b}
                cross_carry = MSB of reg_ls_adder

            Pipeline Stage 2: register sign extended MS_a and MS_b, do the sum
                reg_ms_data_a <= $sign_ext(MS_a)
                reg_ms_data_b <= $sign_ext(MS_b)

            Output logic: Note that the sum discards the LSB, which was only used for holding cross_carry
                ms_adder = {reg_ms_data_a, cross_carry} + {reg_ms_data_b, cross_carry}
                sum = {ms_adder[MSWidth:1], reg_ls_adder[LSWidth-1:0]}
        REGISTER_MIDDLE == 0
                sum = $sign_ext(a) + $sign_ext(b)
        */
        if (REGISTER_MIDDLE != 0) begin : gen_register_middle
            logic [LSWidth-1+1:0] ls_adder;
            logic                 cross_carry;
            register_slice #(
                .DATA_WIDTH (LSWidth + 1),
                .RESET_VALUE(0)
            ) reg_ls_adder (
                .clk     (clk),
                .clk_en  (1'b1),
                .rst     (rst),
                .data_in ({1'b0, a_ext[LSWidth-1:0]} + {1'b0, b_ext[LSWidth-1:0]}),
                .data_out(ls_adder)
            );
            assign cross_carry = ls_adder[LSWidth];

            logic [MSWidth-1:0] ms_data_a, ms_data_b;
            register_slice #(
                .DATA_WIDTH (2 * MSWidth),
                .RESET_VALUE(0)
            ) reg_ms_data_a_b (
                .clk     (clk),
                .clk_en  (1'b1),
                .rst     (rst),
                .data_in ({a_ext[OUT_BITS-1:OUT_BITS-MSWidth], b_ext[OUT_BITS-1:OUT_BITS-MSWidth]}),
                .data_out({ms_data_a, ms_data_b})
            );

            logic [MSWidth-1+1:0] ms_adder;
            assign ms_adder = {ms_data_a, cross_carry} + {ms_data_b, cross_carry};
            assign sum      = {ms_adder[MSWidth:1], ls_adder[LSWidth-1:0]};
        end else begin : gen_no_register_middle
            assign sum = a_ext + b_ext;
        end
    endgenerate

    // optional output register
    generate
        if (REGISTER_OUTPUT != 0) begin : gen_register_output
            register_slice #(
                .DATA_WIDTH (OUT_BITS),
                .RESET_VALUE(0)
            ) reg_out (
                .clk     (clk),
                .clk_en  (1'b1),
                .rst     (rst),
                .data_in (sum),
                .data_out(out)
            );
        end else begin : gen_no_register_output
            assign out = sum;
        end
    endgenerate

endmodule

