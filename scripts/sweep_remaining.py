import os
remaining = []
for root, dirs, files in os.walk("G:/"):
    low = root.lower().replace("\\", "/")
    if "$recycle.bin" in low or "/system volume information" in low:
        dirs[:] = []
        continue
    if low.startswith("g:/quake_legacy/demos"):
        continue
    for f in files:
        if f.lower().endswith(".dm_73"):
            remaining.append(os.path.join(root, f))
print("Remaining .dm_73 outside canonical:", len(remaining))
for r in remaining[:30]:
    print(" ", r)
