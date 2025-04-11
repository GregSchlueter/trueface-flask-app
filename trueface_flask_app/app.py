import os
import openai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Humanity scale mappings
humanity_scale = {
    0: ("0_cave_echo.png", "Cave Echo"),
    1: ("1_torch_waver.png", "Torch Waver"),
    2: ("2_tribal_shouter.png", "Tribal Shouter"),
    3: ("3_debater.png", "Debater"),
    4: ("4_bridge_builder.png", "Bridge Builder"),
    5: ("5_fully_alive.png", "Fully Alive")
}

def score_to_icon(score):
    if score >= 20: return humanity_scale[5]
    elif score >= 15: return humanity_scale[4]
    elif score >= 10: return humanity_scale[3]
    elif score >= 5: return humanity_scale[2]
    else: return humanity_scale[1]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    prompt = f"""
You are TrueFace 3.0, an impartial, truth-seeking AI. Evaluate the COMMENT below in light of the CONTEXT provided. Use a 0–5 scale for each category, followed by a short paragraph. Focus on truth, logic, and human dignity.

COMMENT: {comment}
CONTEXT: {context}

Return JSON with:
1. intro
2. comment_excerpt
3. evaluations (Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, Interpretive Complexity)
4. scores (each category 0–5)
5. together_we_are_all_stronger (a short reflection paragraph)
6. total_score (sum of the five categories)
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        ai_reply = response.choices[0].message.content.strip()
        json_start = ai_reply.find('{')
        json_data = ai_reply[json_start:]

        import json
        data = json.loads(json_data)

        # Fallback score if total is not provided
        if "total_score" not in data:
            data["total_score"] = sum(data["scores"].values())

        data["icon_path"], data["icon_name"] = score_to_icon(data["total_score"])
        return render_template('result.html', **data)

    except Exception as e:
        print("ERROR:", e)
        return render_template('result.html', intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == '__main__':
    app.run(debug=True)
