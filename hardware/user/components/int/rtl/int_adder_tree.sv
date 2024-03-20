/*
    Module:     int_adder_tree
    Description:
                An adder tree for signed/unsigned integers.
                Supports signed/unsigned extension.
                Does not support truncation in layers. Error will be raised if OUT_BITS < BitsPerLayerOutWordEst.
                Supports carry pipeline (REGISTER_MIDDLE) and output pipeline (REGISTER_OUTPUT) in int_adder_tree_node.
*/
`include "timescale.svh"

module int_adder_tree #(
    parameter int NUM_IN_WORDS     = 4,
    parameter int BITS_PER_IN_WORD = 8,
    parameter int OUT_BITS         = 10,
    parameter int SIGN_EXT         = 1,   // bool, enable sign extension or not
    parameter int REGISTER_MIDDLE  = 0,   // bool, register within adders or not
    parameter int REGISTER_OUTPUT  = 0,   // bool, register adder outputs or not
    parameter int EXTRA_BIT_USED   = 0    // bool, extra bit to pass along the pipeline
) (
    input  logic                        clk,
    input  logic                        rst,
    input  logic                        extra_bit_in,
    output logic                        extra_bit_out,
    input  logic [BITS_PER_IN_WORD-1:0] words_in     [NUM_IN_WORDS],
    output logic [        OUT_BITS-1:0] out
);

    initial begin
        assert (NUM_IN_WORDS > 1);
    end

    localparam int NumLayers = $clog2(NUM_IN_WORDS);

    // Generate adder tree layers
    for (genvar i = 0; i < NumLayers; i++) begin : gen_layers
        // NumLayerInWords = ceil( NUM_IN_WORDS / (2^i) ) = (NUM_IN_WORDS + 2^i-1) // 2^i
        localparam int NumLayerInWords = (NUM_IN_WORDS + ((1 << i) - 1)) >> i;
        localparam int BitsPerLayerInWordEst = BITS_PER_IN_WORD + i;
        localparam int BitsPerLayerInWord = (i == 0) ? BITS_PER_IN_WORD : BitsPerLayerInWordEst;
        localparam int BitsPerLayerOutWordEst = BitsPerLayerInWordEst + 1;
        localparam int BitsPerLayerOutWord = (i == (NumLayers - 1)) ? OUT_BITS : BitsPerLayerOutWordEst;
        localparam int NumLayerInPairs = NumLayerInWords / 2;
        localparam int NumLayerInOdd = NumLayerInWords - NumLayerInPairs * 2;
        localparam int NumLayerOutWords = NumLayerInPairs + NumLayerInOdd;


        initial begin
            if (BitsPerLayerOutWordEst > OUT_BITS) begin
                $error("Layer %d: BitsPerLayerOutWordEst %d > OUT_BITS %d", i, BitsPerLayerOutWordEst, OUT_BITS);
                $stop();
            end
        end

        // inputs and outputs of each layer
        logic [ BitsPerLayerInWord-1:0] layer_words_in      [ NumLayerInWords];
        logic [BitsPerLayerOutWord-1:0] layer_words_out     [NumLayerOutWords];
        logic                           layer_extra_bit_in;
        logic                           layer_extra_bit_out;
        // layer i
        int_adder_tree_layer #(
            .NUM_IN_WORDS       (NumLayerInWords),
            .BITS_PER_IN_WORD   (BitsPerLayerInWord),
            .BITS_PER_OUT_WORD  (BitsPerLayerOutWord),
            .SIGN_EXT           (SIGN_EXT),
            .REGISTER_MIDDLE    (REGISTER_MIDDLE),
            .REGISTER_OUTPUT    (REGISTER_OUTPUT),
            .EXTRA_BIT_CONNECTED(EXTRA_BIT_USED)
        ) inst_layer (
            .clk          (clk),
            .rst          (rst),
            .words_in     (layer_words_in),
            .words_out    (layer_words_out),
            .extra_bit_in (layer_extra_bit_in),
            .extra_bit_out(layer_extra_bit_out)
        );

        // Connect module input, output, and adjacent layers
        if (i == 0) begin : gen_first_layer
            // module input -> first layer
            assign gen_layers[0].layer_words_in     = words_in;
            assign gen_layers[0].layer_extra_bit_in = extra_bit_in;
        end

        if (i > 0) begin : gen_adjacent_layers
            // layer[i-1] output -> layer[i] input
            assign gen_layers[i].layer_words_in     = gen_layers[i-1].layer_words_out;
            assign gen_layers[i].layer_extra_bit_in = gen_layers[i-1].layer_extra_bit_out;
        end

        if (i == NumLayers - 1) begin : gen_last_layer
            assign out           = gen_layers[NumLayers-1].layer_words_out[0];
            assign extra_bit_out = gen_layers[NumLayers-1].layer_extra_bit_out;
        end
    end

endmodule
