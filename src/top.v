/*
 * Copyright (c) 2024 Ben Payne
 * SPDX-License-Identifier: Apache-2.0
 */

`define default_netname none

module tt_um_benpayne_ps2_decoder (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    wire valid;
    wire [7:0] ps2_data_bus;
    wire bus_oe;
    wire dec_rst;
    wire dtack;

    reg [7:0] uio_oe_reg;

    assign uio_oe = uio_oe_reg;
    assign uo_out[0] = dtack;
    assign uo_out[7:1] = 7'b0000000;

    ps2_decoder decoder (
        .ps2_clk(ui_in[0]),  // PS2 Clock Input
        .ps2_data(ui_in[1]), // PS2 Data Input
        .reset(dec_rst),      // Reset signal
        .valid(valid),   // IOs: Input path
        .data(ps2_data_bus),  // IOs: Output path
        .clk(clk)            // clock
    );

    cpu68k_interface bus (
        .clk(clk),         // System clock
        .cs(ui_in[2]),          // Chip select, active high
        .ds(ui_in[3]),        // Data strobe, active high
        .rw(ui_in[4]),         // Read/Write line, high for read, low for write
        .uio_in(uio_in),  // Data bus input
        .uio_out(uio_out), // Data bus output
        .uio_oe(bus_oe),   // Output enable for the data bus
        .clr(dec_rst),        // Output high during a read cycle with clock high
        .dtack(dtack),       // Data acknowledge signal, active low
        .read_reg(ps2_data_bus)     // Internal register for read
    );

    always @(posedge clk) begin
        if (bus_oe) begin
            uio_oe_reg <= 8'b11111111;
        end else begin
            uio_oe_reg <= 8'b00000000;
        end
    end
endmodule

