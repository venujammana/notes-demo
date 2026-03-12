import os
from flask import Flask, jsonify, request
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()
notes_collection = db.collection(u'notes')

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route("/notes", methods=["GET"])
def get_notes():
    """Retrieves all notes from Firestore."""
    notes = []
    for doc in notes_collection.stream():
        notes.append(doc.to_dict())
    return jsonify(notes)

@app.route("/notes", methods=["POST"])
def create_note():
    """Creates a new note in Firestore."""
    note = request.get_json()
    if not note or 'text' not in note:
        return jsonify({"error": "Note content is missing."}), 400
    
    # Add a new doc in collection 'notes' with a generated id
    _, doc_ref = notes_collection.add(note)
    return jsonify({"id": doc_ref.id}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
