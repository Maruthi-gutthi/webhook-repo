from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://maruthi:maruthi@githubrepo.wy5fxew.mongodb.net/?retryWrites=true&w=majority&appName=Githubrepo")
db = client['github_events']
collection = db['events']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/feed')
def feed():
    data = list(collection.find({}, {'_id': 0}))
    for item in data:
        item['timestamp'] = item['timestamp'].strftime('%d %b %Y - %I:%M %p UTC')
    return jsonify(data)

@app.route('/webhook', methods=['POST'])
def webhook():
    if not request.is_json:
        return jsonify({'error': 'Invalid content type'}), 403

    payload = request.get_json()
    event_type = request.headers.get('X-GitHub-Event')
    print("Webhook received")
    print("Event type:", event_type)
    print("Payload:", payload)
    data = {}

    if event_type == 'push':
        data = {
            'author': payload['pusher']['name'],
            'to_branch': payload['ref'].split('/')[-1],
            'timestamp': datetime.utcnow(),
            'type': 'push'
        }

    elif event_type == 'pull_request':
        pr = payload['pull_request']
        data = {
            'author': pr['user']['login'],
            'from_branch': pr['head']['ref'],
            'to_branch': pr['base']['ref'],
            'timestamp': datetime.utcnow(),
            'type': 'pull_request'
        }

        # Detect if PR was merged
        if payload['action'] == 'closed' and pr['merged']:
            data['type'] = 'merge'

    if data:
        collection.insert_one(data)

    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(debug=True)
