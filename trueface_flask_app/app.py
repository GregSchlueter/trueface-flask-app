from flask import Flask, render_template, request
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key (replace with environment variable or config for security)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Humanity scale mapping
humanity_icons = {
    0: ("0_cave_echo.png", "Cave Echo"),
    1: ("1_torch_waver.png", "Torch Waver"),
    2: ("2_tribal_shouter.png", "Tribal Shouter"),
    3: ("3_debater.png", "Debater"),
    4: ("4_bridge_builder.png", "Bridge Builder"),
    5: ("5_fully_alive.png", "Fully Alive")
}

def calculate_total_score(scores):
    return sum(scores.values())

def map_score_to_humanity(score):
    if score < 5:
        return 1
    elif score < 10:
        return 2
    elif score < 15:
        return 3
    elif score < 20:
        return 4
    else:
        return 5

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    prompt = f"""
    Below is a user comment and optional context. Evaluate the COMMENT (not the context), considering the context as background motivation. Respond in JSON format with:

    {{
      "intro": "TrueFace is a nonpartisan AI model...",
      "comment_excerpt": "...",
      "evaluations": {{
        "Emotional Proportion": "...",
        "Personal Attribution": "...",
        "Cognitive Openness": "...",
        "Moral Posture": "...",
        "Interpretive Complexity": "..."
      }},
      "scores": {{
        "Emotional Proportion": x,
        "Personal Attribution": x,
        "Cognitive Openness": x,
        "Moral Posture": x,
        "Interpretive Complexity": x
      }},
      "together_we_are_all_stronger": "...",
      "final_summary": "...",
      "final_score": x
    }}

    COMMENT: {comment}
    CONTEXT: {context}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_response = response['choices'][0]['message']['content']
        json_start = ai_response.find('{')
        parsed = eval(ai_response[json_start:])  # Consider replacing with `json.loads` with safety
        scores = parsed["scores"]
        total_score = parsed.get("final_score", calculate_total_score(scores))

        final_humanity = map_score_to_humanity(total_score)
        humanity_icon, humanity_title = humanity_icons[final_humanity]

        return render_template(
            'result.html',
            intro=parsed["intro"],
            comment_excerpt=parsed["comment_excerpt"],
            evaluations=parsed["evaluations"],
            scores=scores,
            together_we_are_all_stronger=parsed["together_we_are_all_stronger"],
            final_score=total_score,
            final_summary=parsed["final_summary"],
            humanity_icon=humanity_icon,
            humanity_title=humanity_title,
            humanity_number=final_humanity
        )

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
