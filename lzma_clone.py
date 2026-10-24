import sys, struct

MAGIC = b"LZC1"
WINDOW = 65535
MIN_MATCH, MAX_MATCH = 3, 258
TOP = 1 << 24

class RangeEncoder:
    def __init__(self):
        self.low, self.range = 0, 0xFFFFFFFF
        self.cache, self.cache_size = 0, 1
        self.out = bytearray()

    def shift_low(self):
        if self.low < 0xFF000000 or self.low >= 0x100000000:
            carry = self.low >> 32
            temp = self.cache
            while True:
                self.out.append((temp + carry) & 0xFF)
                temp = 0xFF
                self.cache_size -= 1
                if self.cache_size == 0:
                    break
            self.cache = (self.low >> 24) & 0xFF
        self.cache_size += 1
        self.low = (self.low & 0x00FFFFFF) << 8

    def encode_bit(self, probs, i, bit):
        p = probs[i]
        bound = (self.range >> 11) * p
        if bit == 0:
            self.range = bound
            probs[i] = p + ((2048 - p) >> 5)
        else:
            self.low += bound
            self.range -= bound
            probs[i] = p - (p >> 5)
        while self.range < TOP:
            self.range = (self.range << 8) & 0xFFFFFFFF
            self.shift_low()

    def encode_direct(self, value, nbits):
        for i in range(nbits - 1, -1, -1):
            self.range >>= 1
            if (value >> i) & 1:
                self.low += self.range
            while self.range < TOP:
                self.range = (self.range << 8) & 0xFFFFFFFF
                self.shift_low()

    def finish(self):
        for _ in range(5):
            self.shift_low()
        return bytes(self.out)

class RangeDecoder:
    def __init__(self, data, pos):
        self.data = data
        self.range = 0xFFFFFFFF
        self.code = int.from_bytes(data[pos + 1:pos + 5], "big")
        self.pos = pos + 5

    def next_byte(self):
        b = self.data[self.pos] if self.pos < len(self.data) else 0
        self.pos += 1
        return b

    def normalize(self):
        while self.range < TOP:
            self.range = (self.range << 8) & 0xFFFFFFFF
            self.code = ((self.code << 8) | self.next_byte()) & 0xFFFFFFFF

    def decode_bit(self, probs, i):
        p = probs[i]
        bound = (self.range >> 11) * p
        if self.code < bound:
            self.range = bound
            probs[i] = p + ((2048 - p) >> 5)
            bit = 0
        else:
            self.code -= bound
            self.range -= bound
            probs[i] = p - (p >> 5)
            bit = 1
        self.normalize()
        return bit

    def decode_direct(self, nbits):
        res = 0
        for _ in range(nbits):
            self.range >>= 1
            if self.code >= self.range:
                self.code -= self.range
                bit = 1
            else:
                bit = 0
            res = (res << 1) | bit
            self.normalize()
        return res

def enc_tree(rc, probs, base, nbits, value):
    m = 1
    for i in range(nbits - 1, -1, -1):
        b = (value >> i) & 1
        rc.encode_bit(probs, base + m, b)
        m = (m << 1) | b

def dec_tree(rc, probs, base, nbits):
    m = 1
    for _ in range(nbits):
        m = (m << 1) | rc.decode_bit(probs, base + m)
    return m - (1 << nbits)

def new_models():
    return {
        "is_match": [1024] * 2,
        "literal": [1024] * (8 * 256),
        "length": [1024] * 256,
        "dist_slot": [1024] * 32,
    }

def compress(src, dst):
    data = open(src, "rb").read()
    n = len(data)
    rc, M = RangeEncoder(), new_models()
    table = {}

    def insert(pos):
        if pos + 3 <= n:
            table.setdefault(data[pos:pos + 3], []).append(pos)

    i, state = 0, 0
    while i < n:
        best_len, best_dist = 0, 0
        if i + 3 <= n:
            cands = table.get(data[i:i + 3])
            if cands:
                maxl = min(MAX_MATCH, n - i)
                for j in reversed(cands[-16:]):
                    d = i - j
                    if d > WINDOW:
                        break
                    l = 3
                    while l < maxl and data[j + l] == data[i + l]:
                        l += 1
                    if l > best_len:
                        best_len, best_dist = l, d
                    if l == maxl:
                        break
        if best_len >= MIN_MATCH:
            rc.encode_bit(M["is_match"], state, 1)
            enc_tree(rc, M["length"], 0, 8, best_len - MIN_MATCH)
            nb = best_dist.bit_length()
            enc_tree(rc, M["dist_slot"], 0, 5, nb)
            rc.encode_direct(best_dist - (1 << (nb - 1)), nb - 1)
            for k in range(i, i + best_len):
                insert(k)
            i += best_len
            state = 1
        else:
            rc.encode_bit(M["is_match"], state, 0)
            prev = data[i - 1] if i > 0 else 0
            enc_tree(rc, M["literal"], (prev >> 5) * 256, 8, data[i])
            insert(i)
            i += 1
            state = 0
    with open(dst, "wb") as f:
        f.write(MAGIC + struct.pack(">I", n) + rc.finish())

def decompress(src, dst):
    data = open(src, "rb").read()
    assert data[:4] == MAGIC, "Fichier invalide"
    (total,) = struct.unpack(">I", data[4:8])
    rc, M = RangeDecoder(data, 8), new_models()
    out, state = bytearray(), 0
    while len(out) < total:
        if rc.decode_bit(M["is_match"], state) == 1:
            length = dec_tree(rc, M["length"], 0, 8) + MIN_MATCH
            nb = dec_tree(rc, M["dist_slot"], 0, 5)
            dist = (1 << (nb - 1)) + rc.decode_direct(nb - 1)
            for _ in range(length):
                out.append(out[-dist])
            state = 1
        else:
            prev = out[-1] if out else 0
            out.append(dec_tree(rc, M["literal"], (prev >> 5) * 256, 8))
            state = 0
    open(dst, "wb").write(out)

if __name__ == "__main__":
    mode, src, dst = sys.argv[1:4]
    (compress if mode == "c" else decompress)(src, dst)