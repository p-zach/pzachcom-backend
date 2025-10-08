import logging
import os
import random
import datetime

import azure.functions as func
from azure.storage.blob import (
    BlobServiceClient,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="photo-of-the-day", methods=["GET"])
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger: photo-of-the-day")

    try:
        conn_str = os.getenv("PHOTO_STORAGE_CONNECTION")
        container_name = os.getenv("PHOTO_CONTAINER", "photos")

        if not conn_str:
            return func.HttpResponse(
                "PHOTO_STORAGE_CONNECTION not configured", status_code=500
            )

        # connect to storage
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service_client.get_container_client(container_name)

        # list blobs
        blob_list = [b.name for b in container_client.list_blobs()]
        if not blob_list:
            return func.HttpResponse("No photos found", status_code=404)

        # get a unique seed based on today's date
        today = datetime.date.today()
        seed = today.year * 366 + today.month * 31 + today.day
        random_today = random.Random(seed)

        chosen = random_today.choice(blob_list)
        blob_client = container_client.get_blob_client(chosen)

        # redirect
        return func.HttpResponse(
            status_code=302,
            headers={"Location": blob_client.url}
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)