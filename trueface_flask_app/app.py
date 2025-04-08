from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import os

app = Flask(__name__)
CORS(app)

# Ensure your OPENAI_API_KEY is set as an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    # Serve the homepage (index.html)
    return render_template('index.html')  # Ensure 'index.html' exists in your 'templates' folder

@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        # Retrieve the comment and context from the JSON request body
        data = request.get_json()
        comment = data.get("comment")
        context = data.get("context", "")

        # If no comment is provided, return an error
        if not comment:
            return jsonify({"error": "Comment is required."}), 400

        # Construct the prompt for OpenAI to evaluate the comment in TF 2.0 format
        prompt = f"""
        Below is a TrueFace evaluation of your comment. TrueFace is an AI model designed to promote truth, clarity, and human dignity in public conversation.

        Comment:
        {comment}

        Evaluation (0–5 scale per category):
        Reasoning:
        Tone:
        Engagement:
        Impact:
        Truth Alignment:
        Topical Consideration:
        Total Score: Summary and final score.
        """

        # Call OpenAI's GPT model to get the evaluation using the correct API method for chat models
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or use your preferred model (e.g., GPT-4)
            messages=[
                {"role": "system", "content": "You are an AI model that helps to evaluate comments based on truth, clarity, and dignity."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the generated evaluation from the OpenAI response
        reply = response['choices'][0]['message']['content'].strip()

        # Return the evaluation as a JSON response
        return jsonify({"evaluation": reply})

    except Exception as e:
        # If any errors occur, return the error message
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the Flask app on the default host and port
    app.run(host="0.0.0.0", port=5000)
