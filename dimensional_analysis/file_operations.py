import os
import shutil
import re

PROCESSED_DIR = "Processed_Rail_IDs"
PROCESSED_IDS_FILE = "Processed_Rail_IDs.txt"

def parse_rail_id_info(rail_id):
    # Extract shift_grade as the character after the date
    shift_grade_match = re.search(r"U\d{6}([A-Z])\d{3}", rail_id)
    shift_grade = shift_grade_match.group(1) if shift_grade_match else None
    
    # Extract defect_type as the text after the third underscore
    defect_match = re.search(r"(?:[^_]*_){1}(.*)", rail_id)
    defect_type = defect_match.group(1) if defect_match else None
    
    return shift_grade, defect_type

def load_processed_ids():
    if not os.path.exists(PROCESSED_IDS_FILE):
        return set()
    with open(PROCESSED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_processed_id(rail_id):
    with open(PROCESSED_IDS_FILE, "a") as f:
        f.write(f"{rail_id}\n")

def move_processed_folder(rail_path):
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
    shutil.move(rail_path, PROCESSED_DIR)