from fastapi import FastAPI, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

S3_BUCKET = "ocr-swingbell"
S3_REGION = "ap-southeast-2"

s3_client = boto3.client("s3", region_name=S3_REGION)
textract_client = boto3.client('textract', region_name=S3_REGION)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the file upload API"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        print(f"File received: {file.filename}, Content type: {file.content_type}")
        # Upload the file to S3
        s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET,  
            file.filename,  
            ExtraArgs={"ContentType": file.content_type},
        )
        
        # Call Amazon Textract to analyze the document
        textract_response = textract_client.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': S3_BUCKET,
                    'Name': file.filename
                }
            }
        )

        job_id = textract_response['JobId']

        # Wait for Textract to complete processing (polling)
        status = None
        while status != 'SUCCEEDED':
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            time.sleep(5)  # Wait 5 seconds between status checks

        # Extract text from the Textract response
        extracted_text = ''
        for result_page in response['Blocks']:
            if result_page['BlockType'] == 'LINE':
                extracted_text += result_page['Text'] + '\n'

        return {"message": "File uploaded and text extracted successfully", "extracted_text": extracted_text}
    
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file or extract text: {str(e)}")
