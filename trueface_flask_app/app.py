from flask import Flask, render_template, request
import openai
import json
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

humanity_scale = {
    0: ["0_cave_echo", "Echoing the loudest voices with no reflection"],
    1: ["1_torch_waver", "Fired up but not fully focused"],
    2: ["2_tribal_shouter", "Rooted in a side, but not in truth"],
    3: ["3_debater", "Ready to think, but still sharp-edged"],
    4: ["4_bridge_builder", "Seeking truth and building unity"],
    5: ["5_fully_alive", "Truthful, respectful, and fully human"]
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form.get("comment")
    context = request.form.get("context", "")

    prompt = f"""
You are TrueFace 3.0, an AI model designed to evaluate online comments for their contribution to public conversation. Given the comment and any context, assess the comment on these five dimensions (scored 0–5):

1. Emotional Proportion
2. Personal Attribution
3. Cognitive Openness
4. Moral Posture
5. Interpretive Complexity

Return JSON with this structure:
{{
  "intro": "...",
  "comment_excerpt": "...",
  "evaluations": {{
    "Emotional Proportion": "...",
    "Personal Attribution": "...",
    "Cognitive Openness": "...",
    "Moral Posture": "...",
    "Interpretive Complexity": "..."
  }},
  "scores": {{
    "Emotional Proportion": 1,
    "Personal Attribution": 2,
    "Cognitive Openness": 3,
    "Moral Posture": 4,
    "Interpretive Complexity": 5
  }},
  "together_we_are_all_stronger": "...",
  "total_score": 15
}}
Context: {context}
Comment: {comment}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_response = response.choices[0].message.content.strip()

        json_start = ai_response.find('{')
        json_str = ai_response[json_start:]
        data = json.loads(json_str)

        # Auto-calculate score if missing
        if isinstance(data, dict) and "total_score" not in data:
            scores = data.get("scores", {})
            data["total_score"] = sum(scores.values())

        return render_template("result.html", **data, humanity_scale=humanity_scale)

    except Exception as e:
        print("ERROR:", e)
        return render_template("result.html",
                               intro="There was an error processing your evaluation.",
                               comment_excerpt=comment,
                               evaluations={},
                               scores={},
                               together_we_are_all_stronger=str(e),
                               total_score=0,
                               humanity_scale=humanity_scale)
