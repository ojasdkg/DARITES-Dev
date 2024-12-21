import cv2
import os
import sys
import time
import re
from .db_operations import connect_db, insert_inspection
from .file_operations import load_processed_ids, save_processed_id, move_processed_folder, parse_rail_id_info
from .image_processing import mask_image, mse
from .clusterDistance import find_largest_cluster

def process_camera_folder(connection, rail_id, camera_id, good_folder, bad_folder):
    # Select the first image from the good_folder
    good_images = [img for img in os.listdir(good_folder) if os.path.isfile(os.path.join(good_folder, img))]
    if not good_images:
        print(f"No images found in good folder: {good_folder}")
        return

    # Use the first image as the reference image
    reference_img_name = good_images[0]
    reference_img_path = os.path.join(good_folder, reference_img_name)
    reference_img_gray = cv2.cvtColor(cv2.imread(reference_img_path), cv2.COLOR_BGR2GRAY)

    shift, defect_type = parse_rail_id_info(rail_id)
        
    # Compare the reference image with other good images
    for other_img_name in good_images:
        other_img_path = os.path.join(good_folder, other_img_name)
        if reference_img_path == other_img_path:
            continue  # Skip comparison with itself
        other_img_gray = cv2.cvtColor(cv2.imread(other_img_path), cv2.COLOR_BGR2GRAY)
        _, mask1 = mask_image(reference_img_path)
        _, mask2 = mask_image(other_img_path)
        edge_diff, _ = mse(mask1, mask2)
        image_diff, diff = mse(reference_img_gray, other_img_gray)

        # Parameters for cluster detection
        # size_threshold = 50  # Example threshold
        PPI = 9268
        resolution = 1 / (PPI / 25.4)  # mm/pixel
        
        # Calculate total distance using the diff image
        dimension_deviation = find_largest_cluster(diff, resolution)

        actual_status = os.path.basename(os.path.dirname(os.path.dirname(other_img_path))).split('_')[0]

        result_status = ''
        if (image_diff > 54.71 and camera_id == '40522337') or (image_diff > 54.69 and camera_id == '40522346') or (image_diff > 54.73 and camera_id == '40522366') or (image_diff > 54.82 and camera_id == '40522375') or (image_diff > 54.94 and camera_id == '40522378') or (image_diff > 55.05 and camera_id == '40525413'):
            result_status = 'fail'
        else:
            result_status = 'pass'

        confusion_classifier = ''
        if actual_status == 'good' and result_status == 'pass':
            confusion_classifier = 'TP'
        else:
            confusion_classifier = 'FN'
        
        insert_inspection(connection, rail_id, camera_id, reference_img_path, other_img_path, edge_diff, 0, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, 'operator_id', 'duty_id', shift, '', 0, 0)

    # Compare the reference image with all bad images
    for bad_img_name in os.listdir(bad_folder):
        bad_img_path = os.path.join(bad_folder, bad_img_name)
        if not os.path.isfile(bad_img_path):
            continue
        bad_img_gray = cv2.cvtColor(cv2.imread(bad_img_path), cv2.COLOR_BGR2GRAY)
        _, mask1 = mask_image(reference_img_path)
        _, mask2 = mask_image(bad_img_path)
        edge_diff, _ = mse(mask1, mask2)
        image_diff, diff = mse(reference_img_gray, bad_img_gray)
        actual_status = os.path.basename(os.path.dirname(os.path.dirname(bad_img_path))).split('_')[0]

        # Parameters for cluster detection
        # size_threshold = 50  # Example threshold
        PPI = 9268
        resolution = 1 / (PPI / 25.4)  # mm/pixel
        
        # Calculate total distance using the diff image
        dimension_deviation = find_largest_cluster(diff, resolution)

        result_status = ''
        if (image_diff > 54.71 and camera_id == '40522337') or (image_diff > 54.69 and camera_id == '40522346') or (image_diff > 54.73 and camera_id == '40522366') or (image_diff > 54.82 and camera_id == '40522375') or (image_diff > 54.94 and camera_id == '40522378') or (image_diff > 55.05 and camera_id == '40525413'):
            result_status = 'fail'
        else:
            result_status = 'pass'

        confusion_classifier = ''
        if actual_status == 'bad' and result_status == 'pass':
            confusion_classifier = 'FP'
        else:
            confusion_classifier = 'TN'

        defectType = ''
        if camera_id == '40522378':
            defectType = ["ASY (+)", "ASY (-)", "CP (+)", "CP (-)"]
        elif camera_id == '40525413':
            defectType = ["OHT", "UHT", "TF (+)", "TF (-)", "TNW", "TKW"]
        elif camera_id == '40522337':
            defectType = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"]
        elif camera_id == '40522346':
            defectType = ["NF", "WF", "FBC", "FBCx"]
        elif camera_id == '40522366':
            defectType = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW", "HH", "LH"]
        else: 
            defectType = ["OHT", "UHT", "HF (+)", "HF (-)", "TNW", "TKW"]

        insert_inspection(connection, rail_id, camera_id, reference_img_path, bad_img_path, edge_diff, 0, image_diff, dimension_deviation, actual_status, result_status, confusion_classifier, 'operator_id', 'duty_id', shift, defectType, 1, 0)

    pass

def all_rails_processed(base_dir, processed_rails):
    current_rails = {f for f in os.listdir(base_dir) if f.startswith('Rail_ID_')}
    new_rails = current_rails - processed_rails
    return new_rails, current_rails

def main_job():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_connection = connect_db()
    if not db_connection:
        print("Database connection failed. Exiting.")
        sys.exit()

    # # Fetch processed rail IDs to skip
    # processed_rail_ids = fetch_processed_rail_ids(db_connection)
    processed_ids = load_processed_ids()
    processed_rails = set()
    
    while True:
        new_rails, processed_rails = all_rails_processed(base_dir, processed_rails)
        if new_rails:
        # rail_folders = [f for f in os.listdir(base_dir) if f.startswith('Rail_ID_')]
            for rail_id_folder in new_rails:
                rail_path = os.path.join(base_dir, rail_id_folder)
                rail_id = '_'.join(rail_id_folder.split('_')[2:])

                good_img_folder = os.path.join(rail_path, 'good_img')
                bad_img_folder = os.path.join(rail_path, 'bad_img')

                camera_folders = ['40522337', '40522346', '40522366', '40522375', '40522378', '40525413']
                for camera_folder in camera_folders:
                    camera_id = re.findall(r'\d+', camera_folder)[0]
                    good_folder = os.path.join(good_img_folder, camera_folder)
                    bad_folder = os.path.join(bad_img_folder, camera_folder)
                
                    if os.path.isdir(good_folder) and os.path.isdir(bad_folder):
                        process_camera_folder(db_connection, rail_id, camera_id, good_folder, bad_folder)

                save_processed_id(rail_id)
                move_processed_folder(rail_path)  # Move the processed folder
                    
            print("New rail folders processed.")
            # time.sleep(600)  # wait 10 minutes before next cycle
        else:
            print("No new rail folders. Waiting for next cycle...")
        time.sleep(600)  # wait 10 minutes before next cycle

if __name__ == "__main__":
    main_job()