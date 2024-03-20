`include "timescale.svh"

module int_adder_tree_layer #(
    parameter  int NUM_IN_WORDS = 5,
    localparam int NumInPairs   = NUM_IN_WORDS / 2,
    localparam int NumInOdd     = NUM_IN_WORDS - NumInPairs * 2,
    localparam int NumOutWords  = NumInPairs + NumInOdd,

    parameter int BITS_PER_IN_WORD    = 16,
    parameter int BITS_PER_OUT_WORD   = 17,
    parameter int SIGN_EXT            = 1,
    parameter int REGISTER_MIDDLE     = 0,
    parameter int REGISTER_OUTPUT     = 1,
    parameter int EXTRA_BIT_CONNECTED = 0
) (
    input  logic                         clk,
    input  logic                         rst,
    input  logic [ BITS_PER_IN_WORD-1:0] words_in     [NUM_IN_WORDS],
    output logic [BITS_PER_OUT_WORD-1:0] words_out    [ NumOutWords],
    input  logic                         extra_bit_in,
    output logic                         extra_bit_out
);

    genvar i;
    generate
        if (EXTRA_BIT_CONNECTED != 0) begin : gen_extra_bit_connected
            // sync extra bit with adder tree pipeline
            logic extra_bit_m;
            if (REGISTER_MIDDLE != 0) begin : gen_register_middle_extra_bit
                register_slice #(
                    .DATA_WIDTH (1),
                    .RESET_VALUE(0)
                ) reg_extra_bit_m (
                    .clk     (clk),
                    .clk_en  (1'b1),
                    .rst     (rst),
                    .data_in (extra_bit_in),
                    .data_out(extra_bit_m)
                );
            end else begin : gen_no_register_middle_extra_bit
                assign extra_bit_m = extra_bit_in;
            end
            if (REGISTER_OUTPUT != 0) begin : gen_register_output_extra_bit
                register_slice #(
                    .DATA_WIDTH (1),
                    .RESET_VALUE(0)
                ) reg_extra_bit_out (
                    .clk     (clk),
                    .clk_en  (1'b1),
                    .rst     (rst),
                    .data_in (extra_bit_m),
                    .data_out(extra_bit_out)
                );
            end else begin : gen_no_register_output_extra_bit
                assign extra_bit_out = extra_bit_m;
            end
        end else begin : gen_extra_bit_not_connected
            always_comb extra_bit_out = 1'b0;
        end

        // Process the pairs as binary adder nodes with optional pipeline
        for (i = 0; i < NumInPairs; i = i + 1) begin : gen_adder_tree_node
            logic [BITS_PER_IN_WORD-1:0] node_in_a, node_in_b;
            /*
                Example:
                    4 input words, NumInPairs = 2, [3:0][BITS_PER_IN_WORD-1:0] words_in
                        i = 0, 2*i = 0, 2*i+1 = 1
                        i = 1, 2*i = 2, 2*i+1 = 3

                    5 input words, NumInPairs = 2, [4:0][BITS_PER_IN_WORD-1:0] words_in
                        even:
                            i = 0, 2*i = 0, 2*i+1 = 1
                            i = 1, 2*i = 2, 2*i+1 = 3
                        odd:
                            words_out[2] = words_in[4] + 0
            */
            assign node_in_a = words_in[2*i];
            assign node_in_b = words_in[2*i+1];
            int_adder_tree_node #(
                .IN_BITS        (BITS_PER_IN_WORD),
                .OUT_BITS       (BITS_PER_OUT_WORD),
                .SIGN_EXT       (SIGN_EXT),
                .REGISTER_OUTPUT(REGISTER_OUTPUT),
                .REGISTER_MIDDLE(REGISTER_MIDDLE)
            ) inst_adder_tree_node (
                .clk(clk),
                .rst(rst),
                .a  (node_in_a),
                .b  (node_in_b),
                .out(words_out[i])
            );
        end
        // fall through the odd word if exists
        if (NumInOdd == 1) begin : gen_odd_word_fall_through
            int_adder_tree_node #(
                .IN_BITS        (BITS_PER_IN_WORD),
                .OUT_BITS       (BITS_PER_OUT_WORD),
                .SIGN_EXT       (SIGN_EXT),
                .REGISTER_OUTPUT(REGISTER_OUTPUT),
                .REGISTER_MIDDLE(REGISTER_MIDDLE)
            ) inst_adder_tree_node_odd (
                .clk(clk),
                .rst(rst),
                .a  (words_in[NUM_IN_WORDS-1]),
                .b  ({BITS_PER_IN_WORD{1'b0}}),
                .out(words_out[NumInPairs])
            );
        end
    endgenerate

endmodule
