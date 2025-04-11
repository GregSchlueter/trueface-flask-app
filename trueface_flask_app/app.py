from flask import Flask, render_template, request
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Humanity scale dictionary
humanity_scale = {
    0: ("0_cave_echo", "Cave Echo", "Echoes others without engagement"),
    1: ("1_torch_waver", "Torch Waver", "Flares up, but offers little light"),
    2: ("2_tribal_shouter", "Tribal Shouter", "Stands with the tribe, not the truth"),
    3: ("3_debater", "Debater", "Raises ideas, but not always people"),
    4: ("4_bridge_builder", "Bridge Builder", "Connects people through clarity"),
    5: ("5_fully_alive", "Fully Alive", "Speaks truth with love and courage")
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    comment = request.form["comment"]
    context = request.form.get("context", "")

    try:
        # Call OpenAI
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that evaluates social media comments on five dimensions..."},
                {"role": "user", "content": f"Context: {context}\nComment: {comment}"}
            ]
        )

        response_text = response.choices[0].message.content.strip()

        # Parse scores and evaluations
        lines = response_text.split("\n")
        evaluations = {}
        scores = {}
        current_key = None

        for line in lines:
            if line.startswith("**"):
                key = line.split("**")[1].strip(":")
                score = int(line.split(":")[2].strip().split("/")[0])
                scores[key] = score
                current_key = key
                evaluations[key] = ""
            elif current_key:
                evaluations[current_key] += line.strip() + " "

        # Handle Together We Are Better and Final Score
        together = next((line for line in lines if "Together we are better" in line), "")
        total_score = sum(scores.values())

        # Final humanity score for icon display
        if total_score <= 4:
            humanity_level = 0
        elif total_score <= 9:
            humanity_level = 1
        elif total_score <= 14:
            humanity_level = 2
        elif total_score <= 19:
            humanity_level = 3
        elif total_score <= 24:
            humanity_level = 4
        else:
            humanity_level = 5

        return render_template("result.html",
            intro="Below is a TrueFace 3.0 evaluation of your comment. TrueFace is an AI model designed to promote truth, logic, and human dignity.",
            comment_excerpt=comment,
            evaluations=evaluations,
            scores=scores,
            total_score=total_score,
            together=together,
            humanity_level=humanity_level,
            humanity_scale=humanity_scale
        )

    except Exception as e:
        print("ERROR:", e)
        return render_template("result.html", intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)
