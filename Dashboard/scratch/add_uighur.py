import re

file_path = r'C:\Users\Irak\Desktop\Alco_Depot_Data_Extractor_From_Git\Alco-Depot-Data-Extractor-main\Dashboard\css\style.css'
with open(file_path, 'a', encoding='utf-8') as f:
    f.write('\n\n/* Temporary MPO Table Font Change */\n#table-strategic-mpos th,\n#table-strategic-mpos td,\n#table-strategic-mpos .cell-clip {\n    font-family: \"Microsoft Uighur\", sans-serif !important;\n    font-size: 1.2rem !important; /* Uighur is usually very small, needs a bump */\n    letter-spacing: normal !important;\n}\n')

print("done adding uighur")
