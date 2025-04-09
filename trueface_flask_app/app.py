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
            "Evaluate each comment across five categories that commonly shape online discourse. Each category represents a continuum—from unhealthy rhetorical habits to healthy, constructive dialogue. "
            "You will assign a score from 0 (very poor) to 5 (excellent) for each category, with a short, thoughtful explanation (3–5 sentences) of why you gave that score. Do not restate the score in the explanation.\n\n"
            "Here are the five categories:\n\n"
            "1. Emotional Proportion – Does the comment express emotion in a healthy, grounded way? Or is it driven by outrage, hostility, or reactivity?\n"
            "2. Personal Attribution – Does the comment critique ideas or behavior? Or does it scapegoat, generalize, or attack people or groups?\n"
            "3. Cognitive Openness – Does the comment show openness to evidence, complexity, or opposing views? Or does it reflect rigidity, dogmatism, or dismissal?\n"
            "4. Moral Posture – Does the comment affirm shared human dignity? Or does it rely on moral superiority, contempt, or dehumanizing language?\n"
            "5. Interpretive Complexity – Does the comment show thoughtful insight, context, and awareness of nuance? Or is it simplistic, binary, or lacking substance?\n\n"
            "After scoring all five categories, include:\n"
            "- Topical Consideration: A short paragraph that thoughtfully identifies missing context, potential fallacies, or overlooked truths. Avoid taking sides. Speak as a wise, charitable, fact-informed voice who invites deeper understanding.\n"
            "- Final Summary: Offer a final paragraph summarizing how this comment contributes to (or detracts from) meaningful conversation. Invite the commenter toward clarity, empathy, and truth.\n\n"
            "Output your response as a JSON object using the following structure:\n"
            "{\n"
            "  \"intro\": \"TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation.\",\n"
            "  \"comment_excerpt\": \"[Truncated excerpt of the comment]\",\n"
            "  \"evaluations\": {\n"
            "    \"Emotional Proportion\": \"[Explanation of score]\",\n"
            "    \"Personal Attribution\": \"[Explanation of score]\",\n"
            "    \"Cognitive Openness\": \"[Explanation of score]\",\n"
            "    \"Moral Posture\": \"[Explanation of score]\",\n"
            "    \"Interpretive Complexity\": \"[Explanation of score]\"\n"
            "  },\n"
            "  \"scores\": {\n"
            "    \"Emotional Proportion\": 0,\n"
            "    \"Personal Attribution\": 0,\n"
            "    \"Cognitive Openness\": 0,\n"
            "    \"Moral Posture\": 0,\n"
            "    \"Interpretive Complexity\": 0\n"
            "  },\n"
            "  \"topical_consideration\": \"[Balanced, insightful paragraph]\",\n"
            "  \"final_summary\": \"[Short paragraph]\",\n"
            "  \"total_score\": 0\n"
            "}\n"
            "Ensure the total_score is the correct sum of the five category scores.\n"
            "Be truthful, fair, and constructive."
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
            final_summary="We were unable to generate a full evaluation at this time.",
            topical_consideration=f"(OpenAI Error: {str(e)})"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
