#!/usr/bin/env python
import struct, sys, MySQLdb, time
from collections import namedtuple

# SETTINGS
inverter_private_key = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
db_user = "dbuser"
db_pass = "dbpassword"
db_name = "solaredge"



#############################################################################################

crcTable = (
0x0000,  0xc0c1,  0xc181,  0x0140,  0xc301,  0x03c0,  0x0280,  0xc241,
0xc601,  0x06c0,  0x0780,  0xc741,  0x0500,  0xc5c1,  0xc481,  0x0440,
0xcc01,  0x0cc0,  0x0d80,  0xcd41,  0x0f00,  0xcfc1,  0xce81,  0x0e40,
0x0a00,  0xcac1,  0xcb81,  0x0b40,  0xc901,  0x09c0,  0x0880,  0xc841,
0xd801,  0x18c0,  0x1980,  0xd941,  0x1b00,  0xdbc1,  0xda81,  0x1a40,
0x1e00,  0xdec1,  0xdf81,  0x1f40,  0xdd01,  0x1dc0,  0x1c80,  0xdc41,
0x1400,  0xd4c1,  0xd581,  0x1540,  0xd701,  0x17c0,  0x1680,  0xd641,
0xd201,  0x12c0,  0x1380,  0xd341,  0x1100,  0xd1c1,  0xd081,  0x1040,
0xf001,  0x30c0,  0x3180,  0xf141,  0x3300,  0xf3c1,  0xf281,  0x3240,
0x3600,  0xf6c1,  0xf781,  0x3740,  0xf501,  0x35c0,  0x3480,  0xf441,
0x3c00,  0xfcc1,  0xfd81,  0x3d40,  0xff01,  0x3fc0,  0x3e80,  0xfe41,
0xfa01,  0x3ac0,  0x3b80,  0xfb41,  0x3900,  0xf9c1,  0xf881,  0x3840,
0x2800,  0xe8c1,  0xe981,  0x2940,  0xeb01,  0x2bc0,  0x2a80,  0xea41,
0xee01,  0x2ec0,  0x2f80,  0xef41,  0x2d00,  0xedc1,  0xec81,  0x2c40,
0xe401,  0x24c0,  0x2580,  0xe541,  0x2700,  0xe7c1,  0xe681,  0x2640,
0x2200,  0xe2c1,  0xe381,  0x2340,  0xe101,  0x21c0,  0x2080,  0xe041,
0xa001,  0x60c0,  0x6180,  0xa141,  0x6300,  0xa3c1,  0xa281,  0x6240,
0x6600,  0xa6c1,  0xa781,  0x6740,  0xa501,  0x65c0,  0x6480,  0xa441,
0x6c00,  0xacc1,  0xad81,  0x6d40,  0xaf01,  0x6fc0,  0x6e80,  0xae41,
0xaa01,  0x6ac0,  0x6b80,  0xab41,  0x6900,  0xa9c1,  0xa881,  0x6840,
0x7800,  0xb8c1,  0xb981,  0x7940,  0xbb01,  0x7bc0,  0x7a80,  0xba41,
0xbe01,  0x7ec0,  0x7f80,  0xbf41,  0x7d00,  0xbdc1,  0xbc81,  0x7c40,
0xb401,  0x74c0,  0x7580,  0xb541,  0x7700,  0xb7c1,  0xb681,  0x7640,
0x7200,  0xb2c1,  0xb381,  0x7340,  0xb101,  0x71c0,  0x7080,  0xb041,
0x5000,  0x90c1,  0x9181,  0x5140,  0x9301,  0x53c0,  0x5280,  0x9241,
0x9601,  0x56c0,  0x5780,  0x9741,  0x5500,  0x95c1,  0x9481,  0x5440,
0x9c01,  0x5cc0,  0x5d80,  0x9d41,  0x5f00,  0x9fc1,  0x9e81,  0x5e40,
0x5a00,  0x9ac1,  0x9b81,  0x5b40,  0x9901,  0x59c0,  0x5880,  0x9841,
0x8801,  0x48c0,  0x4980,  0x8941,  0x4b00,  0x8bc1,  0x8a81,  0x4a40,
0x4e00,  0x8ec1,  0x8f81,  0x4f40,  0x8d01,  0x4dc0,  0x4c80,  0x8c41,
0x4400,  0x84c1,  0x8581,  0x4540,  0x8701,  0x47c0,  0x4680,  0x8641,
0x8201,  0x42c0,  0x4380,  0x8341,  0x4100,  0x81c1,  0x8081,  0x4040)

def calcCrc(data):
    crc = 0x5a5a
    for d in data:
         crc = crcTable[(crc ^ ord(d)) & 0xff] ^ (crc >> 8)
    return crc

#############################################################################################

SEDataInverter = namedtuple("SEDataInverter",
    "uptime interval Temp EdayAC DeltaEdayAC Vac Iac Freq EdayDC DeltaEdayDC Vdc Idc Etotal_f Ircd "
    "L1 CosPhi Mode GndFltR f1 IoutDC L2 L3 Pactive Papparent Preactive f2 f3 L4 Etotal_i L5")
SEDataInverter.size = 120
SEDataInverter.parse = classmethod(
    lambda cls, data, offset=0:
        cls._make(struct.unpack("<LLffffffLLfLffLfLfffLLfffffLLL", data[offset:offset+cls.size])))

#############################################################################################

def iterbytes(byte, data):
  """Yield each element of data (if not None), followed by byte."""
  if data is not None:
    for b in data:
      yield b
  yield byte
#iterbytes

#############################################################################################

from Crypto.Cipher import AES
class SEDecrypt:
    def __init__(self, key, msg0503):
        """
        Initialise a SolarEdge communication decryption object.

        key:     a 16-byte string which consists of the values of
                 parameters 0239, 023a, 023b, and 023c.
        msg0503: a 34-byte string with the contents of a 0503 message.
        """
        enkey1 = map(ord, AES.new(key).encrypt(msg0503[0:16]))
        self.cipher = AES.new("".join(map(chr,
            (enkey1[i] ^ ord(msg0503[i+16]) for i in range(16)))))

    def decrypt(self, msg003d):
        """
        msg003d: the contents of the 003d message to decrypt.

        Returns a tuple(int(sequenceNumber), string(data)).
        """
        rand1 = map(ord, msg003d[0:16])
        rand = map(ord, self.cipher.encrypt(msg003d[0:16]))
        msg003d = map(ord, msg003d)
        posa = 0
        posb = 16
        while posb < len(msg003d):
            msg003d[posb] ^= rand[posa]
            posb += 1
            posa += 1
            if posa == 16:
                posa = 0
                for posc in range(15, -1, -1):
                    rand1[posc] = (rand1[posc] + 1) & 0x0FF
                    if rand1[posc]:
                        break
                rand = map(ord, self.cipher.encrypt("".join(map(chr, rand1))))
        return (msg003d[16] + (msg003d[17] << 8),
                "".join(map(chr, (msg003d[i+22] ^ msg003d[18+(i&3)]
                    for i in range(len(msg003d)-22)))))

#############################################################################################

class SEParser:
  def __init__(self, key=None, decryptor=None, msg_filt=None):
    self.key = key
    self.decryptor = decryptor
    self.msg_filt = msg_filt
    self.last_msg = ""

  def get_messages(self, byteiterator):
    state = 0
    data = []
    datafirst = False
    for byte in byteiterator:
      for byte in iterbytes(byte, data if datafirst else None):
        if datafirst:
          data = []
        datafirst = False
        data.append(byte)
        if state == 0:
          # Skipping to next barker.
          if len(data) >= 4 and "".join(data[-4:]) == "\x12\x34\x56\x79":
            state = 1
            if len(data) > 4:
              eprint("Warning! Skipping %i mysterious bytes!" % (len(data)-4))
              eprint(" ".join("%02x" % ord(x) for x in data[:-4]))
              data = data[-4:]
        elif state == 1:
          # Reading length.
          if len(data) == 6:
            state = 2
            length = struct.unpack("<H", "".join(data[-2:]))[0]
        elif state == 2:
          # Reading length inverted.
          if len(data) == 8:
            state = 3
            if ((~struct.unpack("<H", "".join(data[-2:]))[0]) & 0xFFFF) != length:
              eprint("Warning! Length value mismatch! Skipping over barker...")
              data = data[4:]
              state = 1 if "".join(data) == "\x12\x34\x56\x79" else 0
        elif state == 3:
          # Reading sequence number.
          if len(data) == 10:
            state = 4
        elif state == 4:
          # Reading sender ID.
          if len(data) == 14:
            state = 5
        elif state == 5:
          # Reading receiver ID.
          if len(data) == 18:
            state = 6
        elif state == 6:
          # Reading message type.
          if len(data) == 20:
            state = 7 if length else 8
        elif state == 7:
          # Reading message content.
          if len(data) == 20 + length:
            state = 8
        elif state == 8:
          # Reading message checksum.
          if len(data) == 20 + length + 2:
            data = "".join(data)
            hdr = struct.unpack("<LHHHLLH", data[:20])
            # Check the checksum.
            if struct.unpack("<H", data[-2:])[0] != calcCrc(
                struct.pack(">HLLH", *hdr[3:7]) + data[20:-2]):
              eprint("Warning! Checksum failure, skipping over barker...")
              data = list(data[4:])
              datafirst = True  # Reparse data.
            else:
              if hdr[6] == 0x003d and self.decryptor:
                # If we find a 003d message, decrypt it.
                for msg in self.get_messages(self.decryptor.decrypt(data[20:20+length])[1]):
                  yield msg
              elif self.last_msg != data:  # Deduplication.
                # If we find an unencrypted message, parse that.
                self.last_msg = data
                if self.msg_filt is None or hdr[6] in self.msg_filt:
                  yield (hdr, data[20:20+length])
                if hdr[6] == 0x0503 and self.key:
                  # If we find a 0503 message, initialise the decryptor as well.
                  self.decryptor = SEDecrypt(self.key, data[20:20+length])
              data = []
            state = 0
    if len(data):
      eprint("Warning! Got %i mysterious bytes left! (state=%i)" % (len(data), state))
      eprint(" ".join("%02x" % ord(x) for x in data))

#############################################################################################

class PCAPParser:
  def __init__(self):
    self.tcp_streams = {}

  def prune_silent_streams(self, pcaptime):
    for sid in self.tcp_streams.keys():
      if pcaptime - self.tcp_streams[sid][2] > 3600:
        del self.tcp_streams[sid]

  def give_up_gaps(self, pcaptime):
    for sid in self.tcp_streams:
      if len(self.tcp_streams[sid][1]) and pcaptime - min(self.tcp_streams[sid][1][x][2] for x in self.tcp_streams[sid][1]) >= 60:
        # Could not close gap to out-of-order data within a minute, probably missed something!
        newnext = min(self.tcp_streams[sid][1])
        eprint("%08x  DATA LOSS %i bytes!" % (sid, newnext-self.tcp_streams[sid][0]))
        self.tcp_streams[sid][0] = newnext

  def get_out_of_order_bytes(self, pcaptime):
    for sid in self.tcp_streams:
      while any(x <= self.tcp_streams[sid][0] for x in self.tcp_streams[sid][1]):
        eprint("%08x  Gap closed after %f seconds" % (sid, pcaptime - min(self.tcp_streams[sid][1][x][2] for x in self.tcp_streams[sid][1])))
        for y in (x for x in self.tcp_streams[sid][1].keys() if x <= self.tcp_streams[sid][0]):
          for byte in self.tcp_streams[sid][1][y][0][self.tcp_streams[sid][0]-y:]:
            yield byte
          self.tcp_streams[sid][0] = max(self.tcp_streams[sid][0], y + (1 if (self.tcp_streams[sid][1][y][1]&3) else len(self.tcp_streams[sid][1][y][0])))
          self.tcp_streams[sid][2] = self.tcp_streams[sid][1][y][2]
          del self.tcp_streams[sid][1][y]
          if not len(self.tcp_streams[sid][1]):
            eprint("%08x  Stream is contiguous again" % sid)

  def get_data_from_pcap(self, f):
    pcaphdrlen = 24
    pcaprechdrlen = 16
    etherhdrlen = 14  # May contain 4 additional bytes if it is a VLAN tagged frame.
    iphdrlen = 20     # Has a 'header length' value that may indicate additional optional values.
    tcphdrlen = 20    # Has a 'header length' value that may indicate additional optional values.

    # Check PCAP file header.
    if f.read(pcaphdrlen)[:4] != "\xD4\xC3\xB2\xA1":
      eprint("ERROR! PCAP format not supported! Can only read little-endian PCAP files with microsecond precision!")
      return

    while True:
      try:

        # Read PCAP record header.
        pcaprechdr = f.read(pcaprechdrlen)
        if not pcaprechdr:
          break
        pcaprechdr = struct.unpack("<LLLL", pcaprechdr)
        pcaptime = pcaprechdr[0] + pcaprechdr[1]/1000000.

        # Skip over Ethernet header. It may have 4 additional bytes if it is a VLAN tagged frame.
        etherhdr = f.read(etherhdrlen)
        if etherhdr[12:14] == "\x18\x00":
          f.read(4)

        # Skip over the IP header.
        # TODO: IPv6 support? This will fail badly on any IPv6 traffic.
        ipheader = struct.unpack(">BBHLLLL", f.read(iphdrlen))
        ipheaderlen = (ipheader[0] & 0x0F) << 2
        f.read(ipheaderlen-iphdrlen)  # Skip optional IP header bytes
        ipdatalen = ipheader[2]

        # Parse the TCP header.
        tcpheader = struct.unpack(">HHLLHHHH", f.read(tcphdrlen))
        sid = tcpheader[0] | (tcpheader[1] << 16)
        tcpheaderlen = (tcpheader[4] & 0x0F000) >> 10
        f.read(tcpheaderlen-tcphdrlen)  # Skip optional TCP header bytes
        data = f.read(ipdatalen-ipheaderlen-tcpheaderlen)  # This is the actual data.
        if etherhdr[6:9] == "\x00\x27\x02":  # Inverter speaking.

          # Treat data gaps as loss if not filled within 60 seconds.
          self.give_up_gaps(pcaptime)

          # Write out out-of-order data when the gap is closed.
          for byte in self.get_out_of_order_bytes(pcaptime):
            yield byte

          # Discard streams that have been silent for one hour.
          self.prune_silent_streams(pcaptime)

          # Identify new streams.
          if sid not in self.tcp_streams or tcpheader[4] & 2:
            self.tcp_streams[sid] = [tcpheader[2], {}, pcaptime]

          # Immediately write bytes if they are received in order.
          if self.tcp_streams[sid][0] >= tcpheader[2]:
            for byte in data[self.tcp_streams[sid][0]-tcpheader[2]:]:
              yield byte
            self.tcp_streams[sid][0] = tcpheader[2] + (1 if (tcpheader[4]&3) else len(data))
            self.tcp_streams[sid][2] = pcaptime

          # Store out-of-order segments; we'll write them when the gap is closed.
          else:
            eprint("%08x  Out of order packet! SEQ=%08x expect=%08x (Gap size %i)" % (sid, tcpheader[2], self.tcp_streams[sid][0], tcpheader[2]-self.tcp_streams[sid][0]))
            self.tcp_streams[sid][1][tcpheader[2]] = [data, tcpheader[4], pcaptime]

        # There may be some remaining padding bytes after the data; skip that.
        f.read(pcaprechdr[2]-ipdatalen-etherhdrlen)

      except struct.error:
        eprint("Warning: file read error!")
        break

#############################################################################################

def parse0500(data):
  pos = 0
  while pos < len(data):
    type, id, length, timestamp = struct.unpack("<HLHL", data[pos:pos+12])
    if type == 0x0080 and length == 13:  # Optimizer data (packed)
      bytes = map(ord, data[pos+12:pos+8+length])
      yield {
        'op_id': id,
        'timestamp': timestamp,
        'uptime': bytes[0] | (bytes[1] << 8),
        'v_in': bytes[2] | ((bytes[3] & 0x03) << 8),
        'v_out': (bytes[3] >> 2) | ((bytes[4] & 0x0F) << 6),
        'i_in': (bytes[4] >> 4) | (bytes[5] << 4),
        'e_day': bytes[6] | (bytes[7] << 8),
        'temperature': (bytes[8] | ~0xFF) if bytes[8] & 0x80 else bytes[8]
      }
    elif type == 0x0010 and length == 124:  # Inverter data
      inv = SEDataInverter.parse(data, pos + 12)
      yield {
        'inv_id':       id & ~0x00800000,
        'timestamp':    timestamp,
        'temperature':  inv.Temp,
        'e_day':        inv.EdayAC,
        'de_day':       inv.DeltaEdayAC,
        'v_ac':         inv.Vac,
        'i_ac':         inv.Iac,
        'frequency':    inv.Freq,
        'v_dc':         inv.Vdc,
        'e_total':      inv.Etotal_i,
        'i_rcd':        inv.Ircd,
        'mode':         inv.Mode,
        'p_active':     inv.Pactive,
        'p_apparent':   inv.Papparent,
        'p_reactive':   inv.Preactive
      }
    pos += length + 8


def eprint(message):
  sys.stderr.write(message)
  sys.stderr.write("\n")

#############################################################################################


# Connect to database and get last 0503 message.
conn = MySQLdb.connect(user=db_user, passwd=db_pass, db=db_name)
db = conn.cursor()
db.execute("SELECT last_0503 FROM live_update")
last_0503 = db.fetchone()[0]

parser = SEParser(inverter_private_key, decryptor=SEDecrypt(inverter_private_key, last_0503), msg_filt=set((0x0500, 0x0503)))
reader = PCAPParser()
for filename in sys.argv[1:]:
  eprint("Reading from %s" % filename)
  if filename == "-":
    f = sys.stdin
  else:
    f = open(filename, 'rb')
  byteiterator = reader.get_data_from_pcap(f)
  for hdr, msg in parser.get_messages(byteiterator):
    if hdr[6] == 0x0503:
      eprint("Setting new 0503 key")
      db.execute("UPDATE live_update SET last_0503 = %s", (msg,))
      conn.commit()
    if hdr[6] != 0x0500:
      continue
    for telem in parse0500(msg):
      updated = False
      if "op_id" in telem:
        db.execute(
          "INSERT IGNORE INTO telemetry_optimizers "
          "(op_id, timestamp, uptime, v_in, v_out, i_in, e_day, temperature) VALUES "
          "(%(op_id)s, %(timestamp)s, %(uptime)s, %(v_in)s, %(v_out)s, %(i_in)s, %(e_day)s, %(temperature)s)",
          telem)
        updated = True
      elif "inv_id" in telem:
        db.execute(
          "INSERT IGNORE INTO telemetry_inverter "
          "(inv_id, timestamp, temperature, e_day, de_day, v_ac, i_ac, frequency, v_dc, e_total, i_rcd, mode, p_active, p_apparent, p_reactive) VALUES "
          "(%(inv_id)s, %(timestamp)s, %(temperature)s, %(e_day)s, %(de_day)s, %(v_ac)s, %(i_ac)s, %(frequency)s, %(v_dc)s, %(e_total)s, %(i_rcd)s, %(mode)s, %(p_active)s, %(p_apparent)s, %(p_reactive)s)",
          telem)
        updated = True
      if updated:
        db.execute("UPDATE live_update SET last_telemetry = %s", (int(time.time()),))
        conn.commit()
  f.close()

eprint("End of file. Shutting down.")
conn.close()

