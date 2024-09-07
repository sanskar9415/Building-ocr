from fastapi import FastAPI, UploadFile, File, HTTPException
import boto3
from botocore.exceptions import NoCredentialsError

app = FastAPI()

S3_BUCKET = "ocr-swingbell"
S3_REGION = "ap-southeast-2"



s3_client = boto3.client("s3", region_name=S3_REGION)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the file upload API"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET,  
            file.filename,  
            ExtraArgs={"ContentType": file.content_type},
        )
        return {"message": "File uploaded successfully", "file_name": file.filename}
    except NoCredentialsError:
        raise HTTPException(status_code=401, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
