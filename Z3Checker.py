#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from CircuitGraph import CircuitGraph
from z3 import *
from json import dump, load, dumps
from logger import logger

class Z3Checker(object):

	def __init__(self, circuit, labels, order, mode='transient', check_security=True):
		self.__circuit = circuit
		self.__labels = labels
		self.__order = order
		self.__mode = mode
		self.__check_security = check_security
		self.__checker_init()
		self.__process_circuit()
	
	def __checker_init(self):
		self.__s = Solver()
		secret_list = []
		mask_list = []
		unimportant_list = []
		variables = []
		self.__variables_stable = {}
		self.__variables_transient = {}
		variables_activation = {}

		for node in self.__circuit.nodes():
			if self.__circuit[node]['node_type'] == 'port':
				for label in self.__labels[str(node)]:
					variables += [label]
					label_type = label.split('_')[0]
					if label_type == 's':
						secret_list += [label]
					elif label_type == 'm':
						mask_list += [label]
					elif label_type == 'y':
						unimportant_list += [label]
					else:
						logger.error('Unknown label type of the label {} for the node {}'.format(label, node))
						exit(-1)

		variables = sorted(set(variables) - set(unimportant_list))
		secret_list = set(secret_list)
		mask_list = set(mask_list)

		self.__masks = mask_list
		self.__secrtes = secret_list

		activation_sum = Int('activation_sum')

		for node in self.__circuit.nodes():
			self.__variables_stable[node] = [Bool('{}_{}_stable'.format(v, node)) for v in variables]
			variables_activation[node] = Bool('activation_{}'.format(node))
			if self.__mode == 'transient':
				self.__variables_transient[node] = [Bool('{}_{}_transient'.format(v, node)) for v in variables]
		if self.__check_security:
			activation_sum = Sum([If(variables_activation[node], 1, 0) for node in self.__circuit.nodes()])
			self.__s.add(activation_sum <= self.__order)
			self.__s.add(activation_sum > 0)

			variables_checking_gate = {}
			for var in variables:
				variables_checking_gate[var] = Bool('{}_checking_gate'.format(var))
				lst = []
				for node in self.__circuit.nodes():
					if self.__mode == 'transient':
						ind = [str(i) for i in self.__variables_transient[node]].index('{}_{}_transient'.format(var, node))
						lst += [And(variables_activation[node], self.__variables_transient[node][ind])]
					else:
						ind = [str(i) for i in self.__variables_stable[node]].index('{}_{}_stable'.format(var, node))
						lst += [And(variables_activation[node], self.__variables_stable[node][ind])] 
				variables_checking_gate[var] = self.__xor_list(lst)

			checking_secrets = []
			checking_masks = []
			for var in variables_checking_gate:
				v = '_'.join(str(var).split('_')[:2])
				if v in secret_list:
					checking_secrets += [variables_checking_gate[var]]
				elif v in mask_list:
					checking_masks += [variables_checking_gate[var]]
			self.__s.add(And([Or(checking_secrets)] + [Not(v) for v in checking_masks]))

	def __process_circuit(self):
		for node in self.__circuit.nodes():
			node_type = self.__circuit[node]['node_type']
			if node_type == 'port':
				self.__process_port_gate(node)
			elif node_type in ('xor', 'xnor'):
				self.__process_linear_gate(node)
			elif node_type in ('or', 'and'):
				self.__process_nonlinear_gate(node)
			elif node_type in ('dff', 'dffsr'):
				self.__process_register_gate(node)
			elif node_type == 'not':
				self.__process_not_gate(node)
			else:
				logger.error('Unknown node type {} for the node {}'.format(node_type, node))
				exit(-1)

	def __process_linear_gate(self, gate):
		pred = self.__circuit.predecessors(gate)
		if len(pred) == 2:
			in1, in2 = pred
			self.__s.add(self.__z3_xor(self.__variables_stable[in1],
				self.__variables_stable[in2],
				self.__variables_stable[gate]))
			if self.__mode == 'transient':
				self.__s.add(Or(self.__z3_empty(self.__variables_transient[gate]),
				self.__z3_copy(self.__variables_transient[in1], self.__variables_transient[gate]),
				self.__z3_copy(self.__variables_transient[in2], self.__variables_transient[gate]),
				self.__z3_xor(self.__variables_transient[in1], self.__variables_transient[in2], self.__variables_transient[gate])))
		elif len(pred) == 1:
			in1 = pred[0]
			self.__s.add(self.__z3_copy(self.__variables_stable[in1], self.__variables_stable[gate]))
			if self.__mode == 'transient':
				self.__s.add(self.__z3_copy(self.__variables_transient[in1], self.__variables_transient[gate]))
		else:
			logger.error('Number of inputs for the gate {} should be equal to one or two'.format(gate))
			exit(-1)

	def __process_nonlinear_gate(self, gate):
		pred = self.__circuit.predecessors(gate)
		if len(pred) == 2:
			in1, in2 = pred
			self.__s.add(Or(self.__z3_empty(self.__variables_stable[gate]),
				self.__z3_copy(self.__variables_stable[in1], self.__variables_stable[gate]),
				self.__z3_copy(self.__variables_stable[in2], self.__variables_stable[gate]),
				self.__z3_xor(self.__variables_stable[in1], self.__variables_stable[in2], self.__variables_stable[gate])))
			if self.__mode == 'transient':
				self.__s.add(Or(self.__z3_empty(self.__variables_transient[gate]),
					self.__z3_copy(self.__variables_transient[in1], self.__variables_transient[gate]),
					self.__z3_copy(self.__variables_transient[in2], self.__variables_transient[gate]),
					self.__z3_xor(self.__variables_transient[in1], self.__variables_transient[in2], self.__variables_transient[gate])))
		elif len(pred) == 1:
			in1 = pred[0]
			self.__s.add(self.__z3_copy(self.__variables_stable[in1], self.__variables_stable[gate]))
			if self.__mode == 'transient':
				self.__s.add(self.__z3_copy(self.__variables_transient[in1], self.__variables_transient[gate]))
		else:
			logger.error('Number of inputs for the gate {} should be equal to one or two'.format(gate))
			exit(-1)

	def __process_not_gate(self, gate):
		pred = self.__circuit.predecessors(gate)
		if len(pred) == 1:
			in1 = pred[0]
			self.__s.add(self.__z3_copy(self.__variables_stable[in1], self.__variables_stable[gate]))
			if self.__mode == 'transient':
				self.__s.add(self.__z3_copy(self.__variables_transient[in1], self.__variables_transient[gate]))
		else:
			logger.error('Number of inputs for the gate {} should be equal to one'.format(gate))
			exit(-1)

	def __process_port_gate(self, gate):
		lst = []
		neg_lst = []
		for v in self.__variables_stable[gate]:
			var = '_'.join(str(v).split('_')[:-2])
			if var in self.__labels[str(gate)]:
				lst.append(v)
			else:
				neg_lst.append(v)
		self.__s.add(And(lst + [Not(v) for v in neg_lst]))
		if self.__mode == 'transient':
			lst = []
			neg_lst = []
			for v in self.__variables_transient[gate]:
				var = '_'.join(str(v).split('_')[:-2])
				if var in self.__labels[str(gate)]:
					lst.append(v)
				else:
					neg_lst.append(v)
			self.__s.add(And(lst + [Not(v) for v in neg_lst]))

	def __process_register_gate(self, gate):
		pred = self.__circuit.predecessors(gate)
		if len(pred) == 1:
			in1 = pred[0]
			self.__s.add(self.__z3_copy(self.__variables_stable[in1], self.__variables_stable[gate]))
			if self.__mode == 'transient':
				self.__s.add(self.__z3_copy(self.__variables_stable[in1], self.__variables_transient[gate]))
		else:
			logger.error('Number of inputs for the gate {} should be equal to one'.format(gate))
			exit(-1)

	def __analyze_model(self, model_file=None):
		suspicious_gates = []
		m = self.__s.model()
		model = {}
		for var in m:
			model[str(var)] = is_true(m[var])
		for var in model:
			if 'activation_' in var and model[var]:
				suspicious_gates.append('_'.join(var.split('_')[1:]))
		if model_file:
			with open(model_file, 'w') as fn:
				fn.write(dumps(model))
		return suspicious_gates

	def __z3_xor(self, in1, in2, out):
		lst = []
		for i in range(len(in1)):
			lst.append(out[i] == Xor(in1[i], in2[i]))
		return And(lst)

	def __xor_list(self, lst):
		if len(lst) == 2:
			return Xor(lst[0], lst[1])
		else:
			return Xor(lst[0], self.__xor_list(lst[1:]))

	def __z3_copy(self, inp, out):
		lst = []
		for i in range(len(inp)):
			lst.append(out[i] == inp[i])
		return And(lst)

	def __z3_empty(self, out):
		lst = []
		for o in out:
			lst.append(Not(o))
		return And(lst)

	def dump_smt2(self, fn='tmp/out.smt2'):
		with open(fn, 'w') as filename:
			filename.write(self.__s.to_smt2())

	def check(self):
		r = self.__s.check()
		if r == unsat:
			return True, []
		else:
			return False, self.__analyze_model()
