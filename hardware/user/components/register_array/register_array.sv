`timescale 1ns / 1ps
module register_slice #(
    parameter int IN_WIDTH = 32
) (
    input logic clk,
    input logic rst,

    input logic [IN_WIDTH-1:0] in_data,
    input logic in_valid,
    output logic in_ready,

    output logic [IN_WIDTH-1:0] out_data,
    output logic out_valid,
    input logic out_ready
);

  localparam type WORD = logic [IN_WIDTH-1:0];
  // register_slice
  // This module implements a register slice that can be used to buffer intermediate data

  // FSM stats
  // FETCH: udpate reg_valid
  // WAIT: wait for out_ready
  typedef enum int {
    FETCH,
    WAIT
  } state_t;

  // reg and next state logic
  WORD reg_data, next_data;
  logic reg_valid, next_valid;
  state_t reg_state, next_state;

  // registers
  always_ff @(posedge clk) begin : fsmd_regs
    if (rst) begin
      reg_state <= FETCH;
      reg_valid <= 0;
      reg_data  <= 0;
    end else begin
      reg_state <= next_state;
      reg_valid <= next_valid;
      reg_data  <= next_data;
    end
  end

  // next state logic
  always_comb begin : fsmd_comb
    next_state = reg_state;
    next_valid = reg_valid;
    next_data  = reg_data;
    case (reg_state)
      FETCH: begin
        if (in_valid) begin
          // if in_valid, update reg_valid and reg_data, go to WAIT to wait for out_ready
          next_state = WAIT;
          next_valid = in_valid;
          next_data  = in_data;
        end else begin
          // if not in_valid, keep fetching in_valid
          next_valid = in_valid;
        end
      end
      WAIT: begin
        if (out_ready) begin
          // if out_ready, reg_data will be consumed, go back to FETCH
          next_state = FETCH;
          // fetch in_valid, if in_valid, also fetch in_data
          next_valid = in_valid;
          if (in_valid) begin
            next_data = in_data;
          end
        end
      end
      default: begin
        // this should never happen
        next_state = FETCH;
        next_valid = 0;
        next_data  = 0;
      end
    endcase
  end

  // output logic
  assign out_valid = reg_valid;
  assign out_data  = reg_data;
  // keep streaming data if no backpressure or no valid data in register slice
  assign in_ready  = out_ready | (~reg_valid);

endmodule

/* verilator lint_off DECLFILENAME */
module register_array #(
    parameter int IN_WIDTH = 32,
    parameter int IN_SIZE  = 16
) (
    input logic clk,
    input logic rst,

    input logic [IN_WIDTH-1:0] in_data[IN_SIZE],
    input logic in_valid,
    output logic in_ready,

    output logic [IN_WIDTH-1:0] out_data[IN_SIZE],
    output logic out_valid,
    input logic out_ready
);

  // register_array: a 1-D register array for pipelining

  logic [IN_WIDTH * IN_SIZE - 1 : 0] in_flatten;
  logic [IN_WIDTH * IN_SIZE - 1 : 0] out_flatten;
  for (genvar i = 0; i < IN_SIZE; i++) begin : gen_flatten_unflatten
    assign in_flatten[i*IN_WIDTH+IN_WIDTH-1 : i*IN_WIDTH] = in_data[i];
    assign out_data[i] = out_flatten[i*IN_WIDTH+IN_WIDTH-1 : i*IN_WIDTH];
  end
  register_slice #(
      .IN_WIDTH(IN_WIDTH * IN_SIZE)
  ) register_slice_inst0 (
      .clk      (clk),
      .rst      (rst),
      .in_valid (in_valid),
      .in_ready (in_ready),
      .in_data  (in_flatten),
      .out_valid(out_valid),
      .out_ready(out_ready),
      .out_data (out_flatten)
  );
endmodule
