import logging
import os
import random

import azure.functions as func
from azure.storage.blob import (
    BlobServiceClient,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="random-photo", methods=["GET"])
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger: GetRandomPhoto")

    try:
        conn_str = os.getenv("PHOTO_STORAGE_CONNECTION")
        container_name = os.getenv("PHOTO_CONTAINER", "photos")

        if not conn_str:
            return func.HttpResponse(
                "PHOTO_STORAGE_CONNECTION not configured",
                status_code=500
            )

        # connect to storage
        blob_service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service_client.get_container_client(container_name)

        # list blobs
        blob_list = [b.name for b in container_client.list_blobs()]
        if not blob_list:
            return func.HttpResponse("No photos found", status_code=404)

        chosen = random.choice(blob_list)
        blob_client = container_client.get_blob_client(chosen)

        # add a random query param to break caching
        url_with_nonce = f"{blob_client.url}&_={random.randint(0, 999999)}"

        # redirect
        return func.HttpResponse(
            status_code=302,
            headers={
                "Location": url_with_nonce,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Internal error: {e}", status_code=500)