import logging
from fastapi import FastAPI, Response
import psycopg2
import csv
import os
from fastapi.middleware.cors import CORSMiddleware
from botocore.exceptions import NoCredentialsError
import boto3

# Initialize FastAPI app
app = FastAPI()

# S3 configuration
S3_BUCKET = "ocr-swingbell"
S3_REGION = "ap-southeast-2"
s3_client = boto3.client("s3", region_name=S3_REGION)

# Enable CORS for frontend URL
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection (PostgreSQL)
conn = psycopg2.connect(
    dbname="swingbell",
    user="asimith",
    password="asimith",
    host="13.126.33.160",
    port="5432"
)
cur = conn.cursor()

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Function to execute a query and return data
def fetch_query_data(query):
    cur.execute(query)
    return cur.fetchall(), [desc[0] for desc in cur.description]

# Function to get facility_id from branch_id
def get_facility_id_from_branch_id(branch_id):
    query = f"SELECT facility_id FROM facility_branch WHERE branch_id = '{branch_id}'"
    cur.execute(query)
    result = cur.fetchone()
    return result[0] if result else None

# Function to truncate long text fields
def truncate_field(field, max_length=100):
    if isinstance(field, str) and len(field) > max_length:
        return field[:max_length] + '...'  # Truncate and add ellipsis
    return field

# Function to create a CSV from query data with truncated long fields
def create_csv(data, headers, csv_filename="query_result.csv"):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Writing headers
        for row in data:  # Writing data rows, truncating long fields
            truncated_row = [truncate_field(field) for field in row]
            writer.writerow(truncated_row)
    return csv_filename

# Function to upload CSV to S3
def upload_to_s3(file_path, s3_folder):
    try:
        s3_key = f"{s3_folder}/{os.path.basename(file_path)}"
        logging.info(f"Uploading {file_path} to S3 bucket {S3_BUCKET} at {s3_key}")
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        s3_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logging.info(f"File successfully uploaded to {s3_url}")
        return s3_url
    except FileNotFoundError:
        logging.error("The file was not found")
        return "The file was not found"
    except NoCredentialsError:
        logging.error("Credentials not available")
        return "Credentials not available"
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return f"An error occurred: {str(e)}"

# Function to download CSV from S3
def download_from_s3(s3_url, download_path):
    try:
        s3_key = s3_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[1]
        logging.info(f"Downloading from S3 {s3_url} to local path {download_path}")
        s3_client.download_file(S3_BUCKET, s3_key, download_path)
        logging.info(f"File successfully downloaded to {download_path}")
        return download_path
    except Exception as e:
        logging.error(f"An error occurred during download: {str(e)}")
        return f"An error occurred: {str(e)}"


# Mapping for queries for each table
TABLE_QUERIES = {
    'diagnostic_report': "SELECT * FROM diagnostic_report WHERE branch_id = '{branch_id}'",
    'diagnostic_report_detail': """
        SELECT drd.*, dr.branch_id FROM diagnostic_report_detail drd 
        JOIN diagnostic_report dr ON drd.diagnostic_report_id = dr.id 
        WHERE dr.branch_id = '{branch_id}'
    """,
    'diagnostic_report_detail': """
    SELECT drd.*, dr.branch_id
    FROM diagnostic_report_detail drd
    JOIN diagnostic_report dr ON drd.diagnostic_report_id = dr.id
    WHERE dr.branch_id = '{branch_id}'
""",
    'diagnostic_report_diagnostic_report_detail': """
        SELECT drdrd.*, dr.branch_id 
        FROM diagnostic_report_diagnostic_report_detail drdrd 
        JOIN diagnostic_report dr ON drdrd.diagnostic_report_entity_id = dr.id 
        WHERE dr.branch_id = '{branch_id}'
    """,
    'immunization_completion': """
        SELECT ic.*, ir.branch_id 
        FROM immunization_completion ic 
        JOIN immunization_report ir ON ic.immunization_report_id = ir.id 
        WHERE ir.branch_id = '{branch_id}'
    """,
    'immunization_recommendation': """
        SELECT ir2.*, ir.branch_id 
        FROM immunization_recommendation ir2 
        JOIN immunization_report ir ON ir2.immunization_report_id = ir.id 
        WHERE ir.branch_id = '{branch_id}'
    """,
    'immunization_report': "SELECT * FROM immunization_report WHERE branch_id = '{branch_id}'",
    'immunization_report_immunization_completion': """
        SELECT iric.*, ir.branch_id 
        FROM immunization_report_immunization_completion iric 
        JOIN immunization_report ir ON iric.immunization_report_entity_id = ir.id 
        WHERE ir.branch_id = '{branch_id}'
    """,
    'immunization_report_immunization_recommendation': """
        SELECT irir.*, ir.branch_id 
        FROM immunization_report_immunization_recommendation irir 
        JOIN immunization_report ir ON irir.immunization_report_entity_id = ir.id 
        WHERE ir.branch_id = '{branch_id}'
    """,
    'combined_immunization': """
        SELECT  ic.*, ir2.*, iric.*, irir.*
        FROM immunization_report ir
        LEFT JOIN immunization_completion ic ON ic.immunization_report_id = ir.id
        LEFT JOIN immunization_recommendation ir2 ON ir2.immunization_report_id = ir.id
        LEFT JOIN immunization_report_immunization_completion iric ON iric.immunization_report_entity_id = ir.id
        LEFT JOIN immunization_report_immunization_recommendation irir ON irir.immunization_report_entity_id = ir.id
        WHERE ir.branch_id = '{branch_id}'
    """,
    'patient_care': """
        SELECT pc.*, mh.*
        FROM patient_care pc
        JOIN medical_history mh ON pc.medical_history_id = mh.id
        WHERE mh.branch_id = '{branch_id}'
    """,
    'patient_care_consultations': """
        SELECT pcc.*, pc.branch_id 
        FROM patient_care_consultations pcc
        JOIN patient_care pc ON pcc.patient_care_entity_id = pc.id 
        WHERE pc.branch_id = '{branch_id}'
    """,
    'patient_care_consumables': """
        SELECT pcc.*, pc.branch_id 
        FROM patient_care_consumables pcc 
        JOIN patient_care pc ON pcc.patient_care_entity_id = pc.id 
        WHERE pc.branch_id = '{branch_id}'
    """,
    'patient_care_lab_tests': """
        SELECT pclt.*, pc.branch_id 
        FROM patient_care_lab_tests pclt 
        JOIN patient_care pc ON pclt.patient_care_entity_id = pc.id 
        WHERE pc.branch_id = '{branch_id}'
    """,
   'patient_care_vaccinations': """
        SELECT pcv.*, pc.branch_id
        FROM patient_care_vaccinations pcv
        JOIN patient_care pc ON pcv.patient_care_entity_id = pc.id
        WHERE pc.branch_id = '{branch_id}';
    """,
    'patient_care_vitals': """
        SELECT pcv.*, pc.branch_id 
        FROM patient_care_vitals pcv 
        JOIN patient_care pc ON pcv.patient_care_entity_id = pc.id 
        WHERE pc.branch_id = '{branch_id}'
    """,
    'medical_history': "SELECT * FROM medical_history WHERE branch_id = '{branch_id}'",
    'combined_patient_care': """
        SELECT pc.*, mh.*, pcc.*, pccu.*, pclt.*, pcv.*
        FROM patient_care pc
        JOIN medical_history mh ON pc.medical_history_id = mh.id
        LEFT JOIN patient_care_consultations pcc ON pcc.patient_care_entity_id = pc.id
        LEFT JOIN patient_care_consumables pccu ON pccu.patient_care_entity_id = pc.id
        LEFT JOIN patient_care_lab_tests pclt ON pclt.patient_care_entity_id = pc.id
        LEFT JOIN patient_care_vaccinations pcv ON pcv.patient_care_entity_id = pc.id
        WHERE mh.branch_id = '{branch_id}'
    """,
    'combined_diagnostic_report': """
        SELECT dr.*, drd.*, drdrd.*
        FROM diagnostic_report dr
        LEFT JOIN diagnostic_report_detail drd ON dr.id = drd.diagnostic_report_id
        LEFT JOIN diagnostic_report_diagnostic_report_detail drdrd ON dr.id = drdrd.diagnostic_report_entity_id
        WHERE dr.branch_id = '{branch_id}'
    """,
    'prescription': """
    SELECT * 
    FROM prescription p
    WHERE p.branch_id = '{branch_id}'
""",
'prescription_condition': """
        SELECT pc.*, p.branch_id
        FROM prescription_condition pc
        JOIN prescription p ON pc.prescription_id = p.id
        WHERE p.branch_id = '{branch_id}'
    """,
     'prescription_medication': """
        SELECT pm.*, p.branch_id
        FROM prescription_medication pm
        JOIN prescription p ON pm.prescription_id = p.id
        WHERE p.branch_id = '{branch_id}'
    """,
    'prescription_prescription_condition': """
        SELECT ppc.*, p.branch_id
        FROM prescription_prescription_condition ppc
        JOIN prescription p ON ppc.prescription_entity_id = p.id
        WHERE p.branch_id = '{branch_id}';
    """,
    'prescription_prescription_medication': """
        SELECT ppm.*, p.branch_id
        FROM prescription_prescription_medication ppm
        JOIN prescription p ON ppm.prescription_entity_id = p.id
        WHERE p.branch_id = '{branch_id}';
    """,
     'combined_prescription': """
        SELECT p.*, pc.*, pm.*, ppc.*
        FROM prescription p
        LEFT JOIN prescription_condition pc ON p.id = pc.prescription_id
        LEFT JOIN prescription_medication pm ON p.id = pm.prescription_id
        LEFT JOIN prescription_prescription_condition ppc ON p.id = ppc.prescription_entity_id
        WHERE p.branch_id = '{branch_id}'
    """,
    'consultation': """
    SELECT c.*, pc.branch_id
    FROM consultation c
    JOIN patient_care pc ON c.patient_care_id = pc.id
    WHERE pc.branch_id = '{branch_id}'
""",
'consumables': """
    SELECT c.*, pc.branch_id
    FROM consumables c
    JOIN patient_care pc ON c.patient_care_id = pc.id
    WHERE pc.branch_id = '{branch_id}'
""",
'vital_info': """
    SELECT vi.*, pc.branch_id
    FROM vital_info vi
    JOIN patient_care pc ON vi.patient_care_id = pc.id
    WHERE pc.branch_id = '{branch_id}'
""",
'vaccination': """
    SELECT v.*, pc.branch_id
    FROM vaccination v
    JOIN patient_care pc ON v.patient_care_id = pc.id
    WHERE pc.branch_id = '{branch_id}'
""",
'vital_detail': """
    SELECT * FROM vital_detail vd WHERE branch_id = '{branch_id}'
""",
'patient_profile': """
    SELECT * FROM patient_profile pp WHERE branch_id = '{branch_id}'
""",
'patient_queue': """
    SELECT * FROM patient_queue pq WHERE branch_id = '{branch_id}'
""",
'patient_visit': """
    SELECT * FROM patient_visit pv WHERE branch_id = '{branch_id}'
""",
'op_consultation': """
    SELECT * FROM op_consultation oc WHERE branch_id = '{branch_id}'
""",
'medical_history': """
    SELECT * FROM medical_history mh WHERE branch_id = '{branch_id}'
""",
'consent_request': """
    SELECT * FROM consent_request cr WHERE branch_id = '{branch_id}'
""",
'consolidated_report': """
    SELECT * FROM consolidated_report cr WHERE branch_id = '{branch_id}'
""",
'discover_and_link': """
    SELECT * FROM discover_and_link dal WHERE branch_id = '{branch_id}'
""",
'health_professional': """
    SELECT * FROM health_professional hp WHERE branch_id = '{branch_id}'
""",
'hip_data_push_notification': """
    SELECT * FROM hip_data_push_notification hdpn WHERE branch_id = '{branch_id}'
""",
'hip_data_push_request': """
    SELECT * FROM hip_data_push_request hdpr WHERE branch_id = '{branch_id}'
""",



    'combined_facility': """
        SELECT f.*, fb.*, fs2.*
        FROM facility f
        LEFT JOIN facility_branch fb ON f.facility_id = fb.facility_id
        LEFT JOIN facility_staff fs2 ON f.facility_id = fs2.facility_id
        WHERE f.facility_id = '{facility_id}'
    """
}




@app.get("/download-csv")
async def download_csv(table_name: str, branch_id: str = None):
    if table_name not in TABLE_QUERIES:
        return Response(content=f"Table '{table_name}' not found", status_code=404)

    # Fetch the facility_id if the table is facility-related and branch_id is provided
    if table_name.startswith("combined_facility"):
        facility_id = get_facility_id_from_branch_id(branch_id)
        if not facility_id:
            return Response(content="Facility ID not found for the provided branch ID", status_code=404)
        query = TABLE_QUERIES[table_name].format(facility_id=facility_id)
    else:
        query = TABLE_QUERIES[table_name].format(branch_id=branch_id)

    # Fetch data and headers from the database
    data, headers = fetch_query_data(query)

    # Create a temporary CSV file
    csv_filename = f"{table_name}_report.csv"
    create_csv(data, headers, csv_filename)

    # Create an S3 folder name based on branch_id
    s3_folder = f"branch_id_{branch_id}"

    # Upload the CSV to S3
    s3_url = upload_to_s3(csv_filename, s3_folder)

    if "http" not in s3_url:
        return Response(content=s3_url, status_code=500)

    download_path = f"downloads/{csv_filename}" 
    download_from_s3(s3_url, download_path)

    return {"message": "CSV uploaded and downloaded successfully", "url": s3_url, "local_file": download_path}


@app.on_event("shutdown")
def shutdown_event():
    cur.close()
    conn.close()