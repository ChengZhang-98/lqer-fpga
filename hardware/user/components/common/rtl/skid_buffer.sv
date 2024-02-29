`timescale 1ns / 1ps

/*
    Module:         skid_buffer
    Description:    pipeline register
                    Refer to: http://fpgacpu.ca/fpga/Pipeline_Skid_Buffer.html

    + means insert (handshake at input ports)
    - mean remove (handshake at output ports)

    This skid buffer has three states:
    1. It is Empty.
    2. It is Busy, holding one item of data in the main register, either waiting or actively transferring data through that register.
    3. It is Full, holding data in both registers, and stopped until the main register is emptied and simultaneously refilled from the buffer register,
       so no data is lost or reordered. (Without an available empty register, the input interface cannot skid to a stop, so it must signal it is not ready.)
    4. It is Full and in Circular Buffer Mode, holding data in both registers, and can accept new data into the buffer register
       while simultaneously replacing the contents of the main register with the current contents of the buffer register.

    CBM means in CIRCULAR_BUFFER_MODE, always allowing insert,
    which moves the data_buff_reg to data_out_reg, and load new inserted data to data_buff_reg


                    /--\ +- flow
                    |  |
            load   |  v   fill
    -------   +    ------   +    ------        (CBM)
    |       | ---> |      | ---> |      | ---\ +  dump
    | Empty |      | Busy |      | Full |    |   or
    |       | <--- |      | <--- |      | <--/ +- pass
    -------    -   ------    -   ------
            unload         flush
*/

module skid_buffer #(
    parameter int DATA_WIDTH           = 8,
    parameter int CIRCULAR_BUFFER_MODE = 0
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
    localparam bit [DATA_WIDTH-1:0] DataZero = {DATA_WIDTH{1'b0}};
    /*
    Data path
        Registers:
            data_buffer_reg can receive data_in and output to data_out_reg.
            data_out_reg receives selected_data and outputs to data_out.
        Control signals:
            data_buffer_wren enables write data_in to data_buffer_reg.
            data_out_wren enables write selected_data to data_out_reg.
            use_buffered_data is high if data_buffer_out is selected to sent to data_out_reg, else data_in is sent.
    */
    logic                  data_buffer_wren;  // EMPTY at start, so don't load.
    logic [DATA_WIDTH-1:0] data_buffer_out;

    register_slice #(
        .DATA_WIDTH (DATA_WIDTH),
        .RESET_VALUE(DataZero)
    ) data_buffer_reg (
        .clk     (clk),
        .clk_en  (data_buffer_wren),
        .rst     (rst),
        .data_in (data_in),
        .data_out(data_buffer_out)
    );

    logic                  data_out_wren;  // EMPTY at start, so accept data.
    logic                  use_buffered_data;
    logic [DATA_WIDTH-1:0] selected_data;

    always_comb begin : selected_data_logic
        selected_data = (use_buffered_data == 1'b1) ? data_buffer_out : data_in;
    end

    register_slice #(
        .DATA_WIDTH (DATA_WIDTH),
        .RESET_VALUE(DataZero)
    ) data_out_reg (
        .clk     (clk),
        .clk_en  (data_out_wren),
        .rst     (rst),
        .data_in (selected_data),
        .data_out(data_out)
    );

    /*
    Control path
    */

    // FSM
    localparam int StateBits = 2;
    typedef enum bit [StateBits-1:0] {
        EMPTY,
        BUSY,
        FULL
    } state_t;

    state_t state_cur, state_next;
    register_slice #(
        .DATA_WIDTH (StateBits),
        .RESET_VALUE(EMPTY)       // initial state is EMPTY
    ) state_reg (
        .clk     (clk),
        .clk_en  (1'b1),
        .rst     (rst),
        .data_in (state_next),
        .data_out(state_cur)
    );

    // handshake
    logic insert, remove;

    always_comb begin : insert_remove_logic
        insert = (valid_in & ready_in);
        remove = (valid_out & ready_out);
    end

    // data path states
    logic load, flow, fill, unload, flush, dump, pass;
    always_comb begin : datapath_state_logic
        load   = (state_cur == EMPTY) && (insert == 1'b1) && (remove == 1'b0);
        flow   = (state_cur == BUSY) && (insert == 1'b1) && (remove == 1'b1);
        fill   = (state_cur == BUSY) && (insert == 1'b1) && (remove == 1'b0);
        unload = (state_cur == BUSY) && (insert == 1'b0) && (remove == 1'b1);
        flush  = (state_cur == FULL) && (insert == 1'b0) && (remove == 1'b1);
        dump   = (state_cur == FULL) && (insert == 1'b1) && (remove == 1'b0) && (CIRCULAR_BUFFER_MODE == 1);
        pass   = (state_cur == FULL) && (insert == 1'b1) && (remove == 1'b1) && (CIRCULAR_BUFFER_MODE == 1);
    end

    // this FSM doesn't handle illegal state transfers
    always_comb begin : fsm_next_state_logic
        state_next = (load == 1'b1) ? BUSY : state_cur;
        state_next = (flow == 1'b1) ? BUSY : state_next;
        state_next = (fill == 1'b1) ? FULL : state_next;
        state_next = (flush == 1'b1) ? BUSY : state_next;
        state_next = (unload == 1'b1) ? EMPTY : state_next;
        state_next = (dump == 1'b1) ? FULL : state_next;
        state_next = (pass == 1'b1) ? FULL : state_next;
    end

    // control signals to datapath: data_buffer_wren, data_out_wren, use_buffered_data

    always_comb begin : datapath_control_signal_logic
        data_buffer_wren  = (fill == 1'b1) || (dump == 1'b1) || (pass == 1'b1);
        data_out_wren     = (load == 1'b1) || (flow == 1'b1) || (dump == 1'b1) || (pass == 1'b1) || (flush == 1'b1);
        use_buffered_data = (flush == 1'b1) || (dump == 1'b1) || (pass == 1'b1);
    end

    /*
    Output signals
        - ready_in
        - valid_out
        ready_in and valid_out are stored in registers,
        which avoids directly comb logic across two pipeline stages
    */
    logic ready_in_next;

    // ready_in is stored in a register
    register_slice #(
        .DATA_WIDTH (1),
        .RESET_VALUE(1'b1)
    ) ready_in_reg (
        .clk     (clk),
        .clk_en  (1'b1),
        .rst     (rst),
        .data_in (ready_in_next),
        .data_out(ready_in)
    );
    assign ready_in_next = ((state_next != FULL) || (CIRCULAR_BUFFER_MODE == 1));

    // valid_out is stored in a register
    logic valid_out_next;
    register_slice #(
        .DATA_WIDTH (1),
        .RESET_VALUE(1'b0)
    ) valid_out_reg (
        .clk     (clk),
        .clk_en  (1'b1),
        .rst     (rst),
        .data_in (valid_out_next),
        .data_out(valid_out)
    );
    assign valid_out_next = (state_next != EMPTY);

endmodule
