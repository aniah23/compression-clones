import sys, struct
from huffman import huffman_encode, huffman_decode

BLOCK = 100_000
MAGIC = b"BZC1"

def bwt(data):
    n = len(data)
    rank = list(data)
    sa = list(range(n))
    k = 1
    while True:
        key = lambda i: (rank[i], rank[(i + k) % n])
        sa.sort(key=key)
        new = [0] * n
        for j in range(1, n):
            new[sa[j]] = new[sa[j - 1]] + (key(sa[j]) != key(sa[j - 1]))
        rank = new
        if rank[sa[-1]] == n - 1 or k >= n:
            break
        k *= 2
    last = bytes(data[(i - 1) % n] for i in sa)
    return last, sa.index(0)

def ibwt(last, idx):
    n = len(last)
    counts = [0] * 256
    for b in last:
        counts[b] += 1
    starts, s = [0] * 256, 0
    for c in range(256):
        starts[c] = s
        s += counts[c]
    T, seen = [0] * n, [0] * 256
    for i, b in enumerate(last):
        T[starts[b] + seen[b]] = i
        seen[b] += 1
    out, p = bytearray(), idx
    for _ in range(n):
        p = T[p]
        out.append(last[p])
    return bytes(out)

def mtf_encode(data):
    table, out = list(range(256)), []
    for b in data:
        i = table.index(b)
        out.append(i)
        table.pop(i)
        table.insert(0, b)
    return out

def mtf_decode(idxs):
    table, out = list(range(256)), bytearray()
    for i in idxs:
        b = table.pop(i)
        out.append(b)
        table.insert(0, b)
    return bytes(out)

def compress(src, dst):
    data = open(src, "rb").read()
    blocks = [data[i:i + BLOCK] for i in range(0, len(data), BLOCK)]
    with open(dst, "wb") as f:
        f.write(MAGIC + struct.pack(">I", len(blocks)))
        for blk in blocks:
            last, idx = bwt(blk)
            enc = huffman_encode(mtf_encode(last))
            f.write(struct.pack(">II", idx, len(enc)) + enc)

def decompress(src, dst):
    data = open(src, "rb").read()
    assert data[:4] == MAGIC, "Fichier invalide"
    (nb,) = struct.unpack(">I", data[4:8])
    pos, out = 8, bytearray()
    for _ in range(nb):
        idx, ln = struct.unpack(">II", data[pos:pos + 8])
        pos += 8
        syms = huffman_decode(data[pos:pos + ln])
        pos += ln
        out += ibwt(mtf_decode(syms), idx)
    open(dst, "wb").write(out)

if __name__ == "__main__":
    mode, src, dst = sys.argv[1:4]
    (compress if mode == "c" else decompress)(src, dst)