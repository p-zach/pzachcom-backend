import azure.functions as func
from azure.data.tables import TableServiceClient
import os
import logging

logger = logging.getLogger("azure.functions")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Function GetValue triggered")
    try:
        table_name = "VisitorTable"
        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        service = TableServiceClient.from_connection_string(conn_str)
        table_client = service.get_table_client(table_name)

        partition_key = req.params.get("partitionKey")
        row_key = req.params.get("rowKey")

        entity = table_client.get_entity(partition_key=partition_key, row_key=row_key)
        return func.HttpResponse(f"{entity['VALUE']}", status_code=200)

    except Exception as e:
        logger.error("An error occurred.", exc_info=True)
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
