from login import login, send_mfa_email, pwd_context
import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends,  Body, Response, status, Cookie
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db
import models, schemas
from contextlib import asynccontextmanager
import uuid
import aioboto3 
from botocore.config import Config
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse



login_sessions= {}
mfa_sessions = {}

models.Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Server starting...")
    
    async for s3 in get_s3_wrapper():
        try:
            # Check/Create Bucket Only
            try:
                await s3.head_bucket(Bucket=BUCKET_NAME)
            except:
                print(f"Creating bucket {BUCKET_NAME}...")
                await s3.create_bucket(Bucket=BUCKET_NAME)
                
            print(f"✅ MinIO Connected. Bucket: {BUCKET_NAME}")

        except Exception as e:
            print(f"❌ Critical MinIO Error: {e}")

    yield
    print("🛑 Server shutting down...")




app = FastAPI(lifespan=lifespan)
origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Configuration
S3_ENDPOINT = "http://127.0.0.1:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "secure-data"

# S3 Client Helper
# Updated S3 Client Helper
async def get_s3_wrapper():
    session = aioboto3.Session()
    async with session.client(
        "s3", 
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        # THIS IS THE MISSING PIECE:
        config=Config(signature_version='s3v4') 
    ) as client:
        yield client


def cleanup_expired_sessions():
    now = datetime.datetime.now()
    # We create a list of keys to delete to avoid 'dictionary size changed during iteration' error
    expired_emails = [
        email for email, data in mfa_sessions.items() 
        if now > data["expires_at"]
    ]
    for email in expired_emails:
        del mfa_sessions[email]

def session_token_cleanup():
    now = datetime.datetime.now()
    expired_tokens = [
        token for token, expiry in login_sessions.items()
        if now > expiry
    ]

    for token in expired_tokens:
        del login_sessions[token]

def create_access_token(username: str):
    return f"filecrpyt-Token-{username}-{login(token_session=True)}"

@app.post("/check")
async def check(user: schemas.UserCreate, response: Response, db: Session = Depends(get_db),):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        is_match = pwd_context.verify(user.password, db_user.hashed_password)
        if is_match:
            accesstoken= create_access_token(db_user.name)
            response.set_cookie(
                key="access_token",        # The name of the cookie
                value=accesstoken,        # The actual token
                httponly=True,             # CRITICAL: Prevents XSS attacks
                secure=True,               # Set to True in production (HTTPS only)
                samesite="lax",            # Helps with CSRF (Lax or Strict)
                max_age=3600               # Expires in 1 hour
            )
            db_session = models.LoginSession(
                name=db_user.name,
                email=db_user.email,
                token= accesstoken,
                created_at = datetime.datetime.now(),
                expiry_at = datetime.datetime.now() + datetime.timedelta(minutes=60)
            )
            db.add(db_session)
            db.commit()
            db.refresh(db_session)
            login_sessions[accesstoken]= db_session.expiry_at

            return {"existence": "true","pswd_match": "true"}
        else:
            return {"existence": "true","pswd_match": "false"}
    return {"existence": "False"}

@app.post("/initiate-mfa")
async def request_mfa(user: schemas.UserCreate, background_tasks: BackgroundTasks):
    
    mfa_code,expiry_time = login(token_session=False)
    mfa_sessions[user.email] = {"code": mfa_code, "expires_at": expiry_time, "password": pwd_context.hash(user.password),"Username": user.name}
    background_tasks.add_task(cleanup_expired_sessions)
    
    try:
        send_mfa_email(user.email, mfa_code)
    except Exception:
        del mfa_sessions[user.email]
        raise HTTPException(status_code=500, detail="Mail server error")
    return {"message": "Code sent."}




@app.post("/verify-mfa")
async def verify_mfa(email: str, user_provided_code: str, response: Response, db: Session = Depends(get_db)):
    session = mfa_sessions.get(email)
    if not session:
        return {"state": "No active session found"}
    
    # Check expiry
    if datetime.datetime.now() > session["expires_at"]:
        del mfa_sessions[email]
        return {"state": "Session Ended (Timed Out)"}
    
    # Check code
    if user_provided_code == session["code"]:
        del mfa_sessions[email] # Remove immediately upon success
        new_user = models.User(
        name=session["Username"], 
        email=email, 
        hashed_password=session["password"] 
        )
        
        
        accesstoken= create_access_token(session["Username"])
        response.set_cookie(
                key="access_token",       
                value=accesstoken,      
                httponly=True,            
                secure=True,               
                samesite="lax",           
                max_age=3600              
        )
        db_session = models.LoginSession(
                name=session["Username"],
                email=email,
                token= accesstoken,
                created_at = datetime.datetime.now(),
                expiry_at = datetime.datetime.now() + datetime.timedelta(minutes=60)

        )
        
        db.add(new_user)
        db.add(db_session)
        db.commit()
        db.refresh(new_user)
        db.refresh(db_session)
        login_sessions[accesstoken]= db_session.expiry_at

        return {"state": "home.html"}
    else:
        return {"state": "Wrong KEY" }

@app.get("/startup")
async def userName(background_tasks: BackgroundTasks, access_token: str | None = Cookie(default=None),db: Session = Depends(get_db)):
   background_tasks.add_task(session_token_cleanup)

   if access_token in login_sessions.keys() :
       if login_sessions[access_token] < datetime.datetime.now() :
           del login_sessions[access_token]
           return {"status": "expired"}
       else:
            files= db.query(models.FileMetadata).all()

            return files

# 1. START UPLOAD
@app.post("/upload/start")
async def start_upload(filename: str = Body(..., embed=True), content_type: str = Body(..., embed=True)):
    async for s3 in get_s3_wrapper():
        # Ensure bucket exists
        try:
            await s3.head_bucket(Bucket=BUCKET_NAME)
        except:
            await s3.create_bucket(Bucket=BUCKET_NAME)
            
        file_uuid = str(uuid.uuid4())
        key = f"{file_uuid}.enc"
        
        # Initiate Multipart Upload on MinIO
        resp = await s3.create_multipart_upload(Bucket=BUCKET_NAME, Key=key, ContentType=content_type)
        return {"upload_id": resp["UploadId"], "key": key, "file_uuid": file_uuid}

# 2. UPLOAD CHUNK (Presigned URL)
# We generate a URL so the frontend can PUT the binary data securely
@app.post("/upload/sign-part")
async def sign_upload_part(
    key: str = Body(...),
    upload_id: str = Body(...),
    part_number: int = Body(...)
):
    async for s3 in get_s3_wrapper():
        url = await s3.generate_presigned_url(
            ClientMethod='upload_part',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': key,
                'UploadId': upload_id,
                'PartNumber': part_number
            },
            ExpiresIn=3600
        )
        return {"url": url}



@app.post("/upload/complete")
async def complete_upload(
    key: str = Body(...),
    upload_id: str = Body(...),
    parts: list = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    db: Session = Depends(get_db)
     
):
    # --- 1. NEW VALIDATION CHECK ---
    if not parts:
        raise HTTPException(status_code=400, detail="Error: The 'parts' list is empty. Chunk uploads failed.")
    
    # Check for null ETags which crash MinIO
    for p in parts:
        if not p.get('ETag'):
             raise HTTPException(status_code=400, detail=f"Error: Part {p.get('PartNumber')} has no ETag. Check CORS.")
    # -------------------------------

    async for s3 in get_s3_wrapper():
        try:
            await s3.complete_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            # Save to DB
            db_file = models.FileMetadata(
                filename=filename,
                content_type=content_type,
                access = "PRIVATE",
                file_size=0, 
                minio_key=key
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            
            return {"status": "success", "file_id": db_file.id}

        except Exception as e:
            print(f"❌ MinIO Error: {e}")
            # Return 400 so the frontend can read the error message
            raise HTTPException(status_code=400, detail=str(e))
        




@app.get("/files/{file_id}")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    # 1. Look up file in DB
    db_file = db.query(models.FileMetadata).filter(models.FileMetadata.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    # 2. Generator to stream data from MinIO
    async def s3_stream():
        async for s3 in get_s3_wrapper():
            try:
                # Get the object (stream)
                response = await s3.get_object(Bucket=BUCKET_NAME, Key=db_file.minio_key)
                # Yield chunks of data as they come in
                async for chunk in response['Body']:
                    yield chunk
            except Exception as e:
                print(f"Error streaming file: {e}")
                raise HTTPException(status_code=500, detail="Error retrieving file from storage")

    # 3. Return Streaming Response
    return StreamingResponse(
        s3_stream(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{db_file.filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition" # Allow JS to read filename
        }
    )