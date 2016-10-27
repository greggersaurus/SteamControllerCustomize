#!/usr/bin/env python

import sys 
import getopt
import struct

class FirmwareParser:
	"""
	Takes Steam Controller firmware and decodes it as best as possible.
	"""

	RESET_VEC_ADDR = 0x04
	NMI_VEC_ADDR = 0x08
	HARD_FAULT_VEC_ADDR = 0x0C
	SV_CALL_VEC_ADDR = 0x2C
	PEND_SV_VEC_ADDR = 0x38
	SYS_TICK_VEC_ADDR = 0x3C
	IRQ_N_VEC_ADDR = [
		0x40, 0x44, 0x48, 0x4C, 0x50, 0x54, 0x58, 0x5C,
		0x60, 0x64, 0x68, 0x6C, 0x70, 0x74, 0x78, 0x7C,
		0x80, 0x84, 0x88, 0x8C, 0x90, 0x94, 0x98, 0x9C,
		0xA0, 0xA4, 0xA8, 0xAC, 0xB0, 0xB4, 0xB8, 0xBC,
		]

	# List of all data words read from firmware file. Combined and
	#  categorized as best as possible.
	dataWords = []

##	traceBuffer # Array of instructions that have been execute during emulation
##	# TODO: create functions (read/write) to access memory (controls if emulator try to access inappropriate space, etc.)
##			# 0x0000 0000 (SIZE 0x0002 0000) On Chip Flash
##			binFile #TODO: able to query offset in file, or need separate variable (i.e. programCounter)?
##				# 0x0000 0000 - 0x0000 00BC Vector Table
##			vectorTable # Array of vector addresses? Create enums as logical means to access?
##		SRAM0 	# 0x1000 0000 (SIZE 0x0000 2000) SRAM0
##			stackBuffer # Memory for what is pushed on the stack
##			# 0x1FFF 0000 (SIZE 0x0000 4000) boot ROM
##		SRAM1 	# 0x2000 0000 (SIZE 0x0000 0800) SRAM1
##		SRAM2 	# 0x2000 4000 (SIZE 0x0000 0800) SRAM2
##			# 0x4000 0000 (SIZE 0x0000 4000) APB Peripheral I2C Bus
##			# 0x4000 4000 (SIZE 0x0000 4000) APB Peripheral WWDT
##			# 0x4000 8000 (SIZE 0x0000 4000) APB Peripheral USART/SMART CARD
##			# 0x4000 C000 (SIZE 0x0000 4000) APB Peripheral 16-bit counter/timer 0
##			# 0x4001 0000 (SIZE 0x0000 4000) APB Peripheral 16-bit counter/timer 1
##			# 0x4001 4000 (SIZE 0x0000 4000) APB Peripheral 32-bit counter/timer 0
##			# 0x4001 8000 (SIZE 0x0000 4000) APB Peripheral 32-bit counter/timer 1
##			# 0x4001 C000 (SIZE 0x0000 4000) APB Peripheral ADC
##			# 0x4003 8000 (SIZE 0x0000 4000) APB Peripheral PMU
##			# 0x4003 C000 (SIZE 0x0000 4000) APB Peripheral flash/EEPROM controller
##			# 0x4004 0000 (SIZE 0x0000 4000) APB Peripheral SSP0
##			# 0x4004 4000 (SIZE 0x0000 4000) APB Peripheral IOCON
##			# 0x4004 8000 (SIZE 0x0000 4000) APB Peripheral system control
##			# 0x4004 C000 (SIZE 0x0000 4000) APB Peripheral GPIO interrupts
##			# 0x4005 8000 (SIZE 0x0000 4000) APB Peripheral SSP1 
##			# 0x4005 C000 (SIZE 0x0000 4000) APB Peripheral GPIO GROUP0 INT
##			# 0x4006 0000 (SIZE 0x0000 4000) APB Peripheral GPIO GROUP1 INT
##			# 0x4008 0000 (SIZE 0x0000 4000) USB
##			# 0x5000 0000 (SIZE 0x0000 4000) GPIO
##			# 0xE000 0000 (SIZE 0x0010 0000) Private Peripheral Bus
##	# TODO registers for emulation
##		# Stack pointer
##		# Program counter

	def __init__(self, binFilename):
		"""
		Constructor
			
		Params:
		binFilename Path to binary firmware file
		"""

		# Create the initial list of dataWords by reading the fw file
		binFile = open(binFilename, 'rb')

		offset = 0
		word16 = self.__read16(binFile)	
		while (word16 != -1):
			self.dataWords += [DataWord(word16, offset)]
			offset += 2
			word16 = self.__read16(binFile)	
	
		binFile.close()

		# Identify vector table data 
		self.__identifyVectorTable()

		# Identify start instructions based on specific vector entries
		dataWord = self.__getDataWord(self.RESET_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		dataWord = self.__getDataWord(self.NMI_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		dataWord = self.__getDataWord(self.HARD_FAULT_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		dataWord = self.__getDataWord(self.SV_CALL_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		dataWord = self.__getDataWord(self.PEND_SV_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		dataWord = self.__getDataWord(self.SYS_TICK_VEC_ADDR)
		self.__markInstruction(dataWord.binData)
		for i, addr in enumerate(self.IRQ_N_VEC_ADDR):
			dataWord = self.__getDataWord(addr)
			self.__markInstruction(dataWord.binData)

		# Set children for 32-bit instructions so that instruction 
		#  identification will have all potential necessary data
#TODO

		# Identify possible instructions
		for data in self.dataWords:
			try:
				data.instruction = Instruction(data)
			except ValueError:
				data.instruction = None

	def __read16(self, inFile):
		"""
		Read 16 bit word (little endian) from file

		Params:
		inFile File to read from
		"""

		# Read byte 0
		byte0 = inFile.read(1)
		if (byte0 == ""):
			return -1
	
		# Read byte 1
		byte1 = inFile.read(1) 
		if (byte1 == ""):
			return struct.unpack('B', byte0)[0]
		
		retval = struct.unpack('B', byte1)[0] << 8 | struct.unpack('B', byte0)[0]

		return retval

	def __str__(self):
		retval = ''

		for data in self.dataWords:
			retval += str(data)
		
		return retval

	def __getDataWord(self, addr):
		"""
		Get the DataWord at the given address in firmware

		Params:
		addr Address of DataWord
		"""

		return self.dataWords[addr/2]

	def __identifyVectorTable(self):
		"""
		Identify DataWords that are part of Vector Table
		"""

		self.__setVectorTableEntry(0x00, 'Initial SP Value')
		self.__setVectorTableEntry(self.RESET_VEC_ADDR, 'Reset')
		self.__setVectorTableEntry(self.NMI_VEC_ADDR, 'NMI')
		self.__setVectorTableEntry(self.HARD_FAULT_VEC_ADDR, 'Hard Fault')
		self.__setVectorTableEntry(0x10, 'RESERVED')
		self.__setVectorTableEntry(0x14, 'RESERVED')
		self.__setVectorTableEntry(0x18, 'RESERVED')
		self.__setVectorTableEntry(0x1C, 'RESERVED (Checksum)')
		self.__setVectorTableEntry(0x20, 'RESERVED')
		self.__setVectorTableEntry(0x24, 'RESERVED')
		self.__setVectorTableEntry(0x28, 'RESERVED')
		self.__setVectorTableEntry(self.SV_CALL_VEC_ADDR, 'SVCall')
		self.__setVectorTableEntry(0x30, 'RESERVED')
		self.__setVectorTableEntry(0x34, 'RESERVED')
		self.__setVectorTableEntry(self.PEND_SV_VEC_ADDR, 'PendSV')
		self.__setVectorTableEntry(self.SYS_TICK_VEC_ADDR, 'SysTick')
		for i, addr in enumerate(self.IRQ_N_VEC_ADDR):
			self.__setVectorTableEntry(addr, 'IRQ' + str(i))

	def __setVectorTableEntry(self, addr, desc):
		"""
		Set the DataWord to a Vector Table Entry

		Params:
		addr Address of Vector Table entry
		desc Describes the vector
		"""

		dataWordLo = self.__getDataWord(addr)
		dataWordHi = self.__getDataWord(addr+2)

		if (dataWordLo.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (dataWordLo.offset, dataWordLo.dataType))	
		if (dataWordHi.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (dataWordHi.offset, dataWordHi.dataType))	

		dataWordLo.decodeString = desc
		dataWordLo.combine(dataWordHi)
		dataWordLo.dataType = DataWord.TYPE_VECTOR_TABLE

	def __markInstruction(self, addr):
		"""
		Mark that DataWord at given address is a known instruction

		Params:
		addr The address of the (potential) instruction
		"""

		if (addr == 0):
			# It is valid for vector table to pointer to NULL. Ignore it
			return

		dataWord = self.__getDataWord(addr)

		# Checkif it was already decoded
		if (dataWord.dataType == DataWord.TYPE_INSTRUCTION):
			return

		# Check if the addr does not point to an already labeled DataWord
		if (dataWord.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (dataWord.offset, dataWord.dataType))	
			
		# Mark this DataWord is an instruction
		dataWord.dataType = DataWord.TYPE_INSTRUCTION
		
class DataWord(object):
	"""
	Class to encapsulate a 32 or 16-bit data word read from the firmware file.
	"""

	# To be used for setting dataType
	TYPE_UNKNOWN = "Unknown"
	TYPE_VECTOR_TABLE = "Vector Table"
	TYPE_INSTRUCTION = "Instruction"
	TYPE_DATA = "Data"

	# Raw binary data from firmware file
	__binData = 0
	# Memory location in firmware where this data word can be found
	__offset = 0
	# Defines how the data has been categorized
	__dataType = TYPE_UNKNOWN
	# Type specific string to make understanding this instruction easier
	decodeString = ''
	# Set to another DataWord if this has been combined
	__parent = None
	# Tells us whether this is a 32-bit DataWord or not, and where the 
	#  upper 16-bits of data are if this is 32-bit
	__child = None
	# Decode of __binData into an instruction. Check type to know is 100% valid.
	instruction = None

	def __init__(self, binData, offset):
		"""
		Constructor

		Params:
		binData Raw binary data read from firmware file
		offset Memory location offset in firmware where this data 
			was read from
		"""

		self.__binData = binData
		self.__offset = offset

	@property
	def dataType(self):
		return self.__dataType

	@dataType.setter
	def dataType(self, value):
		if (self.__child != None):
			self.__child.dataType = value

		if (self.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (self.offset, self.dataType))	

		self.__dataType = value 

	@property
	def offset(self):
		return self.__offset

	@property
	def binData(self):
		retval = 0;

		if (self.__child != None):
			retval = self.__child.binData << 16;

		retval |= self.__binData

		return retval

	def __str__(self):
		if (self.__parent != None):
			return ''

		retval = ''

		# Offset address in hex
		retval += '{0:06x}: '.format(self.offset)

		# Upper 16 bits of raw binary data
		if (self.__child != None):
			retval += ' {0:04x}'.format(self.__child.binData)
		else:
			retval += '     '

		# Lower 16 bits of raw binary data
		retval += ' {0:04x}'.format(self.binData%0x10000)

		# The identified data type
		retval += ' {0:>16s}'.format(self.dataType)
		
		# More specific info on the data
		retval += '	' + self.decodeString

		if (self.instruction != None):
			if (self.dataType == DataWord.TYPE_UNKNOWN):
				retval += 'Possible Instruction: '

			retval += self.instruction.description
			retval += ' ' + str(self.instruction)

		retval += '\n'

		return retval

	def combine(self, dataWord):
		"""
		Combine the given DataWord into this word. 

		Params:
		dataWord DataWord higher in memory than self
		"""

		if (self.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (self.offset, self.dataType))	
		if (dataWord.dataType != DataWord.TYPE_UNKNOWN):
			raise ValueError('DataWord at offset 0x%x is of type %s' % (dataWord.offset, dataWord.dataType))	
			
		self.__child = dataWord
		dataWord.__parent = self
			

class Instruction:
	"""
	Represents an assembly instruction
	"""

	description = ''
	args = []

	def __init__(self, dataWord):
		"""
		dataWord
		"""
		self.args = []

		binData = dataWord.binData 

		if ((binData & 0xF800) == 0x4800):
			self.__decodeLoadFromLiteralPool(dataWord)
		elif ((binData & 0xF000) == 0x5000 or \
			(binData & 0xE000) == 0x6000 or \
			(binData & 0xE000) == 0x8000): 
			self.__decodeLoadStoreSingle(dataWord)
		else:
			raise ValueError('Not a valid instruction')	
		
	def __decodeLoadFromLiteralPool(self, dataWord):
		self.description = 'Load Register (literal)'

		self.args.append('LDR')

		self.args.append('R' + str(0x3 & (dataWord.binData >> 8)))

		arg = (0xFF & dataWord.binData) << 2
		arg += dataWord.offset + 4
		self.args.append(hex(arg))

#TODO Once instruction is decoded, how to we map action for 'execution' (i.e. so we can mark LDR locations as potential data (though this does not preclude them from being instructions as well?) or jump location as instructions)
# Note: LDR is a 32-bit load
# Make assumption that loads mean those 32 bits are data (we will gen exception if we reach them as an exception later and can correct if needed)

	def __decodeLoadStoreSingle(self, dataWord):
		self.description = 'Load/Store'
		#TODO: decode further and call more sub functions

	def is32bit(dataWord16):
		"""
		Check if 16-bit data word indicates it is part of 32-bit instruction

		Params:
		dataWord16 16-bit data word
		"""	
		retval = False

		bitsToCheck = dataWord16 & 0xF800
	
		if (bitsToCheck == 0xF100 or bitsToCheck == 0xF000 or bitsToCheck == 0xE100):
			retval = True

		return retval 

	def __str__(self):
		retval = ''	

		for arg in self.args:
			retval += arg + ' '
		
		return retval

def main(argv):
	print "Hello World"

	try:
		opts, args = getopt.getopt(argv,"hi:",["inputfile="])
	except getopt.GetoptError:
		print 'FirmwareParser.py -i <inputFile>'
	for opt, arg in opts:
		if opt == '-h':
			print 'FirmwareParser.py -i <inputFile>'
		elif opt in ("-i", "--inputfile"):
			parser = FirmwareParser(arg)
			print parser


if __name__ == "__main__":
	main(sys.argv[1:])