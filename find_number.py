import json

# อ่านไฟล์
with open('election-stations-2569.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# หาหน่วยเลือกตั้งของจังหวัด
rayong = next((p for p in data['provinces'] if p['name'] == 'ระยอง'), None)
# print(f"ระยอง {rayong['total_stations']} หน่วยเลือกตั้ง")
d = dict()
# หาหน่วยเลือกตั้งจากรหัส
def find_total_station(area,province):
    for p in data['provinces']:
        if p['name'] == province:
            for a in p['areas']:
                if a['area'] == area:
                    for unit in a['stations']:
                        if unit['district'] not in d:
                            d[unit['district']] = dict()
                        if unit['subdistrict'] not in  d[unit['district']]:
                            d[unit['district']][unit['subdistrict']] = 1
                        else:
                            d[unit['district']][unit['subdistrict']] += 1
    return None

find_total_station(2, 'ลำปาง')
print(d)