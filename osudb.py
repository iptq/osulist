"""
Utilities for reading OSU .db files
"""

import struct
from datetime import datetime, timedelta
from typing import ByteString

class OsuDb(object):
	@classmethod
	def read_from_file(cls, path):
		with open(path, "rb") as f:
			return cls.read_from_bytes(f.read())

	@classmethod
	def read_from_bytes(cls, b):
		return OsuDb(b)

	def __init__(self, b):
		self.bytes = b
		self.pos = 0
	
	def process(self):
		self.version = self._read_i32()
		self.n_collections = self._read_i32()

		self.collections = []
		for i in range(self.n_collections):
			name = self._read_string()
			n_beatmaps = self._read_i32()

			beatmaps = []
			for j in range(n_beatmaps):
				md5 = self._read_string()
				beatmaps.append(md5)

			self.collections.append((name, beatmaps))

	def _read_datetime(self) -> datetime:
		ticks = self._read_i64()
		print(ticks)
		return datetime(1, 1, 1) + timedelta(microseconds = ticks // 10)

	def _read_string(self) -> str:
		is_present = self._read_bool()
		if not is_present:
			return ""
		
		length = self._read_uleb128()
		print(f"reading string of length {length}")
		b = self._read_n_bytes(length)
		return b.decode("utf-8")

	def _read_uleb128(self) -> int:
		res = 0
		shift = 0
		while True:
			b = self._read_n_bytes(1)[0]
			lo7 = b & 0x7f
			hi8 = b >> 7
			res |= lo7 << shift
			if hi8 == 0:
				break
			shift += 7
		return res

	def _read_bool(self) -> bool:
		n, = struct.unpack("<B", self._read_n_bytes(1))
		return n

	def _read_i32(self) -> int:
		n, = struct.unpack("<I", self._read_n_bytes(4))
		return n

	def _read_i64(self) -> int:
		n, = struct.unpack("<Q", self._read_n_bytes(8))
		return n

	def _read_n_bytes(self, n) -> ByteString:
		i = self.pos
		self.pos += n
		return self.bytes[i:self.pos]

