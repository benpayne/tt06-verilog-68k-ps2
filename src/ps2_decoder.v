/*
 * Copyright (c) 2024 Ben Payne
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none

module ps2_decoder (
    input  wire       ps2_clk,  // PS2 Clock Input
    input  wire       ps2_data, // PS2 Data Input
    input  wire       reset,    // Reset signal
    output reg        valid,    // IOs: Input path
    output wire [7:0] data,     // IOs: Output path
    input  wire       clk       // clock
);

    // State definitions
    localparam IDLE = 0,
               START_BIT = 1,
               DATA_BITS = 2,
               PARITY_BIT = 3,
               STOP_BIT = 4;

    reg [3:0] state = IDLE;
    reg [3:0] bit_count = 0;
    reg [7:0] shift_reg = 0;  // Includes parity bit
    reg parity_calc = 0;
    reg ps2_clk_prev = 1;
    
    assign data = shift_reg[7:0];

    always @(negedge clk or posedge reset) begin
        if (reset) begin
            state <= IDLE;
            bit_count <= 0;
            shift_reg <= 0;
            parity_calc <= 0;
            valid <= 0;
        end
        else begin
            // Edge detection logic
            if (ps2_clk_prev && !ps2_clk) begin  // Detect falling edge
                case(state)
                    IDLE: begin
                        if (ps2_data == 0) begin  // Confirm start bit
                            state <= DATA_BITS;
                            bit_count <= 0;
                            parity_calc <= 0;
                        end
                    end
                    DATA_BITS: begin
                        shift_reg[bit_count] <= ps2_data;
                        parity_calc <= parity_calc ^ ps2_data;  // Calculate parity
                        bit_count <= bit_count + 1;
                        if (bit_count == 7) begin
                            state <= PARITY_BIT;
                        end
                    end
                    PARITY_BIT: begin
                        if (ps2_data == parity_calc) begin  // Check parity
                            state <= STOP_BIT;
                        end else begin
                            state <= IDLE;  // Parity error, reset to idle
                        end
                    end
                    STOP_BIT: begin
                        if (ps2_data == 1) begin  // Stop bit
                            valid <= 1;
                        end 
                        state <= IDLE;  // Stop bit error
                    end
                endcase
            end
            ps2_clk_prev <= ps2_clk;
        end
    end

endmodule

