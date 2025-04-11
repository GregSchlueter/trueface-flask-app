from flask import Flask, render_template, request
from openai import OpenAI

app = Flask(__name__)
client = OpenAI()

humanity_scale = {
    0: ("0_cave_echo", "Cave Echo", "Echoing groupthink without reflection."),
    1: ("1_torch_waver", "Torch Waver", "Spreading outrage more than insight."),
    2: ("2_tribal_shouter", "Tribal Shouter", "Promoting sides over solutions."),
    3: ("3_debater", "Debater", "Engaging issues but defending turf."),
    4: ("4_bridge_builder", "Bridge Builder", "Reasoned and respectful engagement."),
    5: ("5_fully_alive", "Fully Alive", "Truthful, charitable, and courageous.")
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form.get('comment', '')
    context = request.form.get('context', '')

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a neutral evaluator."},
                {"role": "user", "content": f"Evaluate the following comment in context:

Context: {context}

Comment: {comment}"}
            ],
            temperature=0.3
        )

        data = eval(response.choices[0].message.content.strip())
        scores = data["scores"]
        evaluations = data["evaluations"]
        total_score = sum(scores.values())

        return render_template("result.html",
                               intro="TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity.",
                               comment_excerpt=comment,
                               scores=scores,
                               evaluations=evaluations,
                               total_score=total_score,
                               humanity_scale=humanity_scale)
    except Exception as e:
        print("ERROR:", e)
        return render_template("result.html",
                               intro="There was an error processing your evaluation.",
                               comment_excerpt=comment)

if __name__ == '__main__':
    app.run(debug=True)