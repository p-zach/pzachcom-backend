import logging
import os
import requests
import random
import datetime
import io
import requests
from PIL import Image
import http

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="photo-of-the-day", methods=["GET"])
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    width = req.params.get('max_w', None)
    height = req.params.get('max_h', None)

    if width is not None and height is not None:
        return func.HttpResponse(
            "Cannot specify both max_w and max_h",
            status_code=http.HTTPStatus.BAD_REQUEST
        )

    try:
        blob_url = os.getenv("PHOTO_BLOB_URL")
        photo_json_url = f"{blob_url}/photos.json"

        response = requests.get(photo_json_url)
        response.raise_for_status()
        
        data = response.json()
        
        # Ensure the JSON has the expected structure
        photos = data.get("photos", [])
        if not photos:
            raise ValueError("No photos found in JSON.")

        # Get a unique seed based on today's date
        today = datetime.date.today()
        seed = today.year * 366 + today.month * 31 + today.day
        random_today = random.Random(seed)

        # Choose a photo
        chosen = random_today.choice(photos)
        photo_url = f"{blob_url}/{chosen}"

        response = requests.get(photo_url)

        if response.status_code != 200:
            return func.HttpResponse(
                "Image not found", 
                status_code=http.HTTPStatus.NOT_FOUND
            )

        img = Image.open(io.BytesIO(response.content))

        # Resize if requested, while maintaining aspect ratio
        if width or height:
            img.thumbnail((
                width or img.width * height / img.height, 
                height or img.height * width / img.width
            ))

        # Encode to buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        # Return image directly
        return func.HttpResponse(
            buf.getvalue(),
            mimetype="image/jpeg"
        )
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)