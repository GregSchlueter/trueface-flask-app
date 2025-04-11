from flask import Flask, render_template, request
from openai import OpenAI
import os
import json

app = Flask(__name__)

client = OpenAI()

HUMANITY_SCALE = {
    0: ["cave_echo", "Cave Echo"],
    1: ["torch_waver", "Torch Waver"],
    2: ["tribal_shouter", "Tribal Shouter"],
    3: ["debater", "Debater"],
    4: ["bridge_builder", "Bridge Builder"],
    5: ["fully_alive", "Fully Alive"]
}

SUMMARY_SCALE = {
    0:  "0_cave_echo.png",
    1:  "1_torch_waver.png",
    2:  "2_tribal_shouter.png",
    3:  "3_debater.png",
    4:  "4_bridge_builder.png",
    5:  "5_fully_alive.png"
}

SUMMARY_LABELS = {
    0: "Cave Echo",
    1: "Torch Waver",
    2: "Tribal Shouter",
    3: "Debater",
    4: "Bridge Builder",
    5: "Fully Alive"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    try:
        prompt = (
            f"Evaluate the following comment in light of the provided context using 5 criteria "
            f"(Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, Interpretive Complexity). "
            f"Return a JSON with scores (0–5) and brief insights. \n\nContext:\n{context}\n\nComment:\n{comment}"
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        json_start = ai_response.find('{')
        json_data = ai_response[json_start:]
        data = json.loads(json_data)

        if isinstance(data, int):
            raise ValueError("Data returned as integer unexpectedly.")

        total_score = sum(data["scores"].values())
        final_summary = data.get("together_we_are_all_stronger", "Together we are better.")

        # Determine final humanity score bucket
        if total_score < 5:
            summary_num = 1
        elif total_score < 10:
            summary_num = 2
        elif total_score < 15:
            summary_num = 3
        elif total_score < 20:
            summary_num = 4
        else:
            summary_num = 5

        return render_template(
            'result.html',
            comment_excerpt=comment,
            evaluations=data["evaluations"],
            scores=data["scores"],
            total_score=total_score,
            final_summary=final_summary,
            summary_icon=SUMMARY_SCALE[summary_num],
            summary_label=SUMMARY_LABELS[summary_num],
            humanity_scale=HUMANITY_SCALE
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template(
            'result.html',
            intro="There was an error processing your evaluation.",
            comment_excerpt=comment,
            evaluations={},
            scores={},
            total_score=0,
            final_summary="Oops! Something went wrong.",
            summary_icon="0_cave_echo.png",
            summary_label="Cave Echo",
            humanity_scale=HUMANITY_SCALE
        )

if __name__ == '__main__':
    app.run(debug=True)
