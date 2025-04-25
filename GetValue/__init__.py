import azure.functions as func
from azure.data.tables import TableServiceClient
import os
import logging

logger = logging.getLogger("azure.functions")

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the value in the specified partition and row from the table named
    VisitorTable in the Azure DB.
    """
    logger.info("Function GetValue triggered")
    try:
        # Connect to the table
        table_name = "VisitorTable"
        conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
        service = TableServiceClient.from_connection_string(conn_str)
        table_client = service.get_table_client(table_name)

        # Find entity via keys
        partition_key = req.params.get("partitionKey")
        row_key = req.params.get("rowKey")

        # Get and return the value
        entity = table_client.get_entity(partition_key=partition_key, row_key=row_key)
        return func.HttpResponse(f"{entity['VALUE']}", status_code=200)

    except Exception as e:
        logger.error("An error occurred.", exc_info=True)
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
