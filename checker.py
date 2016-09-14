#!/usr/bin/env python
import os
import sys
import re
import glob
import pygraphviz as pgv

class Include(object):
	def __init__(self, fullpath):
		self._filename = fullpath
		self._includes = []

	@property
	def includes(self):
		return self._includes
	
	@property
	def filename(self):
		return self._filename
	
	def add_include(self, inc):
		if inc not in self.includes:
			self.includes.append(inc)

	def __repr__(self):
		return "Include(%s)" % (self.filename)

def find_include(request, include_paths):
	print "Finding path for:", request, include_paths
	for root in include_paths:
		full = os.path.join(root, request)
		if os.path.exists(full):
			return full
	
def parse_file(filename, include_paths, parsed_files):
	print "Parsing:", filename
	include = Include(filename)
	parsed_files[filename] = include
	with open(filename, 'r') as fh:
		for line in fh.readlines():
			matches = re.match('#\s*include\s+["<](.*)[>"]', line)
			if matches:
				fname = find_include(matches.group(1), [os.path.dirname(filename)] + include_paths)
				if fname is None:
					fname = matches.group(1)
					if fname in parsed_files:
						inc = parsed_files[fname]
					else:
						inc = Include(fname)
				else:
					if fname not in parsed_files:
						inc = parse_file(fname, include_paths, parsed_files)
					else:
						inc = parsed_files[fname]
				include.add_include(inc)
	return include

def safe_print(include):
	print "--> ", include
	visited = []
	def recurse(child):
		print child.filename
		visited.append(child)
		for x in child.includes:
			if x not in visited:
				recurse(x)
			else:
				print "**", x
	recurse(include)

def create_graph(include):
	visited = []
	G = pgv.AGraph(strict=False, directed=True)
	def recurse(child):
		visited.append(child)
		for x in child.includes:
			if x not in visited:
				G.add_edge(child.filename, x.filename)
				recurse(x)
	recurse(include)

	return G


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Check #includes')
	parser.add_argument('include_dirs', metavar='INCLUDE_PATHS', type=str, nargs='+',
			help='List of include dirs to use for search paths')
	parser.add_argument('--source-dir', dest='sourcedir', action='store',
			required=True, help='Directory to start parsing from')
	parser.add_argument('-R', '--recursive', action='store_true', default=False,
                    help='Recursivly scan the source directory')

	args = parser.parse_args()
	include_paths = args.include_dirs
	roots = []
	includes = {}
	cpp_files = {}

	if args.recursive is True:
		for root, dirnames, filenames in os.walk(args.sourcedir):
			roots.append(root)
	else:
		roots = [args.sourcedir]

	for root in roots:
		for filename in glob.glob(os.path.join(root, '*.c')) + glob.glob(os.path.join(root, '*.cpp')):
			print filename
			cpp_files[filename] = parse_file(filename, include_paths, includes)

	for key, x in cpp_files.iteritems():
		G = create_graph(x)
		G.layout('dot')
		
		G.draw('%s.png' %(key))
