import os
from flask import Flask, render_template, request
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_comment(comment, context=""):
    system_prompt = "You are TrueFace, a nonpartisan AI model designed to promote truth, logic, clarity, and human dignity..."
    user_prompt = f"Comment: {comment}\nContext: {context}\nEvaluate this..."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5
    )

    return response.choices[0].message.content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    humanity_scale = [
        ("0_cave_echo", "Echoing the loudest voices with no reflection"),
        ("1_torch_waver", "Fired up but not fully focused"),
        ("2_tribal_shouter", "Rooted in a side, but not in truth"),
        ("3_debater", "Ready to think, but still sharp-edged"),
        ("4_bridge_builder", "Seeking truth and building unity"),
        ("5_fully_alive", "Truthful, respectful, and fully human"),
    ]

    try:
        ai_response = analyze_comment(comment, context)
        data = eval(ai_response.strip())  # Replace with json.loads() if needed

        if isinstance(data, dict) and "total_score" not in data:
            data["total_score"] = sum(data.get("scores", {}).values())

        humanity_index = min(5, max(0, data["total_score"] // 5))

        return render_template(
            "result.html",
            intro="Below is a TrueFace 3.0 evaluation of your comment.",
            comment_excerpt=comment,
            evaluations=data.get("evaluations", {}),
            scores=data.get("scores", {}),
            total_score=data.get("total_score", 0),
            humanity_level=humanity_index,
            humanity_scale=humanity_scale,
            together_we_are_all_stronger=data.get("together_we_are_all_stronger", "")
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template(
            "result.html",
            intro="There was an error processing your evaluation.",
            comment_excerpt=comment,
            humanity_scale=humanity_scale,
            evaluations={},
            scores={},
            total_score=0,
            humanity_level=0,
            together_we_are_all_stronger="Something went wrong. Please try again."
        )

if __name__ == '__main__':
    app.run(debug=True)
