from flask import Flask, request, jsonify
from flask_cors import CORS
import os
# from models import User, Food

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"]) # ?

# get 
@app.route("/places", methods=["GET"])
def get_places():
    # get required params


    


# # need image, user, then adds food based on image
# @app.route("/detect-food", methods=["POST"])
# def detect_food():
#     # --- USER ID REQUIRED ---
#     user_id = request.form.get("user_id")
#     if not user_id:
#         return jsonify({"error": "user_id is required"}), 400

#     # UUID lookup
#     try:
#         user_uuid = uuid.UUID(user_id)
#     except ValueError:
#         return jsonify({"error": "Invalid user_id format"}), 400

#     user = User.objects(id=user_uuid).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     # --- FILE HANDLING ---
#     if "file" not in request.files:
#         return jsonify({"result": "No file uploaded"}), 400

#     file = request.files["file"]
#     os.makedirs("images", exist_ok=True)
#     file_path = os.path.join("images", file.filename)
#     file.save(file_path)

#     # --- RUN IMAGE DETECTION ---
#     items = recognize_items(file_path)
#     if not items.items:
#         return jsonify({"result": "Food could not be detected."})

#     saved_items = []  # IMPORTANT

#     for f in items.items:
#         name = f.name or "Unknown"
#         quantity = (f.quantity or "medium").lower()
#         if quantity not in ("small", "medium", "large"):
#             quantity = "medium"

#         # --- EXPIRATION DATE ---
#         exp_info = get_food_expiration(name)
#         expiration_date = exp_info.get("expiration_date")

#         # fallback if nothing returned
#         if not expiration_date:
#             expiration_date = fallback_expiration(name)

#         # --- SAVE TO DATABASE ---
#         food = Food(
#             user=user,
#             name=name,
#             quantity=quantity,
#             expiration_date=expiration_date
#         )
#         food.save()

#         saved_items.append({
#             "name": name,
#             "quantity": quantity,
#             "expiration_date": expiration_date.isoformat(),
#             "food_id": str(food.id)
#         })

#     return jsonify({
#         "result": "success",
#         "items_saved": saved_items
#     })

if __name__ == "__main__":
    app.run(debug=True, port=8000)