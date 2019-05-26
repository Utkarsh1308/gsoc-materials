from multidiff.Ansi import Ansi
import binascii
import html
import textwrap
import os

class Render():
	def __init__(self, encoder='hexdump', color='html', width='82'):
		'''Configure the output encoding and coloring method of this rendering object'''
		if   color == 'ansi':
			self.highligther = ansi_colored
		elif color == 'html':
			self.highligther = html_colored

		if   encoder == 'hexdump':
			self.encoder = HexdumpEncoder
		elif encoder == 'hex':
			self.encoder = HexEncoder
		elif encoder == 'utf8':
			self.encoder = Utf8Encoder

		self.width = width

	def render(self, model, diff):
		'''Render the diff in the given model into a UTF-8 String'''
		result = self.encoder(self.highligther)
		obj1 = model.objects[diff.target-1]
		obj2 = model.objects[diff.target]
		for op in diff.opcodes:
			data1 = obj1.data[op[1]:op[2]]
			data2 = obj2.data[op[3]:op[4]]
			if type(data2) == bytes:
				result.append(data1, data2, op[0], self.width)
			elif type(data2) == str:
				result.append(bytes(data1, "utf8"), bytes(data2, "utf8"), op[0], self.width)
		return result.final()

	def dumps(self, model):
		'''Dump all diffs in a model. Mostly good for debugging'''
		dump = ""
		for diff in model.diffs:
			dump += self.render(model, diff) + '\n'
		return dump

class Utf8Encoder():
	'''A string (utf8) encoder for the data'''
	def __init__(self, highligther):
		self.highligther = highligther
		self.output = ''

	def append(self, data, color):
		self.output += self.highligther(str(data, 'utf8'), color)

	def final(self):
		return self.output

class HexEncoder():
	'''A hex encoder for the data'''
	def __init__(self, highligther):
		self.highligther = highligther
		self.output = ''
	def append(self, data, color):
		data = str(binascii.hexlify(data),'utf8')
		self.output += self.highligther(data, color)

	def final(self):
		return self.output

class HexdumpEncoder():
	'''A hexdump encoder for the data'''
	def __init__(self, highligther):
		self.highligther = highligther
		self.body = ''
		self.addr = 0
		self.rowlen = 0
		self.hexrow = ''
		self.skipspace = False

	def append(self, data1, data2, color, width):
		if len(data2) == 0:
			self._append(data1, data2, color, width)
		while len(data2) > 0:
			if self.rowlen == 16:
				self._newrow()
			consumed = self._append(data1[:16 - self.rowlen], data2[:16 - self.rowlen], color, width)
			data2 = data2[consumed:]

	def _append(self, data1, data2, color, width):
		# <deletion>
		if len(data2) == 0:
			hexs = str(binascii.hexlify(data1), 'utf8')
			hexs = ' '.join([hexs[i:i+2] for i in range(0, len(hexs), 2)])
		else:
			self._add_hex_space()
			#encode to hex and add some spaces
			hexs = str(binascii.hexlify(data2), 'utf8')
			hexs = ' '.join([hexs[i:i+2] for i in range(0, len(hexs), 2)])

		self.hexrow += self.highligther(hexs, color)
		if len(self.hexrow) > int(width):
			self.hexrow = textwrap.fill(self.hexrow, int(width))
		self.rowlen += len(data2)
		return len(data2)

	def _newrow(self):
#		self._add_hex_space()
		if self.addr != 0:
			self.body = self.body
		ops = ['insert', 'delete', 'replace']
		if any(ext in self.hexrow for ext in ops):
			self.body += "\n{:06x}:{:s}".format(
			self.addr, self.hexrow);
		self.addr += 16
		self.rowlen = 0
		self.hexrow = ''

	def _add_hex_space(self):
		if self.skipspace:
			self.skipspace = False
		else:
			self.hexrow += ' '

	def final(self):
#		self.hexrow += 3*(16 - self.rowlen) * ' '
		self._newrow()
		return self.body

def html_colored(string, op):
	if   op == 'equal':
		return string
	return "<" + op + ">" + html.escape(string) + "</" + op + ">"
