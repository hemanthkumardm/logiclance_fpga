`timescale 1ns / 1ps

module tb_adder;
    reg clk;
    reg [31:0] a;
    reg [31:0] b;
    wire [31:0] sum;
    
    adder uut (
        .clk(clk),
        .a(a),
        .b(b),
        .sum(sum)
    );
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    integer fd_gold, fd_res;
    integer scan_gold;
    integer gold_sum;
    
    initial begin
        // Wait for Global Reset (GSR) to deassert (required for post-impl sim)
        #100;
        
        fd_res = $fopen("RESULT.txt", "w");
        
        fd_gold = $fopen("/tmp/fpga_cmodel_golden.txt", "r");
        if (fd_gold == 0) begin
            $display("ERROR: Could not open golden output file");
            $fwrite(fd_res, "TEST_FAILED\n");
            $fclose(fd_res);
            $finish;
        end
        
        // C-model outputs: A, B, ExpectedSum
        scan_gold = $fscanf(fd_gold, "%d\n%d\n%d", a, b, gold_sum);
        
        // Wait for RTL to compute (give it a few clock cycles)
        #20;
        
        $display("RTL: a=%d b=%d sum=%d", a, b, sum);
        $display("CMOD: expected_sum=%d", gold_sum);
        
        if (sum == gold_sum) begin
            $fwrite(fd_res, "TEST_PASSED\n");
            $display("SUCCESS: RTL matches C-model!");
        end else begin
            $fwrite(fd_res, "TEST_FAILED\n");
            $display("FAIL: RTL %d != C-model %d", sum, gold_sum);
        end
        
        $fclose(fd_gold);
        $fclose(fd_res);
        $finish;
    end
endmodule
