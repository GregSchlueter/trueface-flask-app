from flask import Flask, request, render_template
import openai
import os

app = Flask(__name__)

# OpenAI API Key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# Humanity Scale (image_name, label, description)
humanity_scale = {
    0: ("0_cave_echo", "Cave Echo", "Echoing reactions without reflection."),
    1: ("1_torch_waver", "Torch Waver", "Inflames without illuminating."),
    2: ("2_tribal_shouter", "Tribal Shouter", "Fights more than thinks."),
    3: ("3_debater", "Debater", "Engages with heat and honesty."),
    4: ("4_bridge_builder", "Bridge Builder", "Constructive and curious."),
    5: ("5_fully_alive", "Fully Alive", "Truthful, humble, and humane.")
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form.get("comment")
    context = request.form.get("context", "")

    try:
        # Use OpenAI to get evaluation (GPT-4)
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a neutral assistant evaluating comments for social media quality. Evaluate each of the following categories from 0 to 5 and give short feedback: Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, Interpretive Complexity."},
                {"role": "user", "content": f"Comment: {comment}\nContext: {context}"}
            ]
        )

        # Simulated structured output
        data = {
            "evaluations": {
                "Emotional Proportion": "Moderately reasoned, with some emotional edge.",
                "Personal Attribution": "Mix of critique toward person and ideas.",
                "Cognitive Openness": "Doesn’t invite deeper dialogue.",
                "Moral Posture": "Some moral judgment expressed.",
                "Interpretive Complexity": "Some oversimplification of the issue."
            },
            "scores": {
                "Emotional Proportion": 3,
                "Personal Attribution": 2,
                "Cognitive Openness": 2,
                "Moral Posture": 3,
                "Interpretive Complexity": 2
            }
        }

        evaluations = data["evaluations"]
        scores = data["scores"]
        total_score = sum(scores.values())

        # Map total_score to humanity scale level
        if total_score < 5:
            humanity_icon_num = 0
        elif total_score < 10:
            humanity_icon_num = 1
        elif total_score < 15:
            humanity_icon_num = 2
        elif total_score < 20:
            humanity_icon_num = 3
        elif total_score < 25:
            humanity_icon_num = 4
        else:
            humanity_icon_num = 5

        return render_template(
            "result.html",
            intro="Below is a TrueFace 3.0 evaluation of your comment.",
            comment_excerpt=comment,
            evaluations=evaluations,
            scores=scores,
            total_score=total_score,
            humanity_icon_num=humanity_icon_num,
            humanity_scale=humanity_scale
        )

    except Exception as e:
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment, error=str(e))

if __name__ == "__main__":
    app.run(debug=True)
