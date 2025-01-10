import usaddress
from geopy.geocoders import Nominatim

# 示例地址
address = "浙江省,杭州市,滨江区,滨江区海康路100号,18888888888"

# 使用 usaddress 解析地址
parsed_address = usaddress.parse(address)
parsed_address_dict = usaddress.tag(address)

print("Parsed Address:", parsed_address)
print("Parsed Address (Dictionary):", parsed_address_dict)

# 使用 geopy 获取地理坐标
geolocator = Nominatim(user_agent="address_parser")
location = geolocator.geocode(address)

print("Latitude:", location.latitude)
print("Longitude:", location.longitude)
