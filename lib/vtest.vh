`ifndef VTEST_VH
`define VTEST_VH

`define COLOR_RED     "\033[1;31m"
`define COLOR_GREEN   "\033[1;32m"
`define COLOR_RESET   "\033[0m"

/**
 * VTEST_INIT
 * 声明测试环境所需变量，测试计数器
 */
`define VTEST_INIT \
    integer test_pass_count = 0; \
    integer test_fail_count = 0; \
    integer test_total_count = 0; \
    reg current_test_passed = 1; \
    reg [255:0] current_test_name; \

/**
 * VTEST_BOOT
 * 开始测试，初始化计数器，并打印测试开始的消息
 * @note 开启名为 vtest 的子命名块
 * @note 请记得在完成所有测试用例后调用 @ref VTEST_FINISH
 */
`define VTEST_BOOT \
    begin : vtest \
    test_pass_count = 0; \
    test_fail_count = 0; \
    test_total_count = 0; \
    $display("%0s[==========]%0s Running tests", `COLOR_GREEN, `COLOR_RESET); \

/**
 * TEST(label)
 * 定义一个测试用例，设置当前测试的名称，并打印测试开始的消息
 * @param label: (标识符)测试用例的标签，用于标识测试
 * @note 调用 begin : label, 开启与 label 同名的子命名块
 * @note 记得在测试用例结束时调用 @ref TEST_END
 */
`define TEST(label) \
    begin : label \
    begin \
        current_test_name = `"label`"; \
        current_test_passed = 1; \
        test_total_count = test_total_count + 1; \
        $display("%0s[ RUN      ]%0s %0s", `COLOR_GREEN, `COLOR_RESET, current_test_name); \
    end \

/**
 * TEST_END
 * 结束测试用例，输出测试结果
 * @note 会调用 end 语句, 使 @ref TEST 开启的命名块闭合
 */
`define TEST_END \
    begin \
        if (current_test_passed) begin \
            test_pass_count = test_pass_count + 1; \
            $display("%0s[       OK ]%0s %0s", `COLOR_GREEN, `COLOR_RESET, current_test_name); \
        end \
        else begin \
            test_fail_count = test_fail_count + 1; \
            $display("%0s[  FAILED  ]%0s %0s", `COLOR_RED, `COLOR_RESET, current_test_name); \
        end \
    end \
    end \

/**
 * EXPECT(name, actual, expect)
 * 断言两个值是否相等，不相等时输出断言失败信息
 * @param name (字符串)用于标识此断言的名字
 * @param actual 要断言的值
 * @param expect 断言期望值
 */
`define EXPECT(name, actual, expect) \
    if (actual !== expect) begin \
        current_test_passed = 0; \
        $display("assert failed (%0s): got %h, expected %h", name, actual, expect); \
    end \

/**
 * VTEST_FINISH
 * 结束测试，打印最终测试结果信息
 * @note 会使 @ref VTEST_BOOT 开启的 vtest 命名块闭合
 */
`define VTEST_FINISH \
    begin \
        $display("%0s[==========]%0s %0d tests ran", `COLOR_GREEN, `COLOR_RESET, test_total_count); \
        $display("%0s[  PASSED  ]%0s %0d tests", `COLOR_GREEN, `COLOR_RESET, test_pass_count); \
        if (test_fail_count > 0) begin \
            $display("%0s[  FAILED  ]%0s %0d tests", `COLOR_RED, `COLOR_RESET, test_fail_count); \
        end \
    end \
    end \
    $finish(0); \

`endif
