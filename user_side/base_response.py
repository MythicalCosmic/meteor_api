from rest_framework.response import Response
from rest_framework import status as http_status

def success_response(data=None, message="Success", status=None, meta=None):
    response_data = {
        "success": True,
        "message": message,
        "data": data
    }
    
    if meta:
        response_data["meta"] = meta
    
    return Response(response_data, status=status or http_status.HTTP_200_OK)

def error_response(message="An error occurred", errors=None, status=None):
    response_data = {
        "success": False,
        "message": message
    }
    
    if errors:
        response_data["errors"] = errors
    
    return Response(response_data, status=status or http_status.HTTP_400_BAD_REQUEST)

def created_response(data=None, message="Resource created successfully", meta=None):
    return success_response(data=data, message=message, status=http_status.HTTP_201_CREATED, meta=meta)

def no_content_response(message="Operation completed successfully"):
    return Response({"success": True, "message": message}, status=http_status.HTTP_204_NO_CONTENT)

def not_found_response(message="Resource not found"):
    return error_response(message=message, status=http_status.HTTP_404_NOT_FOUND)

def unauthorized_response(message="Authentication required"):
    return error_response(message=message, status=http_status.HTTP_401_UNAUTHORIZED)

def forbidden_response(message="You don't have permission to access this resource"):
    return error_response(message=message, status=http_status.HTTP_403_FORBIDDEN)

def validation_error_response(errors, message="Validation failed"):
    return error_response(message=message, errors=errors, status=http_status.HTTP_422_UNPROCESSABLE_ENTITY)