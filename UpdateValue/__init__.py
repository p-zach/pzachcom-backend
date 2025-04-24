import azure.functions as func
from azure.data.tables import TableServiceClient
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        table_name = "VisitorTable"
        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        service = TableServiceClient.from_connection_string(conn_str)
        table_client = service.get_table_client(table_name)

        data = req.get_json()
        partition_key = data.get("partitionKey")
        row_key = data.get("rowKey")
        new_value = data.get("value")

        entity = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "VALUE": new_value
        }

        table_client.upsert_entity(entity)
        return func.HttpResponse("Value updated", status_code=200)

    except Exception as e:
        logging.error("An error occurred.", exc_info=True)
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
