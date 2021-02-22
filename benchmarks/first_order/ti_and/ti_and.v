// TI AND

module mul (am, ma0, ma1, bm, mb0, mb1, q0, q1, q2);

  input      am;

  input      ma0;

  input      ma1;

  input      bm;

  input      mb0;

  input      mb1;

  output     q0;

  output     q1;

  output     q2;

 

  wire      am;

  wire      ma0;

  wire      ma1;

  wire      bm;

  wire      mb0;

  wire      mb1;

  reg     q0;

  reg     q1;

  reg     q2;

 

  assign q0 = (ma0 & mb0) ^ (ma0 & mb1)  ^ (ma1 & mb0);

  assign q1 = (ma1 & mb1) ^ (am & mb1)  ^ (ma1 & bm);

  assign q2 = (am & bm)   ^ (am & mb0)  ^ (ma0 & bm);

 

endmodule
