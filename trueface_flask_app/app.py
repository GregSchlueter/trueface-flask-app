from flask import Flask, request, jsonify
import openai
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    comment = data.get("comment")
    context = data.get("context")

    if not comment:
        return jsonify({"error": "Comment is required."}), 400

    prompt = f"""
Below is a TrueFace 2.0 evaluation of a comment.
TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity. Grounded in classical reasoning, social psychology, ethical philosophy, and communication science, TrueFace evaluates public comments across five core categories—reasoning, tone, engagement, impact, and truth alignment. Each is rated from 0 to 5. A higher score reflects a greater contribution to truthful, respectful, and constructive dialogue across differences.

Comment (excerpt):
{comment}

Context:
{context}

Please respond with the TF 2.0 evaluation including each category score with explanation, Topical Consideration, and Total Score.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an impartial AI that evaluates online comments using the TrueFace 2.0 model."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"evaluation": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import sys

    port = os.environ.get("PORT")
    if port is None:
        print("⚠️ PORT environment variable not set. Defaulting to 5000.", file=sys.stderr)
        port = 5000
    else:
        print(f"✅ Render PORT detected: {port}", file=sys.stderr)
        port = int(port)

    app.run(host="0.0.0.0", port=port)