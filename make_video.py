import struct

W, H, FPS, N = 128, 96, 6, 12

def chunk(tag, data):
    pad = b"\0" if len(data) % 2 else b""
    return tag + struct.pack("<I", len(data)) + data + pad

def lst(kind, data):
    return b"LIST" + struct.pack("<I", len(data) + 4) + kind + data

frame_size = W * H * 3
avih = struct.pack("<14I", 1000000 // FPS, frame_size * FPS, 0, 0x10, N, 0, 1, frame_size, W, H, 0, 0, 0, 0)
strh = struct.pack("<4s4sIHH8Ihhhh", b"vids", b"DIB ", 0, 0, 0, 0, 1, FPS, 0, N, frame_size, 0, 0, 0, 0, W, H)
strf = struct.pack("<IiiHHIIiiII", 40, W, H, 1, 24, 0, frame_size, 0, 0, 0, 0)

frames = []
for f in range(N):
    rows = []
    for y in range(H - 1, -1, -1):
        row = bytearray()
        for x in range(W):
            if f * 8 <= x < f * 8 + 24 and 30 <= y < 60:
                row += bytes((0, 200, 255))
            else:
                row += bytes((60 + y, 40, 90 + x // 2))
        rows.append(bytes(row))
    frames.append(b"".join(rows))

movi_chunks, idx, offset = [], b"", 4
for fr in frames:
    movi_chunks.append(chunk(b"00db", fr))
    idx += struct.pack("<4sIII", b"00db", 0x10, offset, len(fr))
    offset += 8 + len(fr)

hdrl = lst(b"hdrl", chunk(b"avih", avih) + lst(b"strl", chunk(b"strh", strh) + chunk(b"strf", strf)))
movi = lst(b"movi", b"".join(movi_chunks))
idx1 = chunk(b"idx1", idx)
body = b"AVI " + hdrl + movi + idx1
open("video.avi", "wb").write(b"RIFF" + struct.pack("<I", len(body)) + body)
print("video.avi créé")