import logging
import os
import random
from datetime import datetime, timedelta

import azure.functions as func
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions
)

app = func.FunctionApp()

@app.route(route="random-photo")
def random_photo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger: GetRandomPhoto")

    try:
        conn_str = os.getenv("PHOTO_STORAGE_CONNECTION")
        container_name = os.getenv("PHOTO_CONTAINER", "photos")
        account_name = os.getenv("STORAGE_ACCOUNT_NAME")
        account_key = os.getenv("STORAGE_ACCOUNT_KEY")

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

        # if account creds are provided, generate SAS
        if account_name and account_key:
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=chosen,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(minutes=15)
            )
            url = f"{blob_client.url}?{sas_token}"
        else:
            # public container case
            url = blob_client.url

        # redirect
        return func.HttpResponse(
            status_code=302,
            headers={"Location": url}
        )

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse("Internal error", status_code=500)