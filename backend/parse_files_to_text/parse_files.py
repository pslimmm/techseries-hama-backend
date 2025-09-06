import os
import base64
import PyPDF2
import requests
from io import BytesIO
from dotenv import load_dotenv

# exports env variables 
load_dotenv()

ocr_api_key = os.getenv("OCR_SPACE_API_KEY")
# print(ocr_api_key)
ocr_api_endpoint = "https://api.ocr.space/parse/image/"


# PyPDF2 documentation: https://pypi.org/project/PyPDF2/
# OCR.space documentation: https://ocr.space/OCRAPI

# this is if we directly parse user form data and use FastAPI's UploadFile properties
async def extract_text(file):
    file_stream = file.file
    text = ""
    # block of code to process pdf
    if file.content_type == "application/pdf":
        # returns an accessible pdf with pages that can be accessed from .page
        pdf = PyPDF2.PdfReader(file_stream)
        for pages in pdf.pages:
            # extract_text extracts text from each PAGE
            text += pages.extract_text() + "\n"

    
    # block of code to process images
    elif file.content_type.startswith("image/"):
        image_bytes = await file.read()
        text = parse_image_to_text(image_bytes, file.content_type)
    
    return text

# parse image from file stream
def parse_image_to_text(image_bytes, file_type):
    try:
        file_extension = file_type.split('/')[1].upper()

        if file_extension not in ["PDF", "GIF", "PNG", "JPG", "TIF", "BMP"]:
            if file_extension == "JPEG":
                file_extension = "JPG"
            else:
                raise ValueError("wrong file type: " + file_extension)
            
        # convert image bytes to a file object (BytesIO) then 
        # encodes it to a base64 string
        # note that we also need to add "data:image/png;base64," in front of the base64 string
        # and make sure there are no trailing spaces in the base64 string
        image_bytes = BytesIO(image_bytes)
        image_bytes.seek(0)
        file_bytes = image_bytes.read()
        base64_string = base64.b64encode(file_bytes).decode("utf-8")
        base64_string = "data:" + file_type + ";base64," + base64_string.strip()
        # print(base64_string)

        data = {
            'apikey': ocr_api_key,
            'base64Image': base64_string, 
            "language": "auto",
            "OCREngine": 2,
            "filetype": file_extension
        }
        # print()
        # print(json.dumps(data))

        # request body to OCR.space uses the data param, not json
        response = requests.post(ocr_api_endpoint, data=data)   
        result = response.json()

        # raise error if bad request
        response.raise_for_status()
        if result["IsErroredOnProcessing"]:
            raise ValueError(result["ErrorMessage"][0])

        # parsed text
        text = result["ParsedResults"][0]["ParsedText"]
        # print(text)
        return text
    except Exception as e:
        print(f"Error: {e}")
        return ""


# this is if we parse the file object retrieved from the db
# def extract_text(doc):
#     if not doc:
#         return "file not found";

#     file_stream = BytesIO(doc["content"])
    
#     if doc.content_type == "application/pdf":
#         # returns an accessible pdf with pages that can be accessed from .page
#         pdf = PyPDF2.PdfReader(file_stream)
#         text = ""
#         for pages in pdf.pages:
#             # extract_text extracts text from each PAGE
#             text += pages.extract_text() + "\n"
        
        
#         return text
#     elif doc.content_type.startswith("image/"):
#         text = parse_image_to_text(file_stream)
        # return text
