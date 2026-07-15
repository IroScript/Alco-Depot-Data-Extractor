import json
import os

BASE_DIR = r"C:\Users\Irak\Desktop\Barishal April Data - Copy\New folder\Alco-Depot-Data-Extractor\TOP_FIELD_FORCE"
json_path = os.path.join(BASE_DIR, "data", "api_data.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

mokast = data["strategic_6_products"]["MOKAST 10 TAB"]
print("ALL MONTHS count of MPOs in JSON:", len(mokast["mpo_top50_all"]))
for m, lst in mokast["mpo_top50_by_month"].items():
    print(f"Month {m} count of MPOs in JSON:", len(lst))
