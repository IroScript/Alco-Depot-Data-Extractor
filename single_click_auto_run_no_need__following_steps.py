import os
import sys
import time
import tkinter as tk
from unittest.mock import patch

def run_step_1(base_dir):
    print("\n" + "="*60)
    print("STEP 1: Extract Product Level Net Sales from Database")
    print("="*60)
    import step_1_extract_Product_Level_Net_Sales_csv as s1
    
    class MockGUI:
        def __init__(self):
            self.all_depots_folder = os.path.join(base_dir, "All_Depots")
            self.output_dir = base_dir
            self.depot_folders = []
            if os.path.exists(self.all_depots_folder):
                for d in os.listdir(self.all_depots_folder):
                    dpath = os.path.join(self.all_depots_folder, d)
                    if os.path.isdir(dpath):
                        self.depot_folders.append(dpath)
            
            class DummyBtn:
                def config(self, **kwargs): pass
            self.start_btn = DummyBtn()
            
            class DummyRoot:
                def destroy(self): pass
                def mainloop(self):
                    # Instead of blocking, immediately run the processing logic!
                    if hasattr(self.parent, 'run_processing'):
                        self.parent.run_processing()
            
            self.root = DummyRoot()
            self.root.parent = self
            
        def log(self, msg): 
            print(f"  [LOG] {msg}")
            
        def update_progress(self, val, msg): 
            print(f"  [{val}%] {msg}")

    mock_gui = MockGUI()
    if not mock_gui.depot_folders:
        print("  [ERROR] No valid depots found in 'All_Depots' folder.")
        return False

    def mock_select_folders():
        return mock_gui

    # Patch the GUI creation and messageboxes
    with patch('step_1_extract_Product_Level_Net_Sales_csv.select_folders_gui', side_effect=mock_select_folders), \
         patch('tkinter.messagebox.showinfo', lambda t, m: print(f"\n  [SUCCESS] {m.split(chr(10))[0]}")), \
         patch('tkinter.messagebox.showerror', lambda t, m: print(f"\n  [ERROR] {m}")):
         
         s1.process_all_depots()
         
    return True

def run_step_2():
    print("\n" + "="*60)
    print("STEP 2: Generate MPO Target vs Achievement")
    print("="*60)
    import step_2_generate_MPO_Target_vs_Achievement_report as s2
    return True

def run_step_3():
    print("\n" + "="*60)
    print("STEP 3: Generate Zone Wise Product Sales Report")
    print("="*60)
    import step_3_generate_Zone_Wise_Product_Sales_Report as s3
    
    root = tk.Tk()
    root.withdraw()
    app = s3.ZoneReportApp(root)
    
    if not app.input_file.get():
        print("  [ERROR] Could not auto-detect input file (CSV) from Step 1!")
        root.destroy()
        return False

    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        root.quit()
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")
        root.quit()

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] Zone Wise Sales Report saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s3.ZoneReportApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    root.destroy()
    return True

def run_step_4():
    print("\n" + "="*60)
    print("STEP 4: Analyze Zone Wise Report (10 Parameters)")
    print("="*60)
    import step_4_analyze_Zone_Wise_Product_Sales_Report as s4
    
    root = tk.Tk()
    root.withdraw()
    app = s4.ZoneDataAnalyzerApp(root)
    
    if not app.input_file.get():
        print("  [ERROR] Could not auto-detect input file (Excel) from Step 3!")
        root.destroy()
        return False

    def on_success(title, msg):
        print(f"\n  [SUCCESS] {msg.split(chr(10))[0]}")
        root.quit()
        
    def on_error(title, msg):
        print(f"\n  [ERROR] {msg}")
        root.quit()

    def mock_show_success_dialog(out_path):
        print(f"\n  [SUCCESS] 10 Parameter Analysis saved to: {out_path}")

    class SyncThread:
        def __init__(self, target, *args, **kwargs):
            self.target = target
        def start(self):
            self.target()

    with patch('tkinter.messagebox.showinfo', side_effect=on_success), \
         patch('tkinter.messagebox.showerror', side_effect=on_error), \
         patch('threading.Thread', SyncThread), \
         patch.object(s4.ZoneDataAnalyzerApp, 'show_success_dialog', mock_show_success_dialog):
         
         app.run_process()
         
    root.destroy()
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("*" * 80)
    print("  FAST SALES DATA EXTRACTOR & ANALYZER - FULL AUTO RUN")
    print("*" * 80)
    
    # Run Step 1
    if not run_step_1(base_dir):
        print("\nPipeline stopped at Step 1.")
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Run Step 2
    if not run_step_2():
        print("\nPipeline stopped at Step 2.")
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Run Step 3
    if not run_step_3():
        print("\nPipeline stopped at Step 3.")
        return
        
    print("\nWaiting 5 seconds before next step...")
    time.sleep(5)
    
    # Run Step 4
    if not run_step_4():
        print("\nPipeline stopped at Step 4.")
        return
        
    print("\n" + "*" * 80)
    print("  ALL STEPS COMPLETED SUCCESSFULLY!")
    print("*" * 80)
    print("\nOutput files have been generated in the current directory.")

if __name__ == "__main__":
    main()
