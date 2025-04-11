
from flask import Flask, render_template, request
import openai
import os
import json

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_trueface_evaluation(comment, context):
    prompt = f"""Evaluate the following comment in the context of public discourse:

Context: {context}

Comment: {comment}

Return a JSON object with five evaluation categories (Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, Interpretive Complexity) each with a score (0-5) and short explanation. Also include a 'together_we_are_all_stronger' paragraph.
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an impartial evaluator for public discourse."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form.get("comment", "")
    context = request.form.get("context", "")

    try:
        ai_response = get_trueface_evaluation(comment, context)
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        ai_json = ai_response[json_start:json_end]
        data = json.loads(ai_json)

        scores = data["scores"]
        total_score = sum(scores.values())

        if total_score < 5:
            total_score_icon = "0_cave_echo"
        elif total_score < 10:
            total_score_icon = "1_torch_waver"
        elif total_score < 15:
            total_score_icon = "2_tribal_shouter"
        elif total_score < 20:
            total_score_icon = "3_debater"
        elif total_score < 25:
            total_score_icon = "4_bridge_builder"
        else:
            total_score_icon = "5_fully_alive"

        humanity_scale = {
            0: ("0_cave_echo", "Cave Echo", "Repeats what it hears. No reflection."),
            1: ("1_torch_waver", "Torch Waver", "Flares up, but not sure where it’s going."),
            2: ("2_tribal_shouter", "Tribal Shouter", "Loyal but loud, heat over light."),
            3: ("3_debater", "Debater", "Engages thoughtfully, but still battles."),
            4: ("4_bridge_builder", "Bridge Builder", "Connects minds and hearts across differences."),
            5: ("5_fully_alive", "Fully Alive", "Seeks truth with love. Honors others."),
        }

        category_icons = {
            "Emotional Proportion": "fa-brain",
            "Personal Attribution": "fa-bullseye",
            "Cognitive Openness": "fa-puzzle-piece",
            "Moral Posture": "fa-heart",
            "Interpretive Complexity": "fa-magnifying-glass"
        }

        return render_template(
            "result.html",
            comment_excerpt=comment,
            evaluations=data["evaluations"],
            scores=scores,
            total_score=total_score,
            together_we_are_all_stronger=data["together_we_are_all_stronger"],
            humanity_scale=humanity_scale,
            total_score_icon=total_score_icon,
            category_icons=category_icons
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)
