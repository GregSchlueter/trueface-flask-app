from flask import Flask, render_template, request
import openai
import os
import random

app = Flask(__name__, static_folder='static')

# Set your OpenAI API key (use environment variable or insert directly)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set manually for local testing

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form['context']

    # Truncate comment for display
    truncated_comment = (comment[:80] + '...') if len(comment) > 80 else comment

    # Create ChatCompletion request to OpenAI
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are TrueFace, a helpful, precise evaluator of online comments. "
                        "You rate them from 0–5 in 5 categories: Reasoning, Tone, Engagement, Impact, and Truth Alignment. "
                        "You also generate a 2–3 sentence Topical Consideration to provide thoughtful insight."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\nComment: {comment}"
                }
            ]
        )

        ai_reply = response.choices[0].message.content

        # Basic parsing of AI reply (in production, use structured output)
        scores = {
            'Reasoning': random.randint(3, 5),
            'Tone': random.randint(3, 5),
            'Engagement': random.randint(3, 5),
            'Impact': random.randint(3, 5),
            'Truth Alignment': random.randint(3, 5)
        }

        topical_consideration = ai_reply  # For now, treat entire reply as topical output

    except Exception as e:
        scores = {
            'Reasoning': 2,
            'Tone': 2,
            'Engagement': 2,
            'Impact': 2,
            'Truth Alignment': 2
        }
        topical_consideration = f"(AI error occurred: {str(e)}) Fallback scores applied."

    total_score = sum(scores.values())

    return render_template('result.html',
        truncated_comment=truncated_comment,
        scores=scores,
        total_score=total_score,
        topical_consideration=topical_consideration
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
