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
        system_prompt = (
            "You are TrueFace 3.0, an AI model designed to evaluate public comments through the lens of rhetorical integrity. "
            "Your role is to guide users toward meaningful, respectful, and truthful dialogue. For each of the five rhetorical categories:\n"
            "- Provide a 2–4 sentence evaluation.\n"
            "- Assign a score from 0–5.\n\n"
            "The categories are:\n"
            "- Emotional Proportion\n"
            "- Personal Attribution\n"
            "- Cognitive Openness\n"
            "- Moral Posture\n"
            "- Interpretive Complexity\n\n"
            "After scoring, return a final section titled 'Together We Are All Stronger'. This should be a thoughtful, balanced, respectful paragraph beginning with 'Dear Commentor,' and ending with the bolded phrase: 'Together we are better.' It should combine wisdom, affirmation, and guidance to improve the comment or engagement.\n\n"
            "Return a valid JSON object in the following format:\n"
            "{\n"
            "  \"intro\": \"TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation.\",\n"
            "  \"comment_excerpt\": \"...\",\n"
            "  \"evaluations\": {\n"
            "    \"Emotional Proportion\": \"...\",\n"
            "    \"Personal Attribution\": \"...\",\n"
            "    \"Cognitive Openness\": \"...\",\n"
            "    \"Moral Posture\": \"...\",\n"
            "    \"Interpretive Complexity\": \"...\"\n"
            "  },\n"
            "  \"scores\": {\n"
            "    \"Emotional Proportion\": 0–5,\n"
            "    \"Personal Attribution\": 0–5,\n"
            "    \"Cognitive Openness\": 0–5,\n"
            "    \"Moral Posture\": 0–5,\n"
            "    \"Interpretive Complexity\": 0–5\n"
            "  },\n"
            "  \"together_we_are_all_stronger\": \"...\",\n"
            "  \"total_score\": 0–25\n"
            "}"
        )

        full_input = f"Context: {context}\nComment: {comment}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_input}
            ]
        )

        ai_response = response.choices[0].message.content.strip()
        data = json.loads(ai_response)

        return render_template('result.html',
            intro=data["intro"],
            comment_excerpt=data["comment_excerpt"],
            evaluations=data["evaluations"],
            scores=data["scores"],
            total_score=data["total_score"],
            together_we_are_all_stronger=data["together_we_are_all_stronger"]
        )

    except Exception as e:
        return render_template('result.html',
            intro="TrueFace is currently unavailable due to a system error.",
            comment_excerpt=truncated_comment,
            evaluations={
                "Emotional Proportion": "System error.",
                "Personal Attribution": "System error.",
                "Cognitive Openness": "System error.",
                "Moral Posture": "System error.",
                "Interpretive Complexity": "System error."
            },
            scores={
                "Emotional Proportion": 0,
                "Personal Attribution": 0,
                "Cognitive Openness": 0,
                "Moral Posture": 0,
                "Interpretive Complexity": 0
            },
            total_score=0,
            together_we_are_all_stronger="(OpenAI Error: " + str(e) + ")"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
