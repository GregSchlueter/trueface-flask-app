from flask import Flask, render_template, request
from openai import OpenAI
import os
import json

app = Flask(__name__, static_folder='static')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form['context']
    truncated_comment = f'"{comment[:80]}..."' if len(comment) > 80 else f'"{comment}"'

    try:
        prompt = (
            "You are an evaluation model. Analyze the following comment and return a JSON object "
            "containing 'scores' (with each of the five categories as keys: Reasoning, Tone, Engagement, "
            "Impact, Truth Alignment), each with a score (0–5) and a one-line explanation. Also return a "
            "'total_summary' and a 'topical_consideration'.\n\n"
            f"Context: {context}\nComment: {comment}\n\n"
            "Respond ONLY with a JSON object in this format:\n\n"
            "{\n"
            "  \"scores\": {\n"
            "    \"Reasoning\": {\"score\": 4, \"explanation\": \"...\"},\n"
            "    \"Tone\": {\"score\": 3, \"explanation\": \"...\"},\n"
            "    ...\n"
            "  },\n"
            "  \"total_summary\": \"...\",\n"
            "  \"topical_consideration\": \"...\"\n"
            "}"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise evaluator of public discourse."},
                {"role": "user", "content": prompt}
            ]
        )

        ai_text = response.choices[0].message.content.strip()

        # Parse AI's JSON response
        data = json.loads(ai_text)

        scores = {k: v["score"] for k, v in data["scores"].items()}
        explanations = {k: v["explanation"] for k, v in data["scores"].items()}
        total_summary = data["total_summary"]
        topical_consideration = data["topical_consideration"]
        total_score = sum(scores.values())

    except Exception as e:
        scores = {cat: 2 for cat in ['Reasoning', 'Tone', 'Engagement', 'Impact', 'Truth Alignment']}
        explanations = {cat: "Evaluation unavailable due to system error." for cat in scores}
        total_score = sum(scores.values())
        total_summary = "Due to a temporary system error, fallback scores were applied."
        topical_consideration = f"(OpenAI Error: {str(e)})"

    return render_template('result.html',
        truncated_comment=truncated_comment,
        context=context,
        scores=scores,
        explanations=explanations,
        total_score=total_score,
        total_summary=total_summary,
        topical_consideration=topical_consideration
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
