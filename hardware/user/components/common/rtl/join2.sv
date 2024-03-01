`timescale 1ns / 1ps

/*
    Module:       join2
    Description:
                  Join2 synchronises two sets of input handshake signals with a set of output handshaked signals.
                  If only one of the inputs is valid - we need to stall the valid input and wait
                  for the other input by setting one of the ready bit of the valid input to 0.
                  Note that if (ready_out & valid_in_a & valid_in_b) is 1, then this module is a passthrough
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  | ready_out      | valid_in_a      | valid_in_b      | ready_in_a      | ready_in_b      |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              0 |               0 |               0 |               0 |               0 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              0 |               0 |               1 |               0 |               0 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              0 |               1 |               0 |               0 |               0 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              0 |               1 |               1 |               0 |               0 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              1 |               0 |               0 |               1 |               1 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              1 |               0 |               1 |               1 |               0 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              1 |               1 |               0 |               0 |               1 |
                  +----------------+-----------------+-----------------+-----------------+-----------------+
                  |              1 |               1 |               1 |               1 |               1 |
                  +----------------+-----------------+-----------------+-----------------+-----------------
*/

module join2 #(
) (
    // upstream ports
    input  logic valid_in_a,
    input  logic valid_in_b,
    output logic ready_in_a,
    output logic ready_in_b,
    // downstream ports
    output logic valid_out,
    input  logic ready_out
);

    assign ready_in_a = ready_out & (!valid_in_a | valid_in_b);
    assign ready_in_b = ready_out & (!valid_in_b | valid_in_a);
    assign valid_out  = valid_in_a & valid_in_b;

endmodule
