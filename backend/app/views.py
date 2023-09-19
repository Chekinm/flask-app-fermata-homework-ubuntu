from app import app
from flask import request, jsonify
from markupsafe import escape
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId
from werkzeug.exceptions import HTTPException
import json
from utils.utils import sanitize_json
from models.models import images_collection, groups_collection
from config.config import (VALID_STATUSES, STATISTIC_NUMBER_OF_DAYS)


@app.route('/groups', methods=['GET'])
def get_groups_with_images():
    """
    Endpoint for retrieving a list of groups with associated images.

    This endpoint performs the following actions:
    1. Joins the 'groups' collection with the 'images' collection based on the
      'group_id' field.
    2. Sorts and filters the list of images, if necessary.
    3. Groups the images by their associated group and counts them.
    4. Returns a JSON response with the grouped data.

    Args:
        None

    Returns:
        A JSON response containing a list of groups with associated
        images and counts.
        If a 'status' query parameter is provided and is a valid status,
        the response will
        only include images with the specified status.
        If the 'status' parameter is invalid,
        a 400 Bad Request response is returned.

    HTTP Methods:
        GET

    Route:
        /groups

    Example Usage:
        GET /groups?status=approved

    Response:
        [
            {
                "_id": ObjectId("5f76b5c5a548ebe57f213b3a"),
                "name": "Group 1",
                "images": [
                    {
                        "_id": ObjectId("5f76b5c5a548ebe57f213b3b"),
                        "name": "Image 1",
                        "status": "approved",
                        "created_at": "2023-09-18T12:00:00Z"
                    },
                    {
                        "_id": ObjectId("5f76b5c5a548ebe57f213b3c"),
                        "name": "Image 2",
                        "status": "approved",
                        "created_at": "2023-09-18T13:00:00Z"
                    }
                ],
                "count": 2
            },
            {
                "_id": ObjectId("5f76b5c5a548ebe57f213b3d"),
                "name": "Group 2",
                "images": [
                    {
                        "_id": ObjectId("5f76b5c5a548ebe57f213b3e"),
                        "name": "Image 3",
                        "status": "approved",
                        "created_at": "2023-09-18T14:00:00Z"
                    }
                ],
                "count": 1
            }
        ]

    """

    status_filter = request.args.get('status')

    pipeline = [
        # 1 stage join collections by group_id field
        {
            '$lookup': {
                'from': 'images',
                'localField': '_id',
                'foreignField': 'group_id',
                'as': 'images'
            }
        },
        {
            # 2d stage
            # we need to destruct list of images to sort and filter (if needed)
            '$unwind': '$images'
        },
        {
            # 3d stage
            # sort by creation date
            '$sort': {
                'images.created_at': 1
            }

        },
        {
            # 4th stage group images back by group id
            # add count field and get back name of the group filed
            '$group': {
                '_id': '$_id',
                'name': {'$first': '$name'},
                'images': {'$push': '$images'},
                'count':  {'$sum': 1}
            }
        },
    ]

    if status_filter and escape(status_filter) in VALID_STATUSES:
        pipeline.insert(2, {'$match': {'images.status': status_filter}})
    elif status_filter:
        return jsonify({
            "code": 400,
            "name": "Invalid status",
            "description": (f"Valid statuses are - {VALID_STATUSES}"),
            }), 400

    groups = sanitize_json(list(groups_collection.aggregate(pipeline)))

    return jsonify(groups), 200


@app.route('/images/<image_id>', methods=['PUT'])
def update_image_status(image_id):
    """
    Endpoint to change the status of an image by its unique identifier.

    This endpoint allows you to update the status of an image
    identified by its 'image_id'.
    The image status is modified based on the
    data provided in the request JSON.

    Args:
        image_id (str): The unique identifier of the
        image (in ObjectId format).

    HTTP Methods:
        PUT

    Route:
        /images/<image_id>

    Request JSON:
        {
            "status": "new_status"
        }

    Returns:
        A JSON response indicating the result of the status update:
        - If the 'image_id' is in an invalid format, a 400 Bad Request
        response is returned.
        - If the 'status' provided is not a valid status, a 400 Bad
        Request response is returned.
        - If the status is successfully updated, a 200 OK response with a
        success message is returned.
        - If the specified image ID is not found in the database, a 400 Bad
        Request response is returned.
        - If an exception occurs during the database update, a 500 Internal
        Server Error response
        with an error description is returned.

    Example Usage:
        PUT /images/5f76b5c5a548ebe57f213b3a

    Request JSON:
        {
            "status": "approved"
        }

    Response (Success):
        {
            "message": "Image status updated"
        }

    Response (Invalid ObjectId):
        {
            "code": 400,
            "name": "Invalid ObjectId",
            "description": "Object ID is in the wrong format"
        }

    Response (Invalid Status):
        {
            "code": 400,
            "name": "Invalid status",
            "description": "Valid statuses are -
                    ['new', 'review', 'accepted', 'deleted']"
        }

    Response (Image Not Found):
        {
            "code": 400,
            "name": "Image not found",
            "description": "Specified ID was not found in the database"
        }

    Response (Database Exception):
        {
            "code": 500,
            "name": "MongoDB exception occurred",
            "description": "An error occurred while updating the image status"
        }
    """
    try:
        image_id = ObjectId(image_id)
    except InvalidId as err:
        # object id is in wrong format
        return jsonify({
            "code": 400,
            "name": "Invalid ObjectId",
            "description": str(err),
        }), 400

    data = request.get_json()
    new_status = data.get('status')
    if new_status not in VALID_STATUSES:
        return jsonify({
            "code": 400,
            "name": "Invalid status",
            "description": (f"Valid statuses are - {VALID_STATUSES}"),
            }), 400

    try:
        result = images_collection.update_one({'_id': image_id},
                                              {'$set': {'status': new_status}})
        if result.modified_count:
            return jsonify({
                'message': 'Image status updated'
                }), 200
        elif result.matched_count:
            return jsonify({
                'message': 'Requested status is the same as current',
                }), 200
        else:
            return jsonify({
                "code": 400,
                "name": "Image not found",
                "description": "Specified ID was not found in database",
                }), 400

    except Exception as err:
        return jsonify({
                "code": 500,
                "name": "MongoDB exeption occured",
                "description": str(err),
            }), 500


@app.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Endpoint to retrieve statistics for images created in the last 30 days.

    This endpoint calculates statistics based on images'
    creation dates within the last 30 days.
    It counts images grouped by their 'status' field and returns
    the counts as a JSON response.

    Args:
        None

    HTTP Methods:
        GET

    Route:
        /statistics

    Returns:
        A JSON response containing statistics
        for images created in the last 30 days. The statistics are grouped
        by 'status'and include the count of images for each status.

    Example Usage:
        GET /statistics

    Response:
        {
            "approved": 12,
            "rejected": 5,
            "pending": 8
        }

    Notes:
        - The endpoint uses a default period of the last 30 days
        to calculate statistics.
        - Images outside this time frame are excluded from the statistics.
    """
    # days = request.args.get('days')
    # try:
    #    days = int(days)
    # except ValueError:
    #     return jsonify({
    #         "code": 400,
    #         "name": "wrong filter",
    #         "description": "filter must be a number of days",
    #         }), 400
    # days = days if days else STATISTIC_NUMBER_OF_DAYS
    days = STATISTIC_NUMBER_OF_DAYS
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    print(start_date)
    pipeline = [
        {
            '$match': {
                'created_at': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }
        }
    ]

    items = images_collection.aggregate(pipeline)
    statistics = sanitize_json({item['_id']: item['count'] for item in items})
    return jsonify(statistics), 200


@app.errorhandler(HTTPException)
def handle_exception(e):
    """
    Error handler for converting HTTP exceptions into JSON responses.

    This error handler is used to intercept HTTP exceptions
    that occur during request processing.
    It transforms these exceptions into JSON
    responses containing error information.

    Args:
        e (HTTPException): The HTTP exception raised during request processing.

    Returns:
        A JSON response representing the error information:
        {
            "code": <HTTP status code>,
            "name": "<HTTP status name>",
            "description": "<Error description>"
        }

    Example Usage:
        This error handler is automatically invoked when an HTTP
        exception occurs within the application.
        It ensures that error responses are in JSON format rather than HTML.

    Notes:
        - The function retrieves the HTTP status code, status name,
        and description from the exception.
        - It sets the response's content type to "application/json"
        and returns the JSON response.

    """
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response, e.code
