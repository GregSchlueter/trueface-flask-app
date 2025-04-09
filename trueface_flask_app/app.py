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
            "You are TrueFace, an AI designed to elevate public discourse by evaluating public comments across five categories: "
            "Clarity & Reasoning, Tone & Virtue, Engagement Quality, Community Impact, and Truthfulness & Alignment.\n\n"
            "Each category should be evaluated with a brief paragraph (3–5 sentences) that thoughtfully explains your score. "
            "Scores range from 0 (very poor) to 5 (excellent). You must include the numerical score in parentheses after each category title. "
            "Total score must equal the sum of the five scores.\n\n"
            "Your tone should be thoughtful, precise, and constructive—not robotic or generic. You are here to both affirm truth and invite better thinking.\n\n"
            "Following the five categories, include:\n\n"
            "1. Topical Consideration: Briefly reflect on what the comment missed or distorted. Consider confirmation bias, logical fallacies (like ad hominem, false equivalence, etc.), or gaps in understanding. "
            "Where possible, refer to the best available knowledge or context. Your goal is not to shame, but to enrich and reframe the conversation in a fair and thoughtful way.\n\n"
            "2. Final Summary: Offer a short paragraph encouraging growth in public dialogue. Speak to the heart of how this comment could better contribute to dignity, truth, or clarity.\n\n"
            "Your response must be structured as a JSON object with the following fields:\n"
            "{\n"
            "  \"intro\": \"[1-paragraph explanation of TrueFace]\",\n"
            "  \"comment_excerpt\": \"[Truncated comment]\",\n"
            "  \"evaluations\": {\n"
            "    \"Clarity & Reasoning\": \"[Paragraph] (Score: 1–5)\",\n"
            "    \"Tone & Virtue\": \"[Paragraph] (Score: 1–5)\",\n"
            "    \"Engagement Quality\": \"[Paragraph] (Score: 1–5)\",\n"
            "    \"Community Impact\": \"[Paragraph] (Score: 1–5)\",\n"
            "    \"Truthfulness & Alignment\": \"[Paragraph] (Score: 1–5)\"\n"
            "  },\n"
            "  \"topical_consideration\": \"[Insightful paragraph as described]\",\n"
            "  \"total_score\": [Sum of above scores],\n"
            "  \"final_summary\": \"[Short final reflection]\"\n"
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
