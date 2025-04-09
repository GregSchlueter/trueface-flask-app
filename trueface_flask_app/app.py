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
            "You are TrueFace, an AI designed to evaluate public comments using a rigorous framework grounded "
            "in classical reasoning, social psychology, ethics, and communication science.\n\n"
            "Given the following comment and context, respond with a JSON object using this structure:\n\n"
            "{\n"
            "  \"intro\": \"[1-paragraph summary of what TrueFace is]\",\n"
            "  \"comment_excerpt\": \"[shortened comment]\",\n"
            "  \"evaluations\": {\n"
            "    \"Clarity & Reasoning\": \"[paragraph-style analysis]\",\n"
            "    \"Tone & Virtue\": \"[paragraph-style analysis]\",\n"
            "    \"Engagement Quality\": \"[paragraph-style analysis]\",\n"
            "    \"Community Impact\": \"[paragraph-style analysis]\",\n"
            "    \"Truthfulness & Alignment\": \"[paragraph-style analysis]\"\n"
            "  },\n"
            "  \"topical_consideration\": \"[insightful paragraph connecting the comment to the broader issue]\",\n"
            "  \"total_score\": 0–25,\n"
            "  \"final_summary\": \"[summary paragraph offering reflection and improvement]\"\n"
            "}"
        )

        full_input = f"Context: {context}\nComment: {comment}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": full_input}
            ]
        )

        ai_text = response.choices[0].message.content.strip()
        data = json.loads(ai_text)

        return render_template('result.html',
            intro=data["intro"],
            comment_excerpt=data["comment_excerpt"],
            evaluations=data["evaluations"],
            total_score=data["total_score"],
            final_summary=data["final_summary"],
            topical_consideration=data["topical_consideration"]
        )

    except Exception as e:
        return render_template('result.html',
            intro="TrueFace is currently unavailable due to a system error.",
            comment_excerpt=truncated_comment,
            evaluations={
                "Clarity & Reasoning": "System error. Please try again later.",
                "Tone & Virtue": "System error.",
                "Engagement Quality": "System error.",
                "Community Impact": "System error.",
                "Truthfulness & Alignment": "System error."
            },
            total_score=0,
            final_summary="We were unable to generate a full evaluation at this time.",
            topical_consideration=f"(OpenAI Error: {str(e)})"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
