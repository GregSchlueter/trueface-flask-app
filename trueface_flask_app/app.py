from flask import Flask, render_template, request
from openai import OpenAI
import os
import random

app = Flask(__name__, static_folder='static')

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form['context']
    truncated_comment = (comment[:80] + '...') if len(comment) > 80 else comment

    try:
        prompt = (
            "Evaluate the following user comment in five categories on a scale from 0 to 5. "
            "Provide a one-line explanation for each category. Then provide a one-paragraph total summary and a topical consideration.\n\n"
            f"Context: {context}\nComment: {comment}\n\n"
            "Respond in the following format:\n"
            "Reasoning: [score] - [explanation]\n"
            "Tone: [score] - [explanation]\n"
            "Engagement: [score] - [explanation]\n"
            "Impact: [score] - [explanation]\n"
            "Truth Alignment: [score] - [explanation]\n"
            "Total Summary: [summary paragraph]\n"
            "Topical Consideration: [insightful reflection]"
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a precise evaluator of public discourse."},
                {"role": "user", "content": prompt}
            ]
        )

        ai_text = response.choices[0].message.content.strip()

        # Very basic parsing (to be improved later with regex or structured output)
        lines = ai_text.split('\n')
        scores = {}
        explanations = {}

        for line in lines:
            if ':' in line and '-' in line:
                category, rest = line.split(':', 1)
                score, explanation = rest.strip().split('-', 1)
                scores[category.strip()] = int(score.strip())
                explanations[category.strip()] = explanation.strip()
            elif line.startswith("Total Summary:"):
                total_summary = line.replace("Total Summary:", "").strip()
            elif line.startswith("Topical Consideration:"):
                topical_consideration = line.replace("Topical Consideration:", "").strip()

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
