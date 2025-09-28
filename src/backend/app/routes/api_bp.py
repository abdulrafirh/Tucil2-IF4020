from flask import Blueprint, jsonify

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/data', methods=['GET'])
def get_data():
    """
    A simple example API endpoint that returns JSON data.
    """
    return jsonify({
        "message": "Hello from the Flask backend!"
    })
