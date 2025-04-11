from flask import Flask, render_template, request
import openai
import os
import json

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Humanity scale config (ensure 3 items per tuple)
humanity_scale = {
    0: ("0_cave_echo", "Cave Echo", "Grunts in the dark. No light, no lift."),
    1: ("1_torch_waver", "Torch Waver", "Throws light, but mostly heat."),
    2: ("2_tribal_shouter", "Tribal Shouter", "Chants, but doesn't check facts."),
    3: ("3_debater", "Debater", "Sharp, fair, not always aware."),
    4: ("4_bridge_builder", "Bridge Builder", "Listens hard. Connects dots and people."),
    5: ("5_fully_alive", "Fully Alive", "Truth in love. Humanity wins.")
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form["comment"]
    context = request.form.get("context", "")

    prompt = f"""Evaluate the following COMMENT in light of its CONTEXT:
---
COMMENT: "{comment}"
CONTEXT: "{context}"
---
Respond in this strict JSON format:

{{
  "evaluations": {{
    "Emotional Proportion": "...",
    "Personal Attribution": "...",
    "Cognitive Openness": "...",
    "Moral Posture": "...",
    "Interpretive Complexity": "..."
  }},
  "scores": {{
    "Emotional Proportion": 1-5,
    "Personal Attribution": 1-5,
    "Cognitive Openness": 1-5,
    "Moral Posture": 1-5,
    "Interpretive Complexity": 1-5
  }},
  "together_we_are_all_stronger": "...",
  "summary": "..."
}}"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        # Extract JSON from response
        full_text = response.choices[0].message.content
        json_start = full_text.find("{")
        json_end = full_text.rfind("}") + 1
        json_content = full_text[json_start:json_end]
        data = json.loads(json_content)

        scores = data["scores"]
        total_score = sum(scores.values())

        # Determine final humanity icon (0-5) from total
        if total_score <= 4:
            final_icon = 0
        elif total_score <= 9:
            final_icon = 1
        elif total_score <= 14:
            final_icon = 2
        elif total_score <= 19:
            final_icon = 3
        elif total_score <= 24:
            final_icon = 4
        else:
            final_icon = 5

        return render_template(
            "result.html",
            intro="Below is a TrueFace evaluation of your comment.",
            comment_excerpt=comment,
            evaluations=data["evaluations"],
            scores=scores,
            total_score=total_score,
            together=data["together_we_are_all_stronger"],
            summary=data.get("summary", ""),
            final_icon=final_icon,
            humanity_scale=humanity_scale
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template(
            "result.html",
            intro="There was an error processing your evaluation.",
            comment_excerpt=comment,
            evaluations={},
            scores={},
            total_score=0,
            together="We hit a snag. Try again soon!",
            summary="",
            final_icon=0,
            humanity_scale=humanity_scale
        )
