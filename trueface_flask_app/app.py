from flask import Flask, render_template, request
import openai
import os
import json

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are TrueFace, an impartial AI that analyzes public comments across five categories: Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, and Interpretive Complexity. You respond in structured JSON."},
                {"role": "user", "content": f"Comment:\n{comment}\n\nContext:\n{context}"}
            ],
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        json_start = ai_response.find('{')
        json_data = json.loads(ai_response[json_start:])

        return render_template('result.html',
                               comment_excerpt=comment,
                               evaluations=json_data['evaluations'],
                               scores=json_data['scores'],
                               total_score=json_data['total_score'],
                               together=json_data['together_we_are_all_stronger'])

    except Exception as e:
        return f"<h2>System Error:</h2><pre>{e}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
