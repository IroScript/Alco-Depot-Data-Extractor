import os
import re
import json
import glob
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ══════════════════════════════════════════════════════════════════
#  Design tokens (matching Step 3 & Step 4 scripts)
# ══════════════════════════════════════════════════════════════════
_C = {
    'void'   : '#03040A',
    'panel'  : '#060816',
    'panel2' : '#050912',
    'cyan'   : '#00F2FE',
    'mag'    : '#FF00AA',
    'violet' : '#9D00FF',
    'green'  : '#00FF88',
    'red'    : '#FF2244',
    'text'   : '#D8F0F8',
    'muted'  : '#5F98A7',
    'border' : '#102A45',
    'hot'    : '#0D2A3F',
}

W_WIN, H_WIN = 580, 420

class GoogleDriveUploadApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ALCO GOOGLE DRIVE AUTOMATION")
        self.root.geometry(f"{W_WIN}x{H_WIN}")
        self.root.resizable(False, False)
        self.root.configure(bg=_C['void'])

        # State Variables
        # Credentials now come from credentials_loader.py (single source of truth).
        # No more hardcoded JSON paths. The optional user-overridden folder ID is
        # persisted to <project>/.upload_folder.json (local, gitignored) so users
        # can override the default depot folder without polluting credentials.
        try:
            from googleDrive.credentials_loader import get_drive_folder_id
            _default_folder = get_drive_folder_id('BARISHAL') or ''
        except Exception:
            _default_folder = ''
        self.config_path = os.path.join(PROJECT_DIR, '.upload_folder.json')

        self.drive_folder_id = tk.StringVar(value=_default_folder)
        self.load_config()

        self.files_to_upload = []
        self.scan_latest_files()

        # GUI Components
        self.setup_ui()

    def load_config(self):
        """Load folder ID from config.json if present"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.drive_folder_id.set(config.get("drive_folder_id", ""))
            except Exception as e:
                print(f"Error loading config.json: {e}")

    def save_config(self):
        """Save folder ID back to config.json"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                config["drive_folder_id"] = self.drive_folder_id.get().strip()
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                print(f"Error saving config.json: {e}")

    def scan_latest_files(self):
        """Scans the workspace for the latest workflow generated files"""
        self.files_to_upload = []
        patterns = [
            ("*Product_Level_Net_Sales*.csv", "01: Product-Level Net Sales (CSV)"),
            ("02A_MPO_Achievement_Pivot_Analysis_*.xlsx", "02A: MPO Achievement Pivot"),
            ("02B_Parsed_Target_Data_Summary_*.xlsx", "02B: Parsed Target Data"),
            ("02C_MPO_Matched_Targets_Summary_*.xlsx", "02C: MPO Matched Targets"),
            ("02D_FINAL_MPO_Target_vs_Achievement_Formula_*.xlsx", "02D: Final Report (Formulas)"),
            ("02E_FINAL_MPO_Target_vs_Achievement_Values_*.xlsx", "02E: Final Report (Values)"),
            ("03_Zone_Wise_Sales_Grouped_Report_*.xlsx", "03: Zone-Wise Sales Report"),
            ("04_Analyzed_10_Param_*.xlsx", "04: 10 Parameter Analyzed Report")
        ]

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        for glob_pat, label in patterns:
            matches = glob.glob(os.path.join(base_dir, glob_pat))
            if matches:
                # Find the latest modified file matching the pattern
                latest_file = max(matches, key=os.path.getmtime)
                self.files_to_upload.append((latest_file, label))

    def setup_ui(self):
        # Header Canvas
        self.header = tk.Canvas(self.root, width=W_WIN, height=50, bg=_C['panel'], highlightthickness=0)
        self.header.pack(fill='x')
        self.header.create_text(20, 25, text="GOOGLE DRIVE UPLOADER", font=('Courier New', 14, 'bold'), fill=_C['cyan'], anchor='w')
        self.header.create_line(0, 49, W_WIN, 49, fill=_C['border'])

        # Main Layout Container
        main_frame = tk.Frame(self.root, bg=_C['void'], padx=20, pady=15)
        main_frame.pack(fill='both', expand=True)

        # Drive Folder Input Section
        folder_frame = tk.Frame(main_frame, bg=_C['void'])
        folder_frame.pack(fill='x', pady=(0, 10))

        tk.Label(folder_frame, text="Google Drive Parent Folder ID (Optional):", font=('Courier New', 9, 'bold'),
                 bg=_C['void'], fg=_C['muted']).pack(anchor='w', pady=(0, 2))

        input_container = tk.Frame(folder_frame, bg=_C['border'], bd=1, padx=1, pady=1)
        input_container.pack(fill='x')

        self.txt_folder_id = tk.Entry(input_container, textvariable=self.drive_folder_id, font=('Courier New', 9),
                                      bg=_C['panel2'], fg=_C['text'], insertbackground=_C['cyan'], relief='flat')
        self.txt_folder_id.pack(fill='x', ipady=4, padx=4)

        # Detected Files Frame
        files_frame = tk.LabelFrame(main_frame, text=" Detected Latest Files to Upload ", font=('Courier New', 9, 'bold'),
                                    bg=_C['void'], fg=_C['cyan'], bd=1, relief='solid', padx=10, pady=10)
        files_frame.pack(fill='both', expand=True, pady=(0, 15))
        # Keep border color styling customized
        files_frame.configure(highlightbackground=_C['border'], highlightcolor=_C['border'])

        self.listbox = tk.Listbox(files_frame, bg=_C['panel2'], fg=_C['text'], font=('Courier New', 8),
                                  selectbackground=_C['hot'], selectforeground='#FFFFFF', relief='flat',
                                  highlightthickness=1, highlightbackground=_C['border'])
        self.listbox.pack(fill='both', expand=True)

        for filepath, label in self.files_to_upload:
            filename = os.path.basename(filepath)
            self.listbox.insert(tk.END, f" {label} -> {filename}")

        if not self.files_to_upload:
            self.listbox.insert(tk.END, " [No generated files found in workspace! Run workflow scripts first.]")
            self.listbox.configure(fg=_C['red'])

        # Progress Section
        progress_frame = tk.Frame(main_frame, bg=_C['void'])
        progress_frame.pack(fill='x', pady=(0, 15))

        self.lbl_progress = tk.Label(progress_frame, text="Idle", font=('Courier New', 9, 'bold'),
                                     bg=_C['void'], fg=_C['muted'])
        self.lbl_progress.pack(anchor='w')

        # Styled Progress Bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Cyan.Horizontal.TProgressbar", thickness=8, troughcolor=_C['panel'], 
                        background=_C['cyan'], bordercolor=_C['border'])
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', style="Cyan.Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=(3, 0))

        # Bottom Button Bar
        btn_frame = tk.Frame(main_frame, bg=_C['void'])
        btn_frame.pack(fill='x')

        self.btn_upload = tk.Button(btn_frame, text="▶ UPLOAD TO GOOGLE DRIVE", command=self.start_upload,
                                     font=('Courier New', 10, 'bold'), bg='#0A1F36', fg=_C['green'],
                                     activebackground=_C['hot'], activeforeground='#FFFFFF', relief='flat',
                                     cursor='hand2', highlightthickness=1, highlightbackground=_C['green'], bd=0)
        self.btn_upload.pack(side='right', padx=(10, 0), ipady=6, ipadx=15)

        self.btn_refresh = tk.Button(btn_frame, text="🔄 REFRESH FILES", command=self.refresh_files,
                                      font=('Courier New', 9), bg=_C['panel2'], fg=_C['text'],
                                      activebackground=_C['hot'], activeforeground='#FFFFFF', relief='flat',
                                      cursor='hand2', highlightthickness=1, highlightbackground=_C['border'], bd=0)
        self.btn_refresh.pack(side='right', ipady=6, ipadx=10)

        # Status Light Label
        self.lbl_status = tk.Label(btn_frame, text="◉ READY", font=('Courier New', 9, 'bold'),
                                   bg=_C['void'], fg=_C['cyan'])
        self.lbl_status.pack(side='left', pady=5)

    def refresh_files(self):
        """Scans again and updates the file list UI"""
        self.scan_latest_files()
        self.listbox.delete(0, tk.END)
        for filepath, label in self.files_to_upload:
            filename = os.path.basename(filepath)
            self.listbox.insert(tk.END, f" {label} -> {filename}")
        if not self.files_to_upload:
            self.listbox.insert(tk.END, " [No generated files found in workspace! Run workflow scripts first.]")
            self.listbox.configure(fg=_C['red'])
        else:
            self.listbox.configure(fg=_C['text'])
        self.lbl_progress.configure(text="Files list refreshed", fg=_C['muted'])

    def log_progress(self, val, msg, color=None):
        """Thread-safe progress updates"""
        self.root.after(0, lambda: [
            self.progress_bar.configure(value=val),
            self.lbl_progress.configure(text=msg, fg=color if color else _C['text'])
        ])

    def start_upload(self):
        if not self.files_to_upload:
            messagebox.showerror("Error", "No files found to upload!")
            return

        # Credentials come from credentials_master.json via credentials_loader — verify it's reachable.
        try:
            from credentials_loader import get_drive_service_account_credentials  # noqa: F401
        except Exception as e:
            messagebox.showerror("Error", f"credentials_master.json not reachable:\n{e}")
            return

        self.btn_upload.configure(state='disabled')
        self.btn_refresh.configure(state='disabled')
        self.lbl_status.configure(text="◉ UPLOADING...", fg=_C['mag'])
        
        # Save current folder ID in config
        self.save_config()

        # Run upload logic inside background thread to keep UI alive
        threading.Thread(target=self.upload_thread_proc, daemon=True).start()

    def upload_thread_proc(self):
        try:
            from credentials_loader import get_drive_service_account_credentials
            self.log_progress(5, "Connecting to Google Drive API...")
            scopes = ['https://www.googleapis.com/auth/drive']
            creds = get_drive_service_account_credentials(scopes=scopes)
            drive_service = build('drive', 'v3', credentials=creds)

            # Retrieve Parent Folder ID
            parent_folder_id = self.drive_folder_id.get().strip()
            if not parent_folder_id:
                parent_folder_id = None
                self.log_progress(10, "Uploading directly to Root Drive (Parent Folder ID empty)...")
            else:
                self.log_progress(10, f"Validating Parent Folder ID: {parent_folder_id}...")
            
            # Create a dedicated run folder with timestamp for organization
            timestamp = datetime.now().strftime('%d-%b-%Y %I.%M %p')
            run_folder_name = f"Barishal April Data Run - {timestamp}"
            
            self.log_progress(15, f"Creating folder: '{run_folder_name}'...")
            
            folder_metadata = {
                'name': run_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]

            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            target_folder_id = folder.get('id')
            
            self.log_progress(25, f"Folder created ID: {target_folder_id}")

            total_files = len(self.files_to_upload)
            
            for idx, (filepath, label) in enumerate(self.files_to_upload):
                filename = os.path.basename(filepath)
                progress_offset = 25 + int((idx / total_files) * 70)
                
                self.log_progress(progress_offset, f"Uploading: {filename} ({idx+1}/{total_files})...")
                
                file_metadata = {
                    'name': filename,
                    'parents': [target_folder_id]
                }
                
                # Determine mimetype dynamically based on extension
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                if filename.endswith('.csv'):
                    mimetype = 'text/csv'
                    
                media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
                
                # Execute Upload
                drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            self.root.after(0, lambda: [
                self.log_progress(100, "✓ All files uploaded successfully!", _C['green']),
                self.lbl_status.configure(text="◉ SUCCESS", fg=_C['green']),
                messagebox.showinfo("Success", f"All {total_files} files successfully uploaded!\n\nFolder: {run_folder_name}"),
                self.btn_upload.configure(state='normal'),
                self.btn_refresh.configure(state='normal')
            ])

        except Exception as e:
            self.root.after(0, lambda err=e: [
                self.log_progress(0, "Execution failed due to error", _C['red']),
                self.lbl_status.configure(text="◉ ERROR", fg=_C['red']),
                messagebox.showerror("Upload Failed", f"An error occurred:\n\n{str(err)}"),
                self.btn_upload.configure(state='normal'),
                self.btn_refresh.configure(state='normal')
            ])

if __name__ == "__main__":
    root = tk.Tk()
    app = GoogleDriveUploadApp(root)
    root.mainloop()
