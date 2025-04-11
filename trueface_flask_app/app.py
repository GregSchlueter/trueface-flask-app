from flask import Flask, render_template, request
import openai
import os
import json

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

icons = {
    "Emotional Proportion": "🧠",
    "Personal Attribution": "🎯",
    "Cognitive Openness": "🍀",
    "Moral Posture": "❤️",
    "Interpretive Complexity": "🔍"
}

humanity_icons = [
    "Cave Echo", "Torch Waver", "Tribal Shouter",
    "Debater", "Bridge Builder", "Fully Alive"
]

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    prompt = f"""
You are TrueFace, an AI model designed to promote truth, logic, and human dignity in public conversation.

Evaluate the following COMMENT in light of the CONTEXT. Respond using the exact JSON structure below. Use your best judgment to assess how the comment contributes to constructive, truthful discourse.

CONTEXT: {context}

COMMENT: {comment}

RESPONSE FORMAT (output only valid JSON like below):

{{
  "intro": "TrueFace is a nonpartisan AI model...",
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
    "Personal Attribution": 1,
    "Cognitive Openness": 1,
    "Moral Posture": 1,
    "Interpretive Complexity": 1
  }},
  "together_we_are_all_stronger": "...",
  "total_score": 5
}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are TrueFace, evaluating public discourse."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1200,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content.strip()
        json_start = ai_response.find('{')
        data = json.loads(ai_response[json_start:])

        comment_excerpt = data.get("comment_excerpt", comment[:120] + "...")
        evaluations = data["evaluations"]
        scores = data["scores"]
        total_score = data.get("total_score", sum(scores.values()))
        summary = data.get("together_we_are_all_stronger", "")

        # Humanity scale category by total score
        if total_score <= 4:
            final_icon_score = 1
        elif total_score <= 9:
            final_icon_score = 2
        elif total_score <= 14:
            final_icon_score = 3
        elif total_score <= 19:
            final_icon_score = 4
        else:
            final_icon_score = 5

        return render_template("result.html",
            comment_excerpt=comment_excerpt,
            evaluations=evaluations,
            scores=scores,
            total_score=total_score,
            icons=icons,
            humanity_icons=humanity_icons,
            final_icon_score=final_icon_score,
            summary=summary
        )

    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
