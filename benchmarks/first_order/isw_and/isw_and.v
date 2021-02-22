module mul_isw (am, ma, bm, mb, m0, qm, mq);

  input      am;

  input      ma;

  input      bm;

  input      mb;

  input      m0;

  output     qm;

  output     mq;

 

  wire      am;

  wire      ma;

  wire      bm;

  wire      mb;

  wire      m0;

  reg     qm;

  reg     mq;

 

  assign qm = (ma & mb) ^ m0 ^ (am & mb) ^ (bm & ma);

  assign mq = (am & bm)  ^ m0;

 

endmodule
