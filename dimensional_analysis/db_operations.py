import mysql.connector
# from dimensional_analysis.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Database connection
def connect_db(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    
# Insert Inspection Record    
def insert_inspection(connection, rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head):
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO Dimensional_Inspection (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (rail_id, camera_id, base_image_path, inspected_image_path, edge_diff, chop_diff, image_diff, actual_status, result_status, confusion_classifier, operator_id, duty_id, shift, defect_type, distance_from_head))
    connection.commit()