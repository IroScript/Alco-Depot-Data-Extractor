"""Standalone test for the 3-stage / 3-layer verification logic.
Self-contained copy of the verification functions + tests them
against the existing local depot folders under
googleDrive/All_Depots/<DEPOT>/Data/
"""
import os
import sys
from pathlib import Path

BASE_DEPOT_DIR = r"C:\Users\Irak\Desktop\Barishal April Data - Copy\New folder\Alco-Depot-Data-Extractor\googleDrive\All_Depots"
EXPECTED_MIN_FILES = 15


def _layer1_os_pathlib(depot_name):
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    s1 = os.path.isdir(depot_dir)
    s2 = False
    if s1:
        for root, dirs, _files in os.walk(depot_dir):
            if "Data" in dirs:
                candidate = os.path.join(root, "Data")
                if os.path.isdir(candidate):
                    s2 = True
                    break
    s3_count = 0
    if s2:
        for root, dirs, _files in os.walk(depot_dir):
            if "Data" in dirs:
                data_dir = os.path.join(root, "Data")
                try:
                    for entry in os.listdir(data_dir):
                        full = os.path.join(data_dir, entry)
                        if not os.path.isfile(full):
                            continue
                        low = entry.lower()
                        if low.endswith(".mdf") or low.endswith(".ldf"):
                            try:
                                if os.path.getsize(full) > 0:
                                    s3_count += 1
                            except OSError:
                                pass
                except OSError:
                    pass
                break
    s3 = s3_count >= EXPECTED_MIN_FILES
    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def _layer2_pathlib_rglob(depot_name):
    depot_path = Path(BASE_DEPOT_DIR) / depot_name
    s1 = depot_path.is_dir()
    s2 = False
    if s1:
        for p in depot_path.rglob("Data"):
            if p.is_dir():
                s2 = True
                break
        if not s2:
            for p in depot_path.rglob("*"):
                if p.is_dir() and p.name.lower() == "data":
                    s2 = True
                    break
    s3_count = 0
    if s2:
        for p in depot_path.rglob("*"):
            if p.is_dir() and p.name.lower() == "data":
                try:
                    for f in p.iterdir():
                        if not f.is_file():
                            continue
                        if f.suffix.lower() in (".mdf", ".ldf"):
                            try:
                                if f.stat().st_size > 0:
                                    s3_count += 1
                            except OSError:
                                pass
                except OSError:
                    pass
                break
    s3 = s3_count >= EXPECTED_MIN_FILES
    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def _layer3_scandir_size(depot_name):
    depot_dir = os.path.join(BASE_DEPOT_DIR, depot_name)
    s1 = False
    try:
        parent = os.path.dirname(depot_dir)
        with os.scandir(parent) as it:
            for entry in it:
                if entry.name == depot_name and entry.is_dir():
                    s1 = True
                    break
    except (FileNotFoundError, OSError):
        s1 = os.path.isdir(depot_dir)
    s2 = False
    data_dir_found = None
    if s1:
        try:
            stack = [depot_dir]
            while stack:
                current = stack.pop()
                try:
                    with os.scandir(current) as it:
                        for entry in it:
                            if entry.is_dir(follow_symlinks=False):
                                if entry.name.lower() == "data":
                                    data_dir_found = entry.path
                                    s2 = True
                                    break
                                stack.append(entry.path)
                        if s2:
                            break
                except (PermissionError, OSError):
                    continue
        except OSError:
            pass
    s3_count = 0
    if s2 and data_dir_found:
        try:
            with os.scandir(data_dir_found) as it:
                for entry in it:
                    if not entry.is_file():
                        continue
                    low = entry.name.lower()
                    if low.endswith(".mdf") or low.endswith(".ldf"):
                        try:
                            st = entry.stat()
                            if st.st_size > 0:
                                s3_count += 1
                        except OSError:
                            pass
        except OSError:
            pass
    s3 = s3_count >= EXPECTED_MIN_FILES
    return {"s1": s1, "s2": s2, "s3": s3, "s3_count": s3_count}


def verify_local_depot_complete(depot_name, min_files=EXPECTED_MIN_FILES,
                                 verbose=True):
    l1 = _layer1_os_pathlib(depot_name)
    l2 = _layer2_pathlib_rglob(depot_name)
    l3 = _layer3_scandir_size(depot_name)
    stage1_ok = l1["s1"] and l2["s1"] and l3["s1"]
    stage2_ok = l1["s2"] and l2["s2"] and l3["s2"]
    counts = [l1["s3_count"], l2["s3_count"], l3["s3_count"]]
    max_count = max(counts)
    min_count = min(counts)
    count_consistent = (max_count - min_count) <= 1
    stage3_ok = (l1["s3"] and l2["s3"] and l3["s3"]
                 and max_count >= min_files and count_consistent)
    all_passed = stage1_ok and stage2_ok and stage3_ok
    if verbose:
        l1c = l1["s3_count"]; l2c = l2["s3_count"]; l3c = l3["s3_count"]
        print(f"    [VERIFY] {depot_name}")
        print(f"      Stage1 (Depot folder):      L1={l1['s1']!s:5s} L2={l2['s1']!s:5s} L3={l3['s1']!s:5s} -> {'OK' if stage1_ok else 'FAIL'}")
        print(f"      Stage2 (Data folder):       L1={l1['s2']!s:5s} L2={l2['s2']!s:5s} L3={l3['s2']!s:5s} -> {'OK' if stage2_ok else 'FAIL'}")
        print(f"      Stage3 ({min_files}+ files):     L1={l1c:2d}    L2={l2c:2d}    L3={l3c:2d}    -> {'OK' if stage3_ok else 'FAIL'}")
        print(f"      >>> {'LOCAL COMPLETE - will skip Google Drive' if all_passed else 'INCOMPLETE - must download'}")
    report = {"layer1": l1, "layer2": l2, "layer3": l3,
              "stage1_ok": stage1_ok, "stage2_ok": stage2_ok,
              "stage3_ok": stage3_ok, "all_passed": all_passed,
              "counts": counts}
    return all_passed, report


if __name__ == "__main__":
    print("=" * 70)
    print("TEST 1: FARIDPUR (should PASS - 17 files present)")
    print("=" * 70)
    ok, rep = verify_local_depot_complete("FARIDPUR", verbose=True)
    print(f"Result: {ok}\n")

    print("\n" + "=" * 70)
    print("TEST 2: BARISHAL (should FAIL - only 2 files)")
    print("=" * 70)
    ok, rep = verify_local_depot_complete("BARISHAL", verbose=True)
    print(f"Result: {ok}\n")

    print("\n" + "=" * 70)
    print("TEST 3: NONEXISTENT_DEPOT (should FAIL)")
    print("=" * 70)
    ok, rep = verify_local_depot_complete("NONEXISTENT_DEPOT", verbose=True)
    print(f"Result: {ok}\n")

    print("\n" + "=" * 70)
    print("TEST 4: All depots at once")
    print("=" * 70)
    all_depots = ["BARISHAL", "CHATTOGRAM", "CUMILLA", "DHAKA-1", "DHAKA-2",
                  "FARIDPUR", "JASHORE", "MYMENSINGH", "RAJSHAHI", "RANGPUR", "SYLHET"]
    passed, failed = [], []
    for d in all_depots:
        ok, rep = verify_local_depot_complete(d, verbose=False)
        if ok:
            passed.append(d)
        else:
            failed.append(d)
        print(f"  {d:12s} -> {'PASS (skip GD)' if ok else 'FAIL (download)'}    counts={rep['counts']}")

    print(f"\n  Summary: {len(passed)} PASS, {len(failed)} FAIL")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
