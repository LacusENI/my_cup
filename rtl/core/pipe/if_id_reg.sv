`default_nettype none

// IF/ID 流水线寄存器
//
// 行为：
//   rst 或 flush -> 清 0（插入气泡）
//   stall        -> 保持当前值（暂停流水线）
//   其他          -> 每个上升沿把输入打一拍
module if_id_reg
    import cpu_pkg::*;
(
    input  logic   clk,
    input  logic   rst,
    input  logic   flush,
    input  logic   stall,
    input  if_id_t if_id_in,
    output if_id_t if_id_out
);
    always_ff @(posedge clk) begin
        if (rst || flush)
            if_id_out <= '0;
        else if (!stall)
            if_id_out <= if_id_in;
    end
endmodule

`default_nettype wire
