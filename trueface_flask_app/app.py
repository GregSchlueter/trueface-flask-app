import os
import json
import openai
from flask import Flask, request, render_template

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form["comment"]
    context = request.form.get("context", "")

    messages = [
        {
            "role": "user",
            "content": f"""Evaluate the following comment in context:

CONTEXT: {context}
COMMENT: {comment}

Return a JSON object with two keys:
- 'evaluations': maps each of the 5 criteria to a short paragraph.
- 'scores': maps each of the same criteria to an integer score (0 to 5).

The criteria are:
1. Emotional Proportion
2. Personal Attribution
3. Cognitive Openness
4. Moral Posture
5. Interpretive Complexity

Do not include any extra text or notes, only the JSON object.
"""
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.4,
        )
        data = json.loads(response.choices[0].message["content"])
        scores = data["scores"]
        total_score = sum(scores.values())

        humanity_scale = {
            0: ("0_cave_echo", "Cave Echo", "Reactively echoing base impulses"),
            1: ("1_torch_waver", "Torch Waver", "Carrying outrage without direction"),
            2: ("2_tribal_shouter", "Tribal Shouter", "Rooted in group-think hostility"),
            3: ("3_debater", "Debater", "Engaging but still combative"),
            4: ("4_bridge_builder", "Bridge Builder", "Listening and reasoning with others"),
            5: ("5_fully_alive", "Fully Alive", "Pursuing truth with wisdom and love")
        }

        return render_template(
            "result.html",
            intro="Below is a TrueFace 3.0 evaluation of your comment. TrueFace is an AI model designed to promote truth, logic, clarity, and human dignity.",
            comment_excerpt=comment,
            evaluations=data["evaluations"],
            scores=scores,
            total_score=total_score,
            humanity_scale=humanity_scale,
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)