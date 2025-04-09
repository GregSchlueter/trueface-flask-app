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
            "Your purpose is to promote truth, logic, and human dignity by helping people recognize patterns of speech that either build or break trust in dialogue.\n\n"
            "Evaluate each comment across five categories. Each category should include:\n"
            "- A short evaluation paragraph (3–5 sentences)\n"
            "- A numeric score from 0 (very poor) to 5 (excellent)\n\n"
            "The five categories are:\n"
            "1. Emotional Proportion\n"
            "2. Personal Attribution\n"
            "3. Cognitive Openness\n"
            "4. Moral Posture\n"
            "5. Interpretive Complexity\n\n"
            "Then provide:\n"
            "- A 'topical_consideration' paragraph: offering constructive insight into how the comment might be better framed or understood.\n"
            "- A 'final_summary' paragraph: summarizing how this comment contributes to or detracts from dignified public discourse.\n\n"
            "Return your full response as a JSON object in the following format:\n\n"
            "{\n"
            "  \"intro\": \"TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation.\",\n"
            "  \"comment_excerpt\": \"[Excerpt]\",\n"
            "  \"evaluations\": {\n"
            "    \"Emotional Proportion\": \"[Short paragraph]\",\n"
            "    \"Personal Attribution\": \"[Short paragraph]\",\n"
            "    \"Cognitive Openness\": \"[Short paragraph]\",\n"
            "    \"Moral Posture\": \"[Short paragraph]\",\n"
            "    \"Interpretive Complexity\": \"[Short paragraph]\"\n"
            "  },\n"
            "  \"scores\": {\n"
            "    \"Emotional Proportion\": 0–5,\n"
            "    \"Personal Attribution\": 0–5,\n"
            "    \"Cognitive Openness\": 0–5,\n"
            "    \"Moral Posture\": 0–5,\n"
            "    \"Interpretive Complexity\": 0–5\n"
            "  },\n"
            "  \"topical_consideration\": \"[Thoughtful, constructive paragraph]\",\n"
            "  \"final_summary\": \"[Short reflection paragraph]\",\n"
            "  \"total_score\": [Sum of above scores]\n"
            "}\n\n"
            "You must return valid JSON that can be parsed directly."
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
        # Uncomment to debug
        # print("AI Response:", ai_response)

        data = json.loads(ai_response)

        return render_template('result.html',
            intro=data["intro"],
            comment_excerpt=data["comment_excerpt"],
            evaluations=data["evaluations"],
            scores=data["scores"],
            total_score=data["total_score"],
            topical_consideration=data["topical_consideration"],
            final_summary=data["final_summary"]
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
            final_summary="",
            topical_consideration=f"(OpenAI Error: {str(e)})"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
