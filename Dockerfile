FROM python:3.10-alpine3.18

COPY requirements.txt .

# Install Tesseract OCR and any necessary dependencies
RUN apk add --no-cache tesseract-ocr
RUN apk add --no-cache tesseract-ocr-data-eng
RUN apk add --no-cache poppler-utils

# Set an environment variable for pytesseract to locate the Tesseract binary
ENV TESSDATA_PREFIX=/usr/share/tessdata
# Set environment variable for PyMuPDF
ENV PYMUPDF_PYTHON /usr/bin

RUN pip install --upgrade -r requirements.txt

# Set an environment variable for pytesseract to locate the Tesseract binary
ENV TESSDATA_PREFIX=/usr/share/tessdata

# Expose the port your FastAPI application will listen on (if necessary)
EXPOSE 8000

# Start your FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]