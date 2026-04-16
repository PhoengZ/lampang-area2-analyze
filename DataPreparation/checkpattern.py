from pathlib import Path

source_dir = Path('page-ocr')
files = list(source_dir.glob('**/*.txt'))

for file in files:
    is_bch = "บช" in file.stem

    # อ่านตัวเลข
    with open(file, 'r') as f:
        numbers = [int(line.strip()) for line in f if line.strip().isdigit()]

    if len(numbers) < 2:
        continue

    expected = []

    if is_bch:
        # pattern: +1, +1, +2
        pattern = [1, 1, 2]
        idx = 0

        current = numbers[0]
        max_num = numbers[-1]

        while current <= max_num:
            expected.append(current)
            current += pattern[idx % 3]
            idx += 1

    else:
        # step ปกติ
        step = numbers[1] - numbers[0]

        current = numbers[0]
        max_num = numbers[-1]

        while current <= max_num:
            expected.append(current)
            current += step

    # แปลงเป็น set เพื่อหา diff
    set_numbers = set(numbers)
    set_expected = set(expected)

    missing = sorted(set_expected - set_numbers)   # เลขที่ควรมีแต่ไม่มี
    extra = sorted(set_numbers - set_expected)     # เลขที่เกินมา

    # ถ้าไม่มีปัญหา ข้าม
    if not missing and not extra:
        continue

    print(f"\n📄 File: {file.name}")
    print(f"Original count: {len(numbers)}")
    print(f"Expected count: {len(expected)}")

    if missing:
        print(f"Missing pages: {missing}")

    if extra:
        print(f"Extra pages: {extra}")