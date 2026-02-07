from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
import os


app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["qwermapdb"]          # your database name
collection = db["qwermap"]     # your collection name


@app.route("/add_user", methods=["POST"])
def add_user():
    data = request.json   # expects JSON input

    collection.insert_one(data)
    return jsonify({"message": "User added!"})

if __name__ == "__main__":
    app.run()