`default_nettype none

module tt_um_example (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path
    input  wire       ena,      // always 1 when design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
  
  // --------------------------------------------------
  // Inputs & Constraint Handling
  // --------------------------------------------------
  wire enable = ui_in[0];
  wire [3:0] raw_period = ui_in[4:1]; // 0 to 15
  wire invert = ui_in[5];
  wire [3:0] raw_duty = uio_in[3:0];  
  
  // Pure synthesizable combo logic clamps
  wire [3:0] period_check = (raw_period < 4'd3) ? 4'd3 : raw_period;
  wire [3:0] duty_check   = (raw_duty > period_check) ? period_check : raw_duty;

  // Registers that update strictly on the clock edge 
  // This completely stops 'x' propagation in Gate Level simulation!
  reg [3:0] period;
  reg [3:0] duty;

  always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
          period <= 4'd3;
          duty   <= 4'd0;
      end else begin
          period <= period_check;
          duty   <= duty_check;
      end
  end
  
  // --------------------------------------------------
  // Up Counter (0 to period-1)
  // --------------------------------------------------
  reg [3:0] counter;

  always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
          counter <= 4'd0;
      end else if (enable) begin
          // Clean synthesizable rollover matching your exact original signal logic
          if (counter >= (period - 4'd1))
              counter <= 4'd0;
          else
              counter <= counter + 1'b1;
      end
  end
  
  // --------------------------------------------------
  // PWM Output Generation
  // --------------------------------------------------
  wire pwm_raw;

  assign pwm_raw = (counter < duty);
  wire pwm = invert ? ~pwm_raw : pwm_raw;

  // --------------------------------------------------
  // Outputs
  // --------------------------------------------------
  assign uo_out[0] = enable ? pwm  : 1'b0; 
  assign uo_out[1] = enable ? ~pwm : 1'b0; 
  assign uo_out[7:2] = 6'b0;

  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  wire _unused = &{ena, ui_in[7:6], uio_in[7:4], 1'b0};

endmodule
