import os
import glob

field_dir = r"c:\Users\Irak\Desktop\Barishal April Data\FieldEdit"
for root, dirs, files in os.walk(field_dir):
    for f in files:
        print(os.path.join(root, f))
