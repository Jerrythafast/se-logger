#!/usr/bin/env python
import struct, sys, MySQLdb
from collections import namedtuple

# SETTINGS
inverter_private_key = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
db_user = "dbuser"
db_pass = "dbpassword"
db_name = "solaredge"



#############################################################################################

SEDataInverter = namedtuple("SEDataInverter",
    "uptime interval Temp EdayAC DeltaEdayAC Vac Iac Freq EdayDC DeltaEdayDC Vdc Idc Etotal_f Ircd "
    "L1 CosPhi Mode GndFltR f1 IoutDC L2 L3 Pactive Papparent Preactive f2 f3 L4 Etotal_i L5")
SEDataInverter.size = 120
SEDataInverter.parse = classmethod(
    lambda cls, data, offset=0:
        cls._make(struct.unpack("<LLffffffLLfLffLfLfffLLfffffLLL", data[offset:offset+cls.size])))

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
    for byte in byteiterator:
      if state == 0:
        # Skipping to next barker.
        data.append(byte)
        if len(data) >= 4 and "".join(data[-4:]) == "\x12\x34\x56\x79":
          state = 1
          if len(data) > 4:
            eprint("Warning! Skipping %i mysterious bytes!" % (len(data)-4))
            eprint(" ".join("%02x" % ord(x) for x in data[:4]))
            data = data[-4:]
      elif state == 1:
        # Reading length.
        data.append(byte)
        if len(data) == 6:
          state = 2
          length = struct.unpack("<H", "".join(data[-2:]))[0]
      elif state == 2:
        # Reading length inverted.
        data.append(byte)
        if len(data) == 8:
          state = 3
          if ((~struct.unpack("<H", "".join(data[-2:]))[0]) & 0xFFFF) != length:
            eprint("Warning! Length value mismatch! Discarding...")
            state = 0
            data = []
      elif state == 3:
        # Reading sequence number.
        data.append(byte)
        if len(data) == 10:
          state = 4
      elif state == 4:
        # Reading sender ID.
        data.append(byte)
        if len(data) == 14:
          state = 5
      elif state == 5:
        # Reading receiver ID.
        data.append(byte)
        if len(data) == 18:
          state = 6
      elif state == 6:
        # Reading message type.
        data.append(byte)
        if len(data) == 20:
          state = 7 if length else 8
      elif state == 7:
        # Reading message content.
        data.append(byte)
        if len(data) == 20 + length:
          state = 8
      elif state == 8:
        # Reading message checksum.
        data.append(byte)
        if len(data) == 20 + length + 2:
          # TODO: Check the checksum.
          data = "".join(data)
          hdr = struct.unpack("<LHHHLLH", data[:20])
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
          state = 0
          data = []
    if len(data):
      eprint("Warning! Got %i mysterious bytes left! (state=%i)" % (len(data), state))
      eprint(" ".join("%02x" % ord(x) for x in data))


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


def get_data_from_pcap(f):
  pcaphdrlen = 24
  pcaprechdrlen = 16
  etherhdrlen = 14  # May contain 4 additional bytes if it is a VLAN tagged frame.
  iphdrlen = 20     # Has a 'header length' value that may indicate additional optional values.
  tcphdrlen = 20    # Has a 'header length' value that may indicate additional optional values.
  data = []
  f.read(pcaphdrlen)  # Skip PCAP file header.
  while True:

    # Read PCAP record header.
    pcaprechdr = f.read(pcaprechdrlen)
    if not pcaprechdr:
      break

    # Number of bytes in pcap record is including Eth/IP/TCP headers and padding.
    pcapdatalen = struct.unpack("<LLLL", pcaprechdr)[2]

    # Skip over Ethernet header. It may have 4 additional bytes if it is a VLAN tagged frame.
    if f.read(etherhdrlen)[12:14] == "\x18\x00":
      f.read(4)

    # Skip over the IP header.
    ipheader = struct.unpack(">BBHLLLL", f.read(iphdrlen))
    ipheaderlen = (ipheader[0] & 0x0F) << 2
    f.read(ipheaderlen-iphdrlen)  # Skip optional IP header bytes
    ipdatalen = ipheader[2]

    # Skip over the TCP header. TODO: Identify retransmits and keep-alives for cleaner output.
    tcpheader = struct.unpack("<HHLLHHHH", f.read(tcphdrlen))
    tcpheaderlen = (tcpheader[4] & 0x0F0) >> 2
    f.read(tcpheaderlen-tcphdrlen)  # Skip optional TCP header bytes
    for byte in f.read(ipdatalen-ipheaderlen-tcpheaderlen):  # This is the actual data.
      yield byte

    # There may be some remaining padding bytes after the data; skip that.
    f.read(pcapdatalen-ipdatalen-etherhdrlen)

#############################################################################################


# Connect to database and get last 0503 message.
conn = MySQLdb.connect(user=db_user, passwd=db_pass, db=db_name)
db = conn.cursor()
db.execute("SELECT last_0503 FROM live_update")
last_0503 = db.fetchone()[0]

parser = SEParser(inverter_private_key, decryptor=SEDecrypt(inverter_private_key, last_0503), msg_filt=set((0x0500, 0x0503)))
for filename in sys.argv[1:]:
  eprint("Reading from %s" % filename)
  if filename == "-":
    f = sys.stdin
  else:
    f = open(filename, 'r')
  byteiterator = get_data_from_pcap(f)
  for hdr, msg in parser.get_messages(byteiterator):
    if hdr[6] == 0x0503:
      eprint("Setting new 0503 key")
      db.execute("UPDATE live_update SET last_0503 = %s", (msg,))
      conn.commit()
    if hdr[6] != 0x0500:
      continue
    for telem in parse0500(msg):
      if "op_id" in telem:
        db.execute(
          "INSERT IGNORE INTO telemetry_optimizers "
          "(op_id, timestamp, v_in, v_out, i_in, e_day, temperature) VALUES "
          "(%(op_id)s, %(timestamp)s, %(v_in)s, %(v_out)s, %(i_in)s, %(e_day)s, %(temperature)s)",
          telem)
      elif "inv_id" in telem:
        db.execute(
          "INSERT IGNORE INTO telemetry_inverter "
          "(inv_id, timestamp, temperature, e_day, de_day, v_ac, i_ac, frequency, v_dc, e_total, i_rcd, mode, p_active, p_apparent, p_reactive) VALUES "
          "(%(inv_id)s, %(timestamp)s, %(temperature)s, %(e_day)s, %(de_day)s, %(v_ac)s, %(i_ac)s, %(frequency)s, %(v_dc)s, %(e_total)s, %(i_rcd)s, %(mode)s, %(p_active)s, %(p_apparent)s, %(p_reactive)s)",
          telem)
    conn.commit()
  f.close()

eprint("End of file. Shutting down.")
conn.close()

