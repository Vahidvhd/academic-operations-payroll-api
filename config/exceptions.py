from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    original_data = response.data

    if isinstance(original_data, dict):
        if "detail" in original_data and len(original_data) == 1:
            error_message = original_data["detail"]
        else:
            error_message = original_data
    else:
        error_message = original_data

    error_code = response.status_code

    response.data = {
        "error_code": error_code,
        "error_message": error_message,
    }
    
    return response