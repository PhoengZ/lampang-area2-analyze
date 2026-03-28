from pathlib import Path

def cleanup_and_rename():
    source_dir = Path('page-ocr')
    
    if not source_dir.exists():
        print(f"ไม่พบโฟลเดอร์: {source_dir}")
        return

    # ค้นหาไฟล์ทั้งหมดที่ลงท้ายด้วย _temp.txt
    temp_files = list(source_dir.glob('**/*_temp.txt'))
    
    if not temp_files:
        print("ไม่พบไฟล์ _temp.txt สำหรับการจัดการ")
        return

    print(f"กำลังจัดการไฟล์จำนวน: {len(temp_files)} ชุด")
    print("-" * 30)

    for temp_file in temp_files:
        try:
            # 1. ระบุชื่อไฟล์ต้นฉบับ (ตัดคำว่า _temp ออก)
            original_file = temp_file.parent / (temp_file.name.replace('_temp.txt', '.txt'))
            
            # 2. ถ้ามีไฟล์ต้นฉบับอยู่ ให้ลบทิ้งก่อน
            if original_file.exists():
                original_file.unlink()
            
            temp_file.rename(original_file)
            
            print(f"✅ Success: {original_file.name}")
            
        except Exception as e:
            print(f"❌ Error: ไม่สามารถจัดการไฟล์ {temp_file.name} ได้เนื่องจาก {e}")

    print("-" * 30)
    print("Cleanup & Rename complete!")

if __name__ == "__main__":
    cleanup_and_rename()