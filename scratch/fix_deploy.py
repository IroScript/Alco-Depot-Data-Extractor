import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\deploy.py'
with open(file_path, 'r', encoding='utf-8') as f:
    py = f.read()

# Add requirements.txt to items
old_items = '''        "local_gateway_sync.py"
    ]'''
new_items = '''        "local_gateway_sync.py",
        "requirements.txt"
    ]'''
py = py.replace(old_items, new_items)

# Add pip install to cmd
old_cmd = '''        cmd = (
            "unzip -o erp_setup.zip && "
            "pkill -f telegram_bot.py ; "
            "workon erp_env && "
            "nohup python telegram_bot.py > bot.log 2>&1 &"
        )'''
new_cmd = '''        cmd = (
            "unzip -o erp_setup.zip && "
            "pkill -f telegram_bot.py ; "
            "workon erp_env && "
            "pip install -r requirements.txt && "
            "nohup python telegram_bot.py > bot.log 2>&1 &"
        )'''
py = py.replace(old_cmd, new_cmd)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(py)

print("done fixing deploy.py")
