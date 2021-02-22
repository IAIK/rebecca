#!/usr/bin/env python3
# Copyright IAIK TU Graz.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from json import load
import networkx as nx
from logger import logger

class CircuitGraph(object):
	def __init__(self, labeling, json_object=None, json_file='tmp/out_labelled.json'):
		self.__redundant_graph = nx.DiGraph()
		self.__graph = nx.DiGraph()
		self.__labeling = labeling
		self.__redundant_circuit = {}
		self.__redundant_circuit['cells'] = {}
		self.__redundant_circuit['wires'] = {}
		self.__circuit = {}
		self.__circuit['cells'] = {}
		self.__ports = {}
		self.__outputs = []

		self.__node_ind = 1
		self.__snodes = {}

		self.__mux_sel = {}
		self.__ignore = []

		if json_object:
			top_module = json_object['top_module']
			self.__parse_json(json_object['modules'][top_module])
		else:
			with open(json_file, 'r') as filename:
				json_object = load(filename)
			top_module = json_object['top_module']
			self.__parse_json(json_object['modules'][top_module])
	
		self.__construct_graph()

	def __parse_json(self, circuit_json):
		netnames = []
		ports = []
		wires = {}

		for p in circuit_json['ports']:
			bits = circuit_json['ports'][p]['bits']
			if circuit_json['ports'][p]['direction'] == 'output':
				self.__outputs += bits
			if 'label' in circuit_json['ports'][p]:
				label = circuit_json['ports'][p]['label']
			else:
				label = None
			self.__ports[p] = bits
			i = 0
			for b in bits:
				ports.append(b)
				self.__add_cell(b, 'port')
				i += 1

		for n in circuit_json['netnames']:
			bits = circuit_json['netnames'][n]['bits']
			for b in bits:
				if b not in netnames:
					netnames.append(b)
				else:
					logger.info('parse json: the netname {} already exists'.
						format(b))

		for c in circuit_json['cells']:
			cell_type = circuit_json['cells'][c]['type']. \
				split('_')[1].lower()
			cell_num = c.split('$')[-1]
			name = '{}_{}'.format(cell_type, cell_num)
			self.__add_cell(name, cell_type)

		for c in circuit_json['cells']:
			cell_type = circuit_json['cells'][c]['type']. \
				split('_')[1].lower()
			cell_num = c.split('$')[-1]
			name = '{}_{}'.format(cell_type, cell_num)
			if 'port_directions' in circuit_json['cells'][c] and \
				'connections' in circuit_json['cells'][c]:
				directions = circuit_json['cells'][c]['port_directions']
				connections = circuit_json['cells'][c]['connections']
				for d in directions:
					if type(connections[d][0]) != int:
						if connections[d][0] not in netnames:
							cname = 'const_{}'.format(connections[d][0])
							netnames.append(cname)
							self.__add_cell(cname, 'const')
						else:
							logger.info('parse json: the const cell {} already exists'.
								format(connections[d][0]))
					if directions[d] == 'input':
							if type(connections[d][0]) != int:
								self.__add_wire('const_{}'.
									format(connections[d][0]), name)
							else:
								if connections[d][0] not in wires:
									wires[connections[d][0]] = {}
								if 'output' not in wires[connections[d][0]]:
									wires[connections[d][0]]['output'] = []
								wires[connections[d][0]]['output'].append(name)
					elif directions[d] == 'output':
						if connections[d][0] not in wires:
							wires[connections[d][0]] = {}
						if 'input' not in wires[connections[d][0]]:
							wires[connections[d][0]]['input'] = []
						wires[connections[d][0]]['input'].append(name)
			else:
				logger.warn('parse json: there is no port or connections for the cell {}'.
					format(c))

		for w in wires:
			if 'input' in wires[w]:
				for i in wires[w]['input']:
					if 'output' in wires[w]:
						for o in wires[w]['output']:
							self.__add_wire(i, o)
					else:
						self.__add_wire(i, w)
						logger.warn('parse json: there is no output for wire {}'.
							format(w))
			else:
				for o in wires[w]['output']:
					self.__add_wire(w, o)
				logger.warn('parse json: there is no input for wire {}'.
					format(w))

	def __add_cell(self, name, ctype, label=None):
		if name not in self.__redundant_circuit['cells']:
			self.__redundant_circuit['cells'][name] = {}
			self.__redundant_circuit['cells'][name]['type'] = ctype
		else:
			logger.warn('add cell: the cell {} ({}) is already exists'.
				format(name, ctype))

	def __add_wire(self, source, to):
		name = '{}-{}'.format(source, to)
		if name not in self.__redundant_circuit['wires']:
			self.__redundant_circuit['wires'][name] = {}
			self.__redundant_circuit['wires'][name]['from'] = source
			self.__redundant_circuit['wires'][name]['to'] = to
		else:
			logger.warn('add wire: the wire {} is alreadey exists'.format(name))

	def __construct_graph(self):
		self.__redundant_graph.clear()
		self.__graph.clear()

		for c in self.__redundant_circuit['cells']:
			ctype = self.__redundant_circuit['cells'][c]['type']
			self.__redundant_graph.add_node(c, node_type=ctype)

		for w in self.__redundant_circuit['wires']:
			self.__redundant_graph.add_edge(
				self.__redundant_circuit['wires'][w]['from'],
				self.__redundant_circuit['wires'][w]['to'])

		isolated_nodes = nx.isolates(self.__redundant_graph)
		logger.warn('remove isolates: {}'.format(isolated_nodes))
		self.__redundant_graph.remove_nodes_from(isolated_nodes)

		for n in self.__redundant_graph.nodes():
			node_type = self.__redundant_circuit['cells'][n]['type']
			if node_type == 'port':
				if 'y_' not in self.__labeling[str(n)][0]:
					self.__circuit['cells'][n] = {}
					self.__circuit['cells'][n]['type'] = node_type
					self.__graph.add_node(n)
					self.__graph[n]['node_type'] = node_type
				else:
					logger.info('port add: skip node {}'.format(n))
			elif node_type in ('and', 'xor', 'dff', 'dffsr'):
				self.__circuit['cells'][n] = {}
				self.__circuit['cells'][n]['type'] = node_type
				self.__graph.add_node(n)
				self.__graph[n]['node_type'] = node_type
			elif node_type == 'or':
				self.__circuit['cells'][n] = {}
				self.__circuit['cells'][n]['type'] = 'and'
				self.__graph.add_node(n)
				self.__graph[n]['node_type'] = node_type
			elif node_type == 'mux':
				self.__circuit['cells'][n] = {}
				self.__circuit['cells'][n]['type'] = 'mux'
				self.__graph.add_node(n, node_type=node_type)
			elif node_type == 'const':
				pass
			elif node_type == 'not':
				pass
			else:
				logger.error('unknown type {} of the node {}'.format(node_type, n))
				exit()
		for n in self.__redundant_graph.nodes():
			node_type = self.__redundant_circuit['cells'][n]['type']
			if node_type == 'not':
				for p in self.__redundant_graph.predecessors(n):
					for o in self.__redundant_graph.successors(n):
						if p in self.__circuit['cells'] and o in self.__circuit['cells']:
							self.__graph.add_edge(p, o)

		for e in self.__redundant_graph.edges():
			if e[0] in self.__graph.nodes() and e[1] in self.__graph.nodes():
				self.__graph.add_edge(*e)

		for n in self.__graph.nodes():
			s = len(self.__graph.successors(n))
			p = len(self.__graph.predecessors(n))
			if s == 0 and p == 0:
				logger.warn('Construct graph: node {} is not connected'.format(n))
			t = self.__circuit['cells'][n]
			if t in ('and', 'xor') and (s < 1 or p != 2):
				logger.warn(
					'Construct graph: node {} is suspicious: predecessors = {}, successors = {}'.
					format(n, p, s))

	def write_graph(self, graph=None, fname=None):
		if graph == None:
			graph = self.__graph
		dot = 'strict digraph  {\n'
		for e in graph.edges():
			if e[1] != 'node_type':
				i, o = str(e[0]), str(e[1])
				dot += '{} -> {};\n'.format(i, o)
		dot += '}\n'
		with open(fname if fname else 'tmp/graph.dot', 'w') as filename:
			filename.write(dot)

	def get_all_predecessors(self, node):
		predecessors = []
		for p in self.__graph.predecessors(node):
			predecessors.append(p)
			predecessors += self.get_all_predecessors(p)
		return set(predecessors)

	def get_all_successors(self, node):
		successors = []
		for p in self.__graph.successors(node):
			if p != 'node_type':
				successors.append(p)
				successors += self.get_all_successors(p)
		return set(successors)

	def get_graph(self):
		return self.__graph

	def get_redundant_graph(self):
		return self.__redundant_graph

	def get_circuit(self):
		return self.__circuit

	def get_outputs(self):
		outputs = []
		trash = set(['node_type'])
		for n in self.__graph.nodes():
			if n != 'node_type':
				if len(set(self.__graph.successors(n)) - trash) == 0:
					outputs += [n]
		return outputs

