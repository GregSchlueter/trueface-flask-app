import os
import openai
from flask import Flask, request, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

humanity_scale = {
    0: ("0_cave_echo", "Cave Echo", "Echoes others without engagement"),
    1: ("1_torch_waver", "Torch Waver", "Flares up, but offers little light"),
    2: ("2_tribal_shouter", "Tribal Shouter", "Stands with the tribe, not the truth"),
    3: ("3_debater", "Debater", "Raises ideas, but not always people"),
    4: ("4_bridge_builder", "Bridge Builder", "Connects people through clarity"),
    5: ("5_fully_alive", "Fully Alive", "Speaks truth with love and courage")
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form.get('context', '')

    prompt = f"""
    Evaluate the following comment using the TrueFace 3.0 model, responding with a JSON object containing:
    - intro
    - comment_excerpt
    - evaluations: a dictionary with each category and a description
    - scores: a dictionary with each category and a number from 0–5
    - together_we_are_all_stronger: a wise summary
    - total_score (if not present, calculate from scores)

    Comment: {comment}
    Context: {context}
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        ai_text = response.choices[0].message.content.strip()
        json_start = ai_text.find('{')
        json_data = ai_text[json_start:]
        data = eval(json_data)

        if isinstance(data, dict):
            if "total_score" not in data:
                data["total_score"] = sum(data["scores"].values())
        else:
            raise ValueError("Unexpected response format.")

        return render_template(
            'result.html',
            intro=data.get("intro", ""),
            comment_excerpt=data.get("comment_excerpt", comment),
            evaluations=data.get("evaluations", {}),
            scores=data.get("scores", {}),
            together_we_are_all_stronger=data.get("together_we_are_all_stronger", ""),
            total_score=data.get("total_score", 0),
            humanity_scale=humanity_scale
        )

    except Exception as e:
        print(f"ERROR: {e}")
        return render_template('result.html', intro="There was an error processing your evaluation.", comment_excerpt=comment)

if __name__ == '__main__':
    app.run(debug=True)
