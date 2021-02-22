# rebecca
```
usage: ./verify [-h] [-v] [-p <netlist> <top module>] [-o]
                [-c <netlist> <order> <labeling> <mode>]
                [-i <netlist> <order> <labeling>]

A tool for checking if a given netlist is side-channel analysis resistant

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -p <netlist> <top module>, --parse-verilog <netlist> <top module>
                        parse verilog file and generate labeling template
  -o, --optimized       run verification in parallel
  -c <netlist> <order> <labeling> <mode>, --check <netlist> <order> <labeling> <mode>
                        check if a netlist <netlist> is <order>-order secure
                        with the <labeling> as initial labeling; mode = s
                        (stable) | t (transient)
  -i <netlist> <order> <labeling>, --independence-check <netlist> <order> <labeling>
                        check if a netlist <netlist> is <order>-order
                        independent with the <labeling> as initial labeling
```