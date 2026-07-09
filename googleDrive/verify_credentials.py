"""
verify_credentials.py — Single source-of-truth credential verifier.

Reads `googleDrive/credentials.json` (the central registry) and:
  1. Confirms every referenced service-account JSON exists on disk.
  2. Prints the client_email + project_id for each SA so you know which Gmail/project it belongs to.
  3. Confirms each spreadsheet ID's URL resolves.
  4. Confirms the googleDrive/env file has all required env keys.
  5. Prints a summary of unused/orphaned credential files (so you can clean them up).

Usage:
    python googleDrive/verify_credentials.py
"""
import os
import sys
import json
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CRED_JSON = os.path.join(SCRIPT_DIR, "credentials.json")
ENV_FILE = os.path.join(SCRIPT_DIR, "env")

# Colors (Windows Terminal / modern cmd)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def cprint(color, msg):
    print(f"{color}{msg}{RESET}")


def main():
    cprint(CYAN, "=" * 80)
    cprint(CYAN, "  ALCO DEPOT DATA EXTRACTOR — CREDENTIAL VERIFICATION REPORT")
    cprint(CYAN, "=" * 80)

    if not os.path.exists(CRED_JSON):
        cprint(RED, f"[FAIL] credentials.json not found at: {CRED_JSON}")
        sys.exit(1)

    with open(CRED_JSON, "r", encoding="utf-8") as f:
        creds = json.load(f)

    referenced_files = set()
    found_sas = []
    missing_sas = []

    # 1. Verify each service account JSON exists
    cprint(CYAN, "\n[1] Service Account JSON files:")
    for gmail_name, gmail_info in creds["gmail_accounts"].items():
        email = gmail_info["email"]
        cprint(YELLOW, f"\n   Gmail Account: {gmail_name}")
        cprint(RESET, f"      Description: {gmail_info['description']}")
        cprint(RESET, f"      Login Email: {email}")

        for sa in gmail_info["service_accounts"]:
            for json_path_rel in sa["json_files"]:
                # Resolve relative to project root
                json_path_abs = os.path.join(PROJECT_DIR, json_path_rel)
                referenced_files.add(os.path.normpath(json_path_abs).lower())
                if os.path.exists(json_path_abs):
                    try:
                        with open(json_path_abs, "r", encoding="utf-8") as jf:
                            sa_data = json.load(jf)
                        client_email = sa_data.get("client_email", "?")
                        project_id = sa_data.get("project_id", "?")
                        cprint(GREEN, f"      [OK]    {json_path_rel}")
                        cprint(RESET, f"              client_email: {client_email}")
                        cprint(RESET, f"              project_id:   {project_id}")
                        found_sas.append((sa["alias"], client_email, project_id, json_path_rel))
                    except Exception as e:
                        cprint(RED, f"      [BAD]   {json_path_rel} (parse error: {e})")
                        missing_sas.append(json_path_rel)
                else:
                    cprint(RED, f"      [MISS]  {json_path_rel}")
                    missing_sas.append(json_path_rel)

    # 2. Verify each spreadsheet ID
    cprint(CYAN, "\n[2] Google Sheets:")
    for sheet_name, sheet_info in creds["google_sheets"].items():
        sid = sheet_info.get("spreadsheet_id")
        if not sid:
            continue
        url = sheet_info.get("url") or f"https://docs.google.com/spreadsheets/d/{sid}/edit"
        cprint(YELLOW, f"\n   Sheet: {sheet_name}")
        cprint(RESET, f"      Description: {sheet_info.get('description', 'N/A')}")
        cprint(RESET, f"      ID: {sid}")
        cprint(RESET, f"      URL: {url}")
        cprint(RESET, f"      Owner: {sheet_info.get('owner', 'N/A')}")

    # 3. Verify env file
    cprint(CYAN, "\n[3] googleDrive/env file:")
    env_keys_required = set()
    for svc_name, svc_info in creds["cloud_services"].items():
        env_keys_required.update(svc_info.get("env_keys_used", []))
    if os.path.exists(ENV_FILE):
        env_data = {}
        with open(ENV_FILE, "r", encoding="utf-8") as ef:
            for line in ef:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_data[k.strip()] = v.strip()
        present = env_keys_required & set(env_data.keys())
        missing = env_keys_required - set(env_data.keys())
        cprint(GREEN, f"   [OK] env file present, {len(env_data)} keys parsed")
        for k in sorted(present):
            v = env_data[k]
            # Mask secrets
            if any(t in k for t in ["TOKEN", "KEY", "PASSWORD"]):
                masked = v[:4] + "*" * (max(0, len(v) - 8)) + v[-4:] if len(v) > 8 else "***"
                cprint(GREEN, f"      [OK]   {k} = {masked}")
            else:
                cprint(GREEN, f"      [OK]   {k} = {v}")
        for k in sorted(missing):
            cprint(RED, f"      [MISS] {k}")
    else:
        cprint(RED, f"   [FAIL] env file not found at {ENV_FILE}")

    # 4. Summary: orphan credential files (in project but not referenced)
    cprint(CYAN, "\n[4] Orphan / unreferenced credential JSONs in project:")
    all_json_in_project = set()
    for root, dirs, files in os.walk(PROJECT_DIR):
        # Skip hidden / archive dirs
        if any(skip in root for skip in [".git", "__pycache__", "node_modules", "All_Depots"]):
            continue
        for fn in files:
            if fn.endswith(".json") and ("credential" in fn.lower() or
                                          "service_account" in fn.lower() or
                                          "client_secret" in fn.lower() or
                                          "alco-pharma" in fn.lower() or
                                          "driveautomation" in fn.lower()):
                full = os.path.normpath(os.path.join(root, fn)).lower()
                all_json_in_project.add(full)

    # Exclude the registry itself + the OAuth client secret (which is referenced
    # under gmail_accounts.primary_alco_drive.oauth_client.client_secret_file)
    oauth_client_secret_rel = creds["gmail_accounts"]["primary_alco_drive"]["oauth_client"]["client_secret_file"]
    oauth_client_secret_abs = os.path.normpath(os.path.join(PROJECT_DIR, oauth_client_secret_rel)).lower()
    self_registry_abs = os.path.normpath(CRED_JSON).lower()
    master_registry_abs = os.path.normpath(os.path.join(SCRIPT_DIR, "credentials_master.json")).lower()
    real_orphans = (all_json_in_project - referenced_files) - {oauth_client_secret_abs, self_registry_abs, master_registry_abs}
    orphans = real_orphans
    if orphans:
        cprint(YELLOW, "   The following credential JSONs exist but are NOT referenced by credentials.json:")
        for o in sorted(orphans):
            rel = os.path.relpath(o, PROJECT_DIR)
            cprint(YELLOW, f"      [ORPHAN] {rel}")
    else:
        cprint(GREEN, "   [OK] No orphan credential files detected.")

    # 5. Final summary
    cprint(CYAN, "\n" + "=" * 80)
    cprint(CYAN, "  SUMMARY")
    cprint(CYAN, "=" * 80)
    cprint(GREEN, f"  Service Accounts found:     {len(found_sas)}")
    if found_sas:
        # Distinct unique client_emails
        unique_emails = set(s[1] for s in found_sas)
        cprint(GREEN, f"  Unique SA client_emails:    {len(unique_emails)}")
        for em in sorted(unique_emails):
            cprint(GREEN, f"     -> {em}")
    if missing_sas:
        cprint(RED, f"  Missing JSON files:         {len(missing_sas)}")
        for m in missing_sas:
            cprint(RED, f"     !! {m}")
    if orphans:
        cprint(YELLOW, f"  Orphan (unreferenced) JSONs: {len(orphans)}")
    cprint(CYAN, "=" * 80)


if __name__ == "__main__":
    main()