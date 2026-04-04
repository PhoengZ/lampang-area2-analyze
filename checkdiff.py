from collections import defaultdict
import re
file_path = "except_extract_copy.txt"

# โครงสร้าง: {ตำบล: {"normal": x, "bch": y}}
data = defaultdict(lambda: {"normal": 0, "bch": 0})

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        # check ว่าเป็น บช ไหม
        is_bch = ("บช" in line) or ("สส.5-18บช" in line) or ("(บช)" in line) or ("(บช.)" in line)

        prefix = line.split("_หน่วยที่_")[0]

        match = re.search(r"(ตำบล|ต\.)\s*\S+", prefix)
        if match:
            tambon = match.group().strip()
            tambon = tambon.replace("ต.", "ตำบล")
        else:
            continue

        if is_bch:
            data[tambon]["bch"] += 1
        else:
            data[tambon]["normal"] += 1

# แสดงผล
for tambon, counts in data.items():
    normal = counts["normal"]
    bch = counts["bch"]
    diff = abs(normal - bch)
    if diff == 0 : continue

    print(f"{tambon}")
    print(f"  5-18: {normal}")
    print(f"  5-18 บช: {bch}")
    print(f"  ต่างกัน: {diff}")
    print("-" * 30)