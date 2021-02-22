#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from itertools import combinations, permutations
from mako.template import Template
from os import system
from json import dumps, load

def is_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def apply_labeling(labels, netlist, filename):
	with open(netlist, 'r') as fn:
		netlist = load(fn)
	top_module = netlist['top_module']
	for p in netlist['modules'][top_module]['ports']:
		bits = netlist['modules'][top_module]['ports'][p]['bits']
		l = [labels[str(b)] for b in bits]
		netlist['modules'][top_module]['ports'][p]['label'] = l
	with open(filename, 'w') as fn:
		fn.write(dumps(netlist, indent=True))

def get_fresh_randomness(filename):
	mask = []
	res = {}
	with open(filename, 'r') as fp:
		for line in fp.readlines():
			var,val = line.split(':')
			b = var.split('_')[-1]
			t = val.split()[0]
			if t == 'mask':
				mask += [b]
	m_ind = 1
	for m in mask:
		res[m] = ['m_{}'.format(m_ind)]
		m_ind += 1
	return res

def generate_labeling(filename):
	ordinary_labels = {}
	unimportant = []
	mask = []
	share = {}
	secret = []
	with open(filename, 'r') as fp:
		for line in fp.readlines():
			var,val = line.split(':')
			b = var.split('_')[-1]
			t = val.split()[0]
			if t == 'mask':
				mask += [b]
			elif t == 'secret':
				secret += [b]
			elif t == 'unimportant':
				unimportant += [b]
			elif t == 'share':
				n = val.split()[1]
				if n not in share:
					share[n] = []
				share[n] += [b]
	m_ind = s_ind = u_ind = 1
	for m in mask:
		ordinary_labels[m] = ['m_{}'.format(m_ind)]
		m_ind += 1
	for s in secret:
		ordinary_labels[s] = ['s_{}'.format(s_ind)]
		s_ind += 1
	for u in unimportant:
		ordinary_labels[u] = ['y_{}'.format(u_ind)]
		u_ind += 1
	labels = {** ordinary_labels}
	for s_id in range(1, len(share) + 1):
		for s in share:
			l = len(share[s])
			labels[share[s][0]] = ['s_{}'.format(s_ind)] + \
				['m_{}'.format(i) for i in range(m_ind, m_ind + l - 1)]
			for r in share[s][1:]:
				labels[r] = ['m_{}'.format(m_ind)]
				m_ind += 1
			s_ind += 1
	return [labels]

def generate_optimized_labeling(filename):
	ordinary_labels = {}
	unimportant = []
	mask = []
	share = {}
	secret = []
	labels = []
	with open(filename, 'r') as fp:
		for line in fp.readlines():
			var,val = line.split(':')
			b = var.split('_')[-1]
			t = val.split()[0]
			if t == 'mask':
				mask += [b]
			elif t == 'secret':
				secret += [b]
			elif t == 'unimportant':
				unimportant += [b]
			elif t == 'share':
				n = val.split()[1]
				if n not in share:
					share[n] = []
				share[n] += [b]
	m_ind = s_ind = u_ind = 1
	for m in mask:
		ordinary_labels[m] = ['m_{}'.format(m_ind)]
		m_ind += 1
	for s in secret:
		ordinary_labels[s] = ['s_{}'.format(s_ind)]
		s_ind += 1
	for u in unimportant:
		ordinary_labels[u] = ['y_{}'.format(u_ind)]
		u_ind += 1
	tmp = {** ordinary_labels}
	shares_handled = []
	for s_id in range(1, len(share) + 1):
		flag = True
		for s in share:
			l = len(share[s])
			if flag and s not in shares_handled:
				tmp[share[s][0]] = ['s_{}'.format(s_id)] + \
				['m_{}'.format(i) for i in range(m_ind, m_ind + l - 1)]
				shares_handled += [s]
				flag = False
			else:
				tmp[share[s][0]] = ['m_{}'.format(i) for i in range(m_ind, m_ind + l - 1)]
			for r in share[s][1:]:
				tmp[r] = ['m_{}'.format(m_ind)]
				m_ind += 1
		labels += [tmp]
		tmp = {** ordinary_labels}
	return labels

def parse_verilog(verilog_files, top_module, template_file='template/yosys.txt'):
	template = Template(filename=template_file)
	basename = ''.join(verilog_files.split('.')[:-1])
	files = verilog_files if type(verilog_files) == list else [verilog_files]
	yosys_script = template.render(input_files=files, top_module=top_module)
	with open('tmp/synth.ys', 'w') as filename:
		filename.write(yosys_script)
	system('yosys {}'.format('tmp/synth.ys'))
	with open('tmp/out.json', 'r') as filename:
		circuit_json = load(filename)
	circuit_json['top_module'] = top_module
	with open('{}.json'.format(basename), 'w') as filename:
		filename.write(dumps(circuit_json, indent=True))
	with open('{}.txt'.format(basename), 'w') as filename:
		for port in sorted(circuit_json['modules'][top_module]['ports']):
			bits = [str(i) for i in circuit_json['modules'][top_module]['ports'][port]['bits']]
			for bit in sorted(bits):
				filename.write('{}_{}: unimportant\n'.format(port, bit))

def split_labeling(labeling):
	secrets = []
	secrets_used = []
	res = []
	for gate in labeling:
		for label in labeling[gate]:
			if 's_' in label:
				secrets += [label]
	for secret in secrets:
		labels = {}
		for gate in labeling:
			l = []
			for label in labeling[gate]:
				if 's_' in label:
					if label == secret:
						l += [label]
				else:
					l += [label]
			labels[gate] = l
		res += [labels]
	return res

def get_shares(filename):
	share = {}
	with open(filename, 'r') as fp:
		for line in fp.readlines():
			var,val = line.split(':')
			b = var.split('_')[-1]
			t = val.split()[0]
			if t == 'share':
				n = val.split()[1]
				if n not in share:
					share[n] = []
				share[n] += [b]
	return share

def get_pretty_labeling(labeling, init_file):
	pretty_labeling = ''
	signal_names = {}
	with open(init_file, 'r') as fp:
		for line in fp.readlines():
			signal = line.split(':')[0]
			b = signal.split('_')[-1]
			signal_names[b] = signal
	for l in labeling:
		pretty_labeling += '{}: {}\n'.format(signal_names[l], '+'.join(labeling[l]))
	return pretty_labeling
