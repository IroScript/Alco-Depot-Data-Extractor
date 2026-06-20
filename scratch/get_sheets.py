import openpyxl

file_path = r'c:\Users\Irak\Desktop\Barishal April Data\FieldEdit\SAMPLE_FIELD_DATA_INPUT.xlsx'
wb = openpyxl.load_workbook(file_path, read_only=True)
print("Sheet names:", wb.sheetnames)
