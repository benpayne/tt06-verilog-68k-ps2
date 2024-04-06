<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project takes input from a PS2 device, clock and data signals, it will run this through a shift register and validate start, stop and parity bits.  When a valid message is descoded it will raise the valid pin (uio_io[0]).  This will remain high until the reset is hit and that will clear valid and get the chip ready for decode another signal.  

## How to test

It hasn't yets been tested...

## External hardware

This will use a keyboard or mouse and this ciruit is intended to connect to a retro computer. 
