from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Store user mappings (in-memory for simplicity, use a DB for production)
user_tunnels = {}


@app.route('/register', methods=['POST'])
def register_tunnel():
    """Register user's ngrok tunnel URL."""
    data = request.json
    user_id = data.get('user_id')
    tunnel_url = data.get('tunnel_url')

    if not user_id or not tunnel_url:
        return jsonify({'error': 'user_id and tunnel_url are required'}), 400

    # Store the user's tunnel URL
    user_tunnels[user_id] = tunnel_url
    return jsonify({'message': f'User {user_id} tunnel registered successfully'}), 200


@app.route('/<user_id>/files/structure', methods=['GET'])
def forward_file_structure(user_id):
    """Forward the request to the user's local API."""
    tunnel_url = user_tunnels.get(user_id)
    if not tunnel_url:
        return jsonify({'error': 'User not registered or tunnel not available'}), 404

    # Forward request to user's API
    try:
        response = requests.get(f'{tunnel_url}/files/structure')
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to reach user API: {str(e)}'}), 500


@app.route('/<user_id>/files/content', methods=['POST'])
def forward_file_content(user_id):
    """Forward the request to the user's local API."""
    tunnel_url = user_tunnels.get(user_id)
    if not tunnel_url:
        return jsonify({'error': 'User not registered or tunnel not available'}), 404

    # Forward request to user's API
    try:
        response = requests.post(
            f'{tunnel_url}/files/content', json=request.json)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to reach user API: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
