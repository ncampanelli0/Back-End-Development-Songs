from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def get_health():
    return {"status": "OK"}, 200

@app.route("/count", methods=["GET"])
def count():
    """return length of data"""
    count = client.songs.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def songs():
    songs = client.songs.songs.find({})
    return {"songs": parse_json(list(songs))}, 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song = client.songs.songs.find_one({"id": id})
    if song:
        return json_util.dumps(song), 200
    return {"message": f"song with id {id} not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    new_song = request.json
    if not new_song:
        return {"message": "Invalid input parameter"}, 422
    if client.songs.songs.find_one({"id": new_song['id']}):
        return {"Message": f"song with id {new_song['id']} already present"}, 302
    insert_id: InsertOneResult = client.songs.songs.insert_one(new_song)
    return {"inserted id": json_util.dumps(insert_id.inserted_id)}, 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song_in = request.json
    if not song_in:
        return {"message": "Invalid input parameter"}, 422
    song = client.songs.songs.find_one({"id": id})
    if not song:
        return {"message": "song not found"}, 404
    result = client.songs.songs.update_one({"id": id}, {"$set": song_in})
    if result.modified_count == 0:
        return {"message": "song found, but nothing updated"}, 200
    else:
        return json_util.dumps(db.songs.find_one({"id": id})), 201

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    result = client.songs.songs.delete_one({"id": id})
    if result.deleted_count == 0:
        return {"message": "song not found"}, 404
    return "", 204

