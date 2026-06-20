import os
import sys
import tkinter as tk
from unittest.mock import patch

# Add parent directory to sys.path to resolve local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Reconfigure console output encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    except:
        pass

import step_1_extract_Product_Level_Net_Sales_csv as s1

class MockGUI:
    def __init__(self):
        self.all_depots_folder = r'c:\Users\Irak\Desktop\Barishal April Data\googleDrive\All_Depots'
        self.output_dir = r'c:\Users\Irak\Desktop\Barishal April Data'
        self.depot_folders = [os.path.join(self.all_depots_folder, 'BARISHAL')]
        
        class DummyBtn:
            def config(self, **kwargs): pass
        self.start_btn = DummyBtn()
        
        class DummyRoot:
            def destroy(self): pass
            def mainloop(self):
                if hasattr(self.parent, 'run_processing'):
                    self.parent.run_processing()
        self.root = DummyRoot()
        self.root.parent = self
        
    def log(self, msg): 
        print(f"  [LOG] {msg}")
        
    def update_progress(self, val, msg): 
        print(f"  [{val}%] {msg}")

def main():
    mock_gui = MockGUI()
    
    def mock_select_folders():
        return mock_gui

    # Patch the GUI creation and messageboxes to execute headlessly
    with patch('step_1_extract_Product_Level_Net_Sales_csv.select_folders_gui', side_effect=mock_select_folders), \
         patch('tkinter.messagebox.showinfo', lambda t, m: print(f"\n  [SUCCESS] {m.split(chr(10))[0]}")), \
         patch('tkinter.messagebox.showerror', lambda t, m: print(f"\n  [ERROR] {m}")):
         
         s1.process_all_depots()

if __name__ == '__main__':
    main()
