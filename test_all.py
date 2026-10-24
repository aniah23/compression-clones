import os, sys, time, filecmp
import bzip2_clone, lzma_clone, sevenzip_clone

def run(files):
    print(f"{'Fichier':<14}{'Algo':<7}{'Original':>10}{'Compressé':>11}{'Taux':>8}{'Temps':>8}  Vérif")
    for f in files:
        orig = os.path.getsize(f)
        for name, mod, ext in (("bzip2", bzip2_clone, ".bzc"), ("lzma", lzma_clone, ".lzc")):
            c, d = f + ext, f + ext + ".out"
            t = time.time()
            mod.compress(f, c)
            dt = time.time() - t
            mod.decompress(c, d)
            ok = filecmp.cmp(f, d, shallow=False)
            size = os.path.getsize(c)
            print(f"{f:<14}{name:<7}{orig:>10}{size:>11}{orig/size:>7.2f}x{dt:>7.1f}s  {'OK' if ok else 'ERREUR'}", flush=True)
            os.remove(d)
    print()
    sevenzip_clone.create("archive.szc", files)

if __name__ == "__main__":
    run(sys.argv[1:])