from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Query, Depends, HTTPException, status
import os  # Import the 'os' module
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import databases
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from databases import Database
from sqlalchemy.sql import select
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel



app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/pdftoword")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}


# @app.post("/uploadfile/")
# async def create_upload_file(file: UploadFile):
#     # return {"filename": file.filename}
#     return file
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# @app.post("/uploadfile/")
# async def create_upload_file(file: UploadFile):
#     # Save the uploaded file to the local directory
#     file_path = os.path.join(upload_dir, file.filename)
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())

    
    # return {"filename": file.filename, "file_path": file_path}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    # Save the uploaded file to the local directory
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    return {"filename": file.filename, "file_path": file_path}


@app.get("/convert-to-ocr/")
async def convert_to_ocr(filename: str = Query(..., description="Name of the PDF file to OCR")):
    pdf_path = os.path.join(upload_dir, filename)
    if not os.path.exists(pdf_path):
        return JSONResponse(content={"error": f"File '{filename}' not found"}, status_code=404)
    print("file found", pdf_path)
    # Convert PDF to a list of images
    images = convert_from_path(pdf_path)

    ocr_text = ""
    for image in images:
        # Perform OCR on each image
        ocr_text += pytesseract.image_to_string(image)

    return JSONResponse(content={"ocr_text": ocr_text})


# Pydantic model for response
class OCRResponseModel(BaseModel):
    id: int
    pdf_filename: str
    ocr_text: str

# # FastAPI route to get all OCR requests and responses
# @app.get("/get-all-ocr-requests/", response_model=List[OCRResponseModel])
# async def get_all_ocr_requests():
#     query = select([requests])
#     results = await database.fetch_all(query)
#     return results


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": True,
    },
}

def fake_hash_password(password: str):
    return "fakehashed" + password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def fake_decode_token(token):
    # This doesn't provide any security at all
    # Check the next version
    user = get_user(fake_users_db, token)
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


