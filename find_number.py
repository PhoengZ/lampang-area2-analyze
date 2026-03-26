import json

# อ่านไฟล์
with open('election-stations-2569.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# หาหน่วยเลือกตั้งของจังหวัด
rayong = next((p for p in data['provinces'] if p['name'] == 'ระยอง'), None)
# print(f"ระยอง {rayong['total_stations']} หน่วยเลือกตั้ง")

# หาหน่วยเลือกตั้งจากรหัส
def find_total_station(area,province):
    for p in data['provinces']:
        if p['name'] == province:
            for a in p['areas']:
                if a['area'] == area:
                    return a['total_stations']
    return None

print(find_total_station(2, 'ลำปาง'))