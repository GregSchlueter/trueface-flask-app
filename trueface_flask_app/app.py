import os
from flask import Flask, render_template, request
from openai import OpenAI

app = Flask(__name__)

client = OpenAI()

# Humanity scale mapping (icon, label, description)
humanity_scale = {
    0: ("0_cave_echo.png", "Cave Echo", "Grunts in the dark. No light, no lift."),
    1: ("1_torch_waver.png", "Torch Waver", "Throws light, but mostly heat."),
    2: ("2_tribal_shouter.png", "Tribal Shouter", "Chants, but doesn’t check facts."),
    3: ("3_debater.png", "Debater", "Sharp, fair fight. Not always aware."),
    4: ("4_bridge_builder.png", "Bridge Builder", "Listens hard. Connects dots and people."),
    5: ("5_fully_alive.png", "Fully Alive", "Truth in love. Humanity wins.")
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI trained to evaluate public comments."},
                {"role": "user", "content": f"Evaluate the following comment in context:
Context: {context}
Comment: {comment}"}
            ]
        )
        content = response.choices[0].message.content

        # Parse scores (simulate expected format)
        lines = content.split('\n')
        scores = {}
        evaluations = {}
        total_score = 0

        for line in lines:
            if ':' in line and '/' in line:
                parts = line.split(':')
                category = parts[0].strip()
                score = int(parts[1].strip().split('/')[0])
                scores[category] = score
                total_score += score
            elif category:
                evaluations[category] = line.strip()

        # Determine humanity icon
        if total_score < 5:
            humanity_icon = 0
        elif total_score < 10:
            humanity_icon = 1
        elif total_score < 15:
            humanity_icon = 2
        elif total_score < 20:
            humanity_icon = 3
        elif total_score < 25:
            humanity_icon = 4
        else:
            humanity_icon = 5

        return render_template("result.html",
                               intro="Below is a TrueFace 3.0 evaluation of your comment. TrueFace is an AI model designed to promote truth, logic, and human dignity.",
                               comment_excerpt=comment,
                               scores=scores,
                               evaluations=evaluations,
                               total_score=total_score,
                               humanity_icon=humanity_icon,
                               humanity_scale=humanity_scale)
    except Exception as e:
        print("ERROR:", e)
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)