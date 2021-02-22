#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from argparse import ArgumentParser, FileType
from helpers import *
from CircuitGraph import CircuitGraph
from time import perf_counter, process_time
from Z3Checker import Z3Checker
from IndepChecker import IndepChecker
from sys import setrecursionlimit
from multiprocessing import Pool
from logger import logger

setrecursionlimit(10000)

def verify_circuit(circuit_file, labeling, order, mode='transient', log='tmp/report.txt'):
	secrets = ', '.join(
		[var for k in labeling for var in labeling[k] if 's_' in var])
	labels = labeling
	time_start_abs = perf_counter()
	time_start_rel = process_time()
	circuit = CircuitGraph(labels, json_file=circuit_file)
	checker = Z3Checker(circuit.get_graph(), labels, order, mode)
	logger.info('Checking secrets: {}...'.format(secrets))
	check_res, gates = checker.check()
	time_end_abs = perf_counter()
	time_end_rel = process_time()
	rel_time = time_end_rel - time_start_rel
	m_rel, s_rel = divmod(rel_time, 60)
	h_rel, m_rel = divmod(m_rel, 60)
	logger.info('... secrets {} are checked in {}h{}m{}s'.format(
		secrets, int(h_rel), int(m_rel), round(s_rel, 2)))
	logger.info('Result ({}): {}, {}'.format(secrets, check_res, gates))
	return (check_res, gates)

if __name__ == '__main__':
	parser = ArgumentParser(prog='Rebecca',
		description=' A tool for checking if a given netlist is side-channel analysis resistant',
		epilog='Questions and suggestions can be sent to the email <email>')
	parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.9.2')
	parser.add_argument('-p', '--parse-verilog', nargs=2,
		metavar=('<netlist>', '<top module>'),
		help='parse verilog file and generate labeling template')
	parser.add_argument('-o', '--optimized', action='store_true',
		help='run verification in parallel')
	parser.add_argument('-c', '--check', nargs=4, metavar=('<netlist>', '<order>', '<labeling>', '<mode>'),
		help='check if a netlist <netlist> is <order>-order secure with the <labeling> as initial labeling; mode = s (stable) | t (transient)')
	parser.add_argument('-i', '--independence-check', nargs=3, metavar=('<netlist>', '<order>', '<labeling>'),
		help='check if a netlist <netlist> is <order>-order independent with the <labeling> as initial labeling')
	args = vars(parser.parse_args())
	if args['parse_verilog']:
		parse_verilog(args['parse_verilog'][0], args['parse_verilog'][1])
	if args['independence_check']:
		shares = get_shares(args['independence_check'][2])
		labels = generate_labeling(args['independence_check'][2])[0]
		circuit = CircuitGraph(labels, json_file=args['independence_check'][0])
		if is_int(args['independence_check'][1]):
			order = int(args['independence_check'][1])
		else:
			print('ERR: order should be int')
			exit()
		outputs = circuit.get_outputs()
		checker = IndepChecker(circuit.get_graph(), labels, order, shares, outputs)
		print(checker.check())
	if args['check']:
		labels = []
		if args['optimized']:
			labels = generate_optimized_labeling(args['check'][2])
		else:
			labels = generate_labeling(args['check'][2])
		if is_int(args['check'][1]):
			order = int(args['check'][1])
		else:
			print('ERR: order should be int')
			exit()
		if args['check'][3] == 't':
			mode = 'transient'
		elif args['check'][3] == 's':
			mode = 'stable'
		else:
			print('ERR: mode should be either s or t')
			exit()
		logger.info('Verifying {} for {} order in {} mode'.format(
			args['check'][0], order, mode))
		for l in labels:
			logger.info('Initial labeling:\n{}'.format(get_pretty_labeling(
				l, args['check'][2])))
		pool_len = len(labels) if len(labels) <= 10 else 10
		with Pool(pool_len) as p:
			res = p.starmap(verify_circuit,
				[(args['check'][0], l, order, mode) for l in labels])
		for r in res:
			if not r[0]:
				print(r)
				exit()
		print((True, []))
