import os
from flask import Flask, request, render_template
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant trained to analyze and score comments."},
                {"role": "user", "content": f"Evaluate the following comment in context: '{context}' and the comment: '{comment}'."}
            ]
        )
        data = eval(response.choices[0].message.content)

        scores = data["scores"]
        evaluations = data["evaluations"]
        summary = data["together_we_are_all_stronger"]
        total_score = sum(scores.values())

        humanity_scale = {
            0: ("0_cave_echo", "Cave Echo", "Trapped in reactive noise, no original thought."),
            1: ("1_torch_waver", "Torch Waver", "Carries passion but fuels fire more than light."),
            2: ("2_tribal_shouter", "Tribal Shouter", "Speaks for a side, not to be understood."),
            3: ("3_debater", "Debater", "Engages ideas but still seeks to win."),
            4: ("4_bridge_builder", "Bridge Builder", "Invites dialogue and genuine clarity."),
            5: ("5_fully_alive", "Fully Alive", "Models truth with logic, love, and humility.")
        }

        final_humanity_score = min(5, max(0, total_score // 5))

        return render_template(
            "result.html",
            comment_excerpt=comment[:160] + "..." if len(comment) > 160 else comment,
            scores=scores,
            evaluations=evaluations,
            total_score=total_score,
            final_humanity_score=final_humanity_score,
            humanity_scale=humanity_scale,
            summary=summary,
            intro="TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity."
        )
    except Exception as e:
        print("ERROR:", e)
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)