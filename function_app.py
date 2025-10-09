import logging
import os
import requests
import random
import datetime

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="photo-of-the-day", methods=["GET"])
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger: photo-of-the-day")

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

        chosen = random_today.choice(photos)
        photo_url = f"{blob_url}/{chosen}"

        # Redirect
        return func.HttpResponse(
            status_code=302,
            headers={"Location": photo_url}
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)