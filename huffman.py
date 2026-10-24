import heapq, struct
from collections import Counter

def build_codes(freq):
    heap = [(w, i, s) for i, (s, w) in enumerate(freq.items())]
    heapq.heapify(heap)
    if len(heap) == 1:
        return {heap[0][2]: "0"}
    n = len(heap)
    while len(heap) > 1:
        w1, _, a = heapq.heappop(heap)
        w2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (w1 + w2, n, (a, b)))
        n += 1
    codes = {}
    def walk(node, prefix):
        if isinstance(node, tuple):
            walk(node[0], prefix + "0")
            walk(node[1], prefix + "1")
        else:
            codes[node] = prefix
    walk(heap[0][2], "")
    return codes

def huffman_encode(symbols):
    if not symbols:
        return struct.pack(">IH", 0, 0)
    freq = Counter(symbols)
    codes = build_codes(freq)
    header = struct.pack(">IH", len(symbols), len(freq))
    for s, w in freq.items():
        header += struct.pack(">HI", s, w)
    bits = "".join(codes[s] for s in symbols)
    bits += "0" * ((-len(bits)) % 8)
    payload = int(bits, 2).to_bytes(len(bits) // 8, "big")
    return header + payload

def huffman_decode(data):
    total, k = struct.unpack(">IH", data[:6])
    if total == 0:
        return []
    pos = 6
    freq = {}
    for _ in range(k):
        s, w = struct.unpack(">HI", data[pos:pos + 6])
        freq[s] = w
        pos += 6
    codes = build_codes(freq)
    rev = {c: s for s, c in codes.items()}
    payload = data[pos:]
    bits = bin(int.from_bytes(payload, "big"))[2:].zfill(len(payload) * 8)
    out, cur = [], ""
    for b in bits:
        cur += b
        if cur in rev:
            out.append(rev[cur])
            cur = ""
            if len(out) == total:
                break
    return out