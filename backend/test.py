from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from mongoengine import connect, Document, StringField


# app = Flask(__name__)

# MONGO_URI = os.getenv("MONGO_URI")
# client = MongoClient(MONGO_URI)

# db = client["qwermapdb"]          # your database name
# collection = db["qwermap"]     # your collection name


# @app.route("/add_user", methods=["POST"])
# def add_user():
#     data = request.json   # expects JSON input

#     collection.insert_one(data)
#     return jsonify({"message": "User added!"})

# if __name__ == "__main__":
#     app.run()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB", "qwermapdb")

# Connect MongoEngine
connect(db=MONGO_DB, host=MONGO_URI)
print("Connected to MongoDB!")