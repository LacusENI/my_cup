`ifndef EXT_VH
`define EXT_VH

function [31:0] s_ext_16_32(input [15:0] in);
    s_ext_16_32 = {{16{in[15]}}, in};
endfunction

function [31:0] z_ext_16_32(input [15:0] in);
    z_ext_16_32 = {16'b0, in};
endfunction

function [31:0] s_ext_8_32(input [7:0] in);
    s_ext_8_32 = {{24{in[7]}}, in};
endfunction

function [31:0] z_ext_8_32(input [7:0] in);
    z_ext_8_32 = {24'b0, in};
endfunction

`endif
