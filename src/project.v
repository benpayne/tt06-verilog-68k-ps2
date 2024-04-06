/*
 * Copyright (c) 2024 Ben Payne
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // All output pins must be assigned. If not used, assign to 0.
    assign uio_out = 0;
    assign uio_oe  = 8'hFF;   // All pins are outputs
    assign reset  = ~rst_n;  // Invert reset signal

    // State definitions
    localparam IDLE = 0,
               START_BIT = 1,
               DATA_BITS = 2,
               PARITY_BIT = 3,
               STOP_BIT = 4;

    reg [3:0] state = IDLE;
    reg [3:0] bit_count = 0;
    reg [8:0] shift_reg = 0;  // Includes parity bit
    reg valid_reg = 0;
    reg parity_calc = 0;

    assign uo_out = shift_reg[7:0];  
    assign uio_out[0] = valid_reg;  // Output data

    always @(negedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            bit_count <= 0;
            shift_reg <= 0;
            parity_calc <= 0;
        end
        else begin
            case(state)
                IDLE: begin
                    if (ui_in[0] == 0) begin  // Start bit detected
                        state <= START_BIT;
                    end
                end
                START_BIT: begin
                    if (ui_in[0] == 0) begin  // Confirm start bit
                        state <= DATA_BITS;
                        bit_count <= 0;
                        parity_calc <= 0;
                    end else begin
                        state <= IDLE;
                    end
                end
                DATA_BITS: begin
                    shift_reg[bit_count] <= ui_in[0];
                    parity_calc <= parity_calc ^ ui_in[0];  // Calculate parity
                    bit_count <= bit_count + 1;
                    if (bit_count == 7) begin
                        state <= PARITY_BIT;
                    end
                end
                PARITY_BIT: begin
                    if (ui_in[0] == parity_calc) begin  // Check parity
                        state <= STOP_BIT;
                    end else begin
                        state <= IDLE;  // Parity error, reset to idle
                    end
                end
                STOP_BIT: begin
                    if (ui_in[0] == 1) begin  // Stop bit
                        valid_reg <= 1;
                        state <= IDLE;
                    end else begin
                        state <= IDLE;  // Stop bit error
                    end
                end
            endcase
        end
    end

    // Clear valid flag after being set for one cycle
    always @(posedge valid_reg) begin
        valid_reg <= 0;
    end

endmodule

