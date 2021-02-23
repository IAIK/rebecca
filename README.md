# REBECCA

REBECCA is a tool for the formal verification of masked cryptographic hardware implementations
that, given the netlist of a masked hardware circuit, determines if a correct separation between
shares is preserved throughout the circuit.

This is a re-publication of the [original code](https://github.com/riusupov/rebecca) of the
REBECCA tool which was developed as part of the paper [Formal Verification of Masked Hardware
Implementations in the Presence of Glitches](https://eprint.iacr.org/2017/897.pdf) from
EUROCRYPT 2018. This code version is identical to the original one, except for added
declarations for the used Apache 2.0 license.

## Prerequisites

### Python Dependencies

REBECCA has a couple of Python dependencies. You can run
```console
$ pip install --user -r python_requirements.txt
```
to install those dependencies.

### Yosys

REBECCA requires the [Yosys Open SYnthesis Suite](https://github.com/YosysHQ/yosys) to be installed.

## Usage

```console
$ ./verify -h
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
                        check if a parsed netlist <netlist> is <order>-order secure
                        with the <labeling> as initial labeling; mode = s
                        (stable) | t (transient)
  -i <netlist> <order> <labeling>, --independence-check <netlist> <order> <labeling>
                        check if a parsed netlist <netlist> is <order>-order
                        independent with the <labeling> as initial labeling
```

## Example

The following steps illustrate how to use REBECCA for verifying the DOM AND gate.

1. In a first step, the netlist needs to be parsed using Yosys:
```console
$ ./verify.py --parse-verilog benchmarks/first_order/dom_and/dom_and.v dom_and
```

2. As a result, the verilog netlist is parsed into a .json file and a the labeling
template is produced. Open the file `benchmarks/first_order/dom_and/dom_and.txt` and
label the input nodes as follows:
```
ClkxCI_2: unimportant
QxDO_10: unimportant
QxDO_9: unimportant
RstxBI_3: unimportant
XxDI_4: share 1
XxDI_5: share 1
YxDI_6: share 2
YxDI_7: share 2
ZxDI_8: mask
```

3. Now, the following command can be used to perform the check of the netlist:
```console
$ ./verify.py --check benchmarks/first_order/dom_and/dom_and.json 1 benchmarks/first_order/dom_and/dom_and.txt t
```
4. As the DOM AND gate is first-order secure, this should produce the following output:
```console
(True, [])
```

## References

- [Formal Verification of Masked Hardware Implementations in the Presence of Glitches](https://eprint.iacr.org/2017/897.pdf)
