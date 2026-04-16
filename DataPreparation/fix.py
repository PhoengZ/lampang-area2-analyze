from pathlib import Path

source_dir = Path('page-ocr')

# ค้นหาไฟล์ทั้งหมดที่ลงท้ายด้วย _temp.txt ในโฟลเดอร์และโฟลเดอร์ย่อย
temp_files = list(source_dir.glob('**/*_temp.txt'))

deleted_count = 0

for file in temp_files:
    try:
        file.unlink() # คำสั่งสำหรับลบไฟล์
        print(f"Deleted: {file.name}")
        deleted_count += 1
    except Exception as e:
        print(f"Error deleting {file.name}: {e}")

print(f"\nลบไฟล์เสร็จสิ้น ลบไปทั้งหมด: {deleted_count} ไฟล์")