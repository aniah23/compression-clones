import sys, os, struct
import lzma_clone

MAGIC = b"SZC1"

def create(archive, files):
    buf = bytearray(MAGIC + struct.pack(">I", len(files)))
    contents = []
    for path in files:
        data = open(path, "rb").read()
        name = os.path.basename(path).encode("utf-8")
        buf += struct.pack(">H", len(name)) + name + struct.pack(">Q", len(data))
        contents.append(data)
    for d in contents:
        buf += d
    tmp = archive + ".tmp"
    open(tmp, "wb").write(buf)
    lzma_clone.compress(tmp, archive)
    os.remove(tmp)
    print(f"Archive créée : {len(buf)} -> {os.path.getsize(archive)} octets")

def read_archive(archive):
    tmp = archive + ".tmp"
    lzma_clone.decompress(archive, tmp)
    data = open(tmp, "rb").read()
    os.remove(tmp)
    assert data[:4] == MAGIC, "Archive invalide"
    (n,) = struct.unpack(">I", data[4:8])
    pos, entries = 8, []
    for _ in range(n):
        (ln,) = struct.unpack(">H", data[pos:pos + 2]); pos += 2
        name = data[pos:pos + ln].decode("utf-8"); pos += ln
        (size,) = struct.unpack(">Q", data[pos:pos + 8]); pos += 8
        entries.append((name, size))
    return data, pos, entries

def list_files(archive):
    _, _, entries = read_archive(archive)
    for name, size in entries:
        print(f"{size:>12}  {name}")

def extract(archive, outdir):
    data, pos, entries = read_archive(archive)
    os.makedirs(outdir, exist_ok=True)
    for name, size in entries:
        path = os.path.join(outdir, os.path.basename(name))
        open(path, "wb").write(data[pos:pos + size])
        pos += size
        print("Extrait :", path)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "a":
        create(sys.argv[2], sys.argv[3:])
    elif cmd == "l":
        list_files(sys.argv[2])
    elif cmd == "x":
        extract(sys.argv[2], sys.argv[3])