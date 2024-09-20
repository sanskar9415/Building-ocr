import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError
from fastapi.middleware.cors import CORSMiddleware
import time
from transformers import pipeline
import openai

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

app = FastAPI()

S3_BUCKET = "ocr-swingbell"
S3_REGION = "ap-southeast-2"

s3_client = boto3.client("s3", region_name=S3_REGION)
textract_client = boto3.client('textract', region_name=S3_REGION)

openai.api_key = 'WRITE THE OPEN AI KEY HERE'

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.info("Application startup")

@app.get("/")
async def read_root():
    logging.info("Root endpoint accessed")
    return {"message": "Welcome to the file upload API"}

@app.post("/upload-text")
async def upload_text(file: UploadFile = File(...)):
    try:
        logging.info(f"File received for text extraction: {file.filename}, Content type: {file.content_type}")
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={"ContentType": file.content_type},
        )
        logging.info(f"File uploaded to S3 bucket: {S3_BUCKET}, Filename: {file.filename}")
        textract_response = textract_client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': S3_BUCKET,
                    'Name': file.filename
                }
            }
        )
        job_id = textract_response['JobId']
        logging.info(f"Started Textract job for text detection. Job ID: {job_id}")
        status = None
        while status != 'SUCCEEDED':
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            logging.info(f"Textract job status: {status}")
            time.sleep(5)
        extracted_text = ''
        total_confidence = 0
        confidence_count = 0
        for result_page in response['Blocks']:
            if result_page['BlockType'] == 'LINE':
                extracted_text += result_page['Text'] + '\n'
                total_confidence += result_page['Confidence']
                confidence_count += 1
        average_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
        logging.info(f"Text extracted successfully with average confidence: {average_confidence}")
        return {
            "message": "File uploaded and text extracted successfully",
            "extracted_text": extracted_text,
            "average_confidence": average_confidence
        }
    except NoCredentialsError:
        logging.error("AWS credentials not found")
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        logging.error(f"Error during file upload or text extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file or extract text: {str(e)}")

@app.post("/upload-form")
async def upload_form(file: UploadFile = File(...)):
    try:
        logging.info(f"File received for form extraction: {file.filename}, Content type: {file.content_type}")
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={"ContentType": file.content_type},
        )
        logging.info(f"File uploaded to S3 bucket: {S3_BUCKET}, Filename: {file.filename}")
        textract_response = textract_client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': S3_BUCKET,
                    'Name': file.filename
                }
            },
            FeatureTypes=["FORMS"]
        )
        job_id = textract_response['JobId']
        logging.info(f"Started Textract job for form extraction. Job ID: {job_id}")
        status = None
        while status != 'SUCCEEDED':
            response = textract_client.get_document_analysis(JobId=job_id)
            status = response['JobStatus']
            logging.info(f"Textract job status: {status}")
            time.sleep(5)
        extracted_key_values = {}
        for block in response['Blocks']:
            if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
                key_text = ''
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            child_block = next((b for b in response['Blocks'] if b['Id'] == child_id), None)
                            if child_block and 'Text' in child_block:
                                key_text += child_block['Text']
                value_text = ''
                value_block = next((b for b in response['Blocks'] if b['Id'] in block.get('Relationships', [])[0].get('Ids', [])), None)
                if value_block:
                    for relationship in value_block.get('Relationships', []):
                        if relationship['Type'] == 'CHILD':
                            for child_id in relationship['Ids']:
                                child_block = next((b for b in response['Blocks'] if b['Id'] == child_id), None)
                                if child_block and 'Text' in child_block:
                                    value_text += child_block['Text']
                if key_text and value_text:
                    extracted_key_values[key_text] = value_text
        logging.info(f"Form extracted successfully with key-value pairs: {extracted_key_values}")
        return {
            "message": "File uploaded and form data extracted successfully",
            "form_data": extracted_key_values
        }
    except NoCredentialsError:
        logging.error("AWS credentials not found")
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        logging.error(f"Error during file upload or form extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file or extract form data: {str(e)}")

@app.post("/extract-info")
async def extract_info(file: UploadFile = File(...)):
    try:
        logging.info(f"File received for AI-based processing: {file.filename}, Content type: {file.content_type}")
        s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET,  
            file.filename,  
            ExtraArgs={"ContentType": file.content_type},
        )
        logging.info(f"File uploaded to S3 bucket: {S3_BUCKET}, Filename: {file.filename}")
        textract_response = textract_client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': S3_BUCKET,
                    'Name': file.filename
                }
            }
        )
        job_id = textract_response['JobId']
        logging.info(f"Started Textract job for text detection. Job ID: {job_id}")
        status = None
        while status != 'SUCCEEDED':
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            logging.info(f"Textract job status: {status}")
            time.sleep(5)
        extracted_text = ''
        for result_page in response['Blocks']:
            if result_page['BlockType'] == 'LINE':
                extracted_text += result_page['Text'] + '\n'
        logging.info("Text extracted, sending to OpenAI for summarization and analysis.")
        prompt = f"Summarize the following text and identify any medicines mentioned:\n\n{extracted_text}"
        openai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        summary_and_medicines = openai_response['choices'][0]['message']['content'].strip()
        logging.info("OpenAI processing completed.")
        return {
            "message": "File processed and analyzed successfully",
            "summary_and_medicines": summary_and_medicines
        }
    except NoCredentialsError:
        logging.error("AWS credentials not found")
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        logging.error(f"Error during file processing or analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process or analyze file: {str(e)}")
