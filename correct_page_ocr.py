from pathlib import Path

source_dir = Path('page-ocr')

files = list(source_dir.glob('**/*.txt'))

for file in files:
    temp_file = file.parent / (file.stem +'_temp.txt')
    with open(file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    with open(temp_file, 'w') as f_write:
        if "(บช)" in file.stem:
            o = 3
        else:
            o = 1
        first_page = -1
        c = 0
        for i, line in enumerate(lines):
            page = int(line.strip())
            if c == 0:
                first_page = page
                f_write.write(f"{page}\n")
                c+=1
            else:
                exp_page = first_page + c
                while exp_page < page and c < o:
                    f_write.write(f"{exp_page}\n")
                    c+=1
                    exp_page = first_page + c
                if c < o:
                    f_write.write(f"{page}\n")
                    c+=1
                else:
                    c = 1
                    f_write.write(f"{page}\n")
                    first_page = page

        while c < o:
            f_write.write(f"{first_page + c}")
            c+=1
print("success correct page")