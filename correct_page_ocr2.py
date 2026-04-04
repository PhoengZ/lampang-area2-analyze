from pathlib import Path

source_dir = Path('page-ocr')
files = list(source_dir.glob('**/*.txt'))

for file in files:
    is_bch = "บช" in file.stem

    with open(file, 'r') as f:
        numbers = [int(line.strip()) for line in f if line.strip().isdigit()]

    if len(numbers) < 2:
        continue

    expected = []

    if is_bch:
        #  pattern: +1, +1, +2 -> 0 1 2 0 1 2
        pattern = [1, 1, 2]
        idx = 0

        current = numbers[0]
        max_num = numbers[-1]

        while current <= max_num:
            expected.append(current)
            current += pattern[idx % 3]
            idx += 1

    else:
        step = numbers[1] - numbers[0]

        current = numbers[0]
        max_num = numbers[-1]

        while current <= max_num:
            expected.append(current)
            current += step

    # เช็คว่ามี missing ไหม
    if numbers == expected:
        continue

    # สร้างไฟล์ใหม่ถ้าเลขขาด
    temp_file = file.parent / f"{file.stem}_temp.txt"

    with open(temp_file, 'w') as f:
        for num in expected:
            f.write(f"{num}\n")

    print(f"Fixed: {file.name} -> {temp_file.name}")