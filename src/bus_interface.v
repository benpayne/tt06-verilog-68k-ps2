`define default_netname none

module cpu68k_interface(
    input wire clk,         // System clock
    input wire cs,          // Chip select, active low
    input wire ds,          // Data strobe, active low
    input wire rw,          // Read/Write line, high for read, low for write
    input wire reset,       // Reset signal
    input wire [7:0] uio_in,  // Data bus input
    output reg [7:0] uio_out, // Data bus output
    output reg uio_oe,      // Output enable for the data bus
    output reg clr,         // Output high during a read cycle with clock high
    output reg data_rdy,    // Output high during a write cycle with clock high
    output wire dtack,       // Data acknowledge signal, active low
    input wire [7:0] read_reg,  // Internal register for read
    output reg [7:0] write_reg  // Internal register for read
);
    assign dtack = cs || ds;

    always @(ds or cs or reset) begin
        if (reset) begin
            write_reg <= 8'b00000000;
            uio_out <= 8'b00000000;
            uio_oe <= 0;
            clr <= 0;
            data_rdy <= 0;
        end else if (!cs && !ds) begin
            if (rw) begin  // Read cycle
                uio_out <= read_reg;  // Place read register contents on the bus
                uio_oe <= 1;          // Enable output
                clr <= 1;             // Set clr high as reading occurs
            end else begin  // Write cycle
                write_reg <= uio_in;  // Capture data from the bus
                data_rdy <= 1;        // Indicate data is ready
                uio_oe <= 0;          // Disable output as it's a write operation
            end
        end else begin
            uio_oe <= 0;  // Disable output if not selected or strobed
            clr <= 0;
        end
    end

    initial begin
        $monitor("uio_out=%h uio_oe=%b clr=%b data_rdy=%b dtack=%b cs=%b ds=%b", uio_out, uio_oe, clr, data_rdy, dtack, cs, ds);
    end
endmodule
