"""
Created on 6 May 2013

@author: mike
"""

import os.path

from volatility.framework import interfaces, exceptions


class BufferDataLayer(interfaces.layers.DataLayerInterface):
    """A DataLayer class backed by a buffer in memory, designed for testing and swift data access"""

    def __init__(self, context, name, buffer):
        interfaces.layers.DataLayerInterface.__init__(self, context, name)
        self._buffer = self._type_check(buffer, bytes)

    @property
    def maximum_address(self):
        """Returns the largest available address in the space"""
        return len(self._buffer) - 1

    @property
    def minimum_address(self):
        """Returns the smallest available address in the space"""
        return 0

    def is_valid(self, offset):
        """Returns whether the offset is valid or not"""
        return self.minimum_address <= offset <= self.maximum_address

    def read(self, address, length, pad = False):
        """Reads the data from the buffer"""
        return self._buffer[address:address + length]

    def write(self, address, data):
        """Writes the data from to the buffer"""
        self._type_check(data, bytes)
        self._buffer = self._buffer[:address] + data + self._buffer[address + len(data):]


class FileLayer(interfaces.layers.DataLayerInterface):
    """a DataLayer backed by a file on the filesystem"""

    def __init__(self, context, name, filename):
        interfaces.layers.DataLayerInterface.__init__(self, context, name)

        self._file = open(filename, "r+b")
        self._size = os.path.getsize(filename)

    @property
    def maximum_address(self):
        """Returns the largest available address in the space"""
        # Zero based, so we return the size of the file minus 1
        return self._size - 1

    @property
    def minimum_address(self):
        """Returns the smallest available address in the space"""
        return 0

    def is_valid(self, offset):
        """Returns whether the offset is valid or not"""
        return self.minimum_address <= offset <= self.maximum_address

    def read(self, offset, length, pad = False):
        """Reads from the file at offset for length"""
        if not self.is_valid(offset):
            raise exceptions.InvalidAddressException("Offset outside of the " + self.name + " file boundaries")
        if not self.is_valid(offset + (length - 1)):
            raise exceptions.InvalidAddressException("Final offset outside of the " + self.name + " file boundaries")
        if length < 0:
            raise TypeError("Length must be positive")
        self._file.seek(offset)
        data = self._file.read(length)
        if len(data) < length:
            if pad:
                data += (b"\x00" * (length - len(data)))
            else:
                raise exceptions.InvalidAddressException("Could not read sufficient bytes from the " +
                                                         self.name + " file")
        return data

    def write(self, offset, data):
        """Writes to the file

           This will technically allow writes beyond the extent of the file
        """
        if not self.is_valid(offset):
            raise exceptions.InvalidAddressException("Offset outside of the " + self.name + " file boundaries")
        self._file.seek(offset)
        self._file.write(data)