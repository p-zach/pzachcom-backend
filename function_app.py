import logging
import os
import requests
import random
import datetime
import io
import requests
from PIL import Image
import http
import json

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="photo-of-the-day", methods=["GET"])
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    max_width = req.params.get('max_w', None)
    max_height = req.params.get('max_h', None)

    try:
        blob_url, photos = get_photo_blob_json()

        # Get a unique seed based on today's date
        today = datetime.date.today()
        seed = today.year * 366 + today.month * 31 + today.day
        random_today = random.Random(seed)

        # Choose a photo
        chosen = random_today.choice(photos)["name"]
        photo_url = f"{blob_url}/{chosen}"

        response = requests.get(photo_url)

        if response.status_code != 200:
            return func.HttpResponse(
                "Image not found", 
                status_code=http.HTTPStatus.NOT_FOUND
            )

        img = Image.open(io.BytesIO(response.content))

        # Resize if requested, while maintaining aspect ratio
        if max_width or max_height:
            # Set unset values to img value since img.thumbnail automatically preserves aspect ratio
            if max_width is None:
                max_width = img.width
            if max_height is None:
                max_height = img.height
                
            img.thumbnail((int(max_width), int(max_height)))

        # Encode to buffer
        buf = io.BytesIO()
        img.save(buf, format="JPEG", exif=img.info.get("exif"))
        buf.seek(0)

        # Return image directly
        return func.HttpResponse(
            buf.getvalue(),
            mimetype="image/jpeg"
        )
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)

@app.route(route="gallery-list", methods=["GET"])
def gallery_list(req: func.HttpRequest) -> func.HttpResponse:
    random_order = req.params.get('random_order', False)
    max_photos = req.params.get('max_photos', 0)

    try:
        _, photos = get_photo_blob_json()

        if random_order:
            random.shuffle(photos)

        if int(max_photos) > 0 and int(max_photos) < len(photos):
            photos = photos[:int(max_photos)]

        return func.HttpResponse(json.dumps(photos))
    except ValueError as e:
        return func.HttpResponse(f"Bad request: {e}", status_code=400)
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)

def get_photo_blob_json() -> tuple:
    """Gets the URL of the blob containing the photos and the list of photos in
    the blob. A photo in the list consists of a JSON object with name, src, 
    width, height, and alt fields.

    Raises:
        ValueError: If there are no photos in the JSON.

    Returns:
        tuple: (the blob URL, the list of photos)
    """
    blob_url = os.getenv("PHOTO_BLOB_URL")
    photo_json_url = f"{blob_url}/photos.json"

    response = requests.get(photo_json_url)
    response.raise_for_status()
    
    data = response.json()
    
    # Ensure the JSON has the expected structure
    photos = data.get("photos", [])
    if not photos:
        raise ValueError("No photos found in JSON.")

    for photo in photos:
        photo["src"] = f"{blob_url}/{photo["name"]}"

    return blob_url, photos