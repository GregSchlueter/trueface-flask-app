from flask import Flask, render_template, request
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key securely
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Humanity scale mapping
humanity_scale = {
    0: ("0_cave_echo.png", "Cave Echo", "Echoes outrage with no original thought."),
    1: ("1_torch_waver.png", "Torch Waver", "Signals heat, but sheds little light."),
    2: ("2_tribal_shouter.png", "Tribal Shouter", "Rallies the crowd, not the cause."),
    3: ("3_debater.png", "Debater", "Engages logically but may lack empathy."),
    4: ("4_bridge_builder.png", "Bridge Builder", "Pursues truth and mutual respect."),
    5: ("5_fully_alive.png", "Fully Alive", "Embodies truth, humility, and love.")
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    try:
        system_message = {
            "role": "system",
            "content": "Evaluate the COMMENT in light of the CONTEXT using these five categories: Emotional Proportion, Personal Attribution, Cognitive Openness, Moral Posture, Interpretive Complexity. Provide a short paragraph and a score (0-5) for each."
        }

        user_message = {
            "role": "user",
            "content": f"CONTEXT: {context}\n\nCOMMENT: {comment}"
        }

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[system_message, user_message],
            temperature=0.3
        )

        raw = response.choices[0].message.content
        lines = raw.split("\n")

        evaluations = {}
        scores = {}
        current_category = None

        for line in lines:
            if any(label in line for label in ["Emotional Proportion", "Personal Attribution", "Cognitive Openness", "Moral Posture", "Interpretive Complexity"]):
                parts = line.split(":")
                if len(parts) >= 2:
                    category = parts[0].strip(" 🧠🎯🧩❤️🔍")
                    score = int(parts[1].strip().split("/")[0])
                    scores[category] = score
                    current_category = category
            elif current_category and line.strip():
                evaluations[current_category] = evaluations.get(current_category, '') + ' ' + line.strip()

        total_score = sum(scores.values())

        # Final summary generation
        summary_prompt = f"""Write a concise paragraph for 'Together We Are Better' in light of the context and the comment: '{comment}'. 
        Be candid but kind, logically insightful, and reference if appropriate the tendency toward exaggeration, bias, or missed nuance. 
        End with: 'Together we are better.'"""

        summary_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a wise and charitable assistant helping people reflect deeply on public discourse."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3
        )

        together_we_are_all_stronger = summary_response.choices[0].message.content

        return render_template(
            'result.html',
            intro="Below is a TrueFace 3.0 evaluation of your comment.",
            comment_excerpt=comment,
            scores=scores,
            evaluations=evaluations,
            total_score=total_score,
            together_we_are_all_stronger=together_we_are_all_stronger,
            humanity_scale=humanity_scale
        )

    except Exception as e:
        print("ERROR:", str(e))
        return render_template('result.html', intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == '__main__':
    app.run(debug=True)
