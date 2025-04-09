from flask import Flask, render_template, request
from openai import OpenAI
import os
import json

app = Flask(__name__, static_folder='static')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = request.form['comment']
    context = request.form['context']
    truncated_comment = f'"{comment[:80]}..."' if len(comment) > 80 else f'"{comment}"'

    try:
        system_prompt = (
            "You are TrueFace 3.0, an AI model designed to evaluate public comments through the lens of rhetorical integrity. "
            "You help elevate online dialogue by assessing comments across five dimensions, each reflecting a human virtue or defect. "
            "A higher score (4–5) means the comment reflects a virtue (e.g., calmness, fairness, openness). A lower score (0–1) reflects the opposite (e.g., hostility, scapegoating, closed-mindedness).\n\n"
            "Evaluate the comment in five categories:\n"
            "- Emotional Proportion (5 = calm and reasoned, 0 = hostile and reactive)\n"
            "- Personal Attribution (5 = focuses on ideas, 0 = attacks people or motives)\n"
            "- Cognitive Openness (5 = invites understanding, 0 = dismisses all views)\n"
            "- Moral Posture (5 = acknowledges complexity and seeks common good, 0 = moral superiority)\n"
            "- Interpretive Complexity (5 = fair and nuanced, 0 = oversimplified or propagandistic)\n\n"
            "For each category:\n"
            "- Provide a short paragraph (2–4 sentences)\n"
            "- Give a score from 0 to 5\n\n"
            "Then conclude with one final paragraph titled 'Together We Are All Stronger'.\n"
            "- Begin with: 'Dear Commentor,'\n"
            "- Address the person respectfully and wisely, engaging factual issues or patterns if helpful\n"
            "- Challenge confirmation bias or flawed thinking gently but truthfully\n"
            "- Call them to better dialogue and understanding\n"
            "- End the paragraph with the line (in bold): 'Together we are better.'\n\n"
            "Return a valid JSON object in the following format:\n"
            "{\n"
            "  \"intro\": \"TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation.\",\n"
            "  \"comment_excerpt\": \"[truncated or full comment]\",\n"
            "  \"evaluations\": {\n"
            "    \"Emotional Proportion\": \"...\",\n"
            "    \"Personal Attribution\": \"...\",\n"
            "    \"Cognitive Openness\": \"...\",\n"
            "    \"Moral Posture\": \"...\",\n"
            "    \"Interpretive Complexity\": \"...\"\n"
            "  },\n"
            "  \"scores\": {\n"
            "    \"Emotional Proportion\": 0–5,\n"
            "    \"Personal Attribution\": 0–5,\n"
            "    \"Cognitive Openness\": 0–5,\n"
            "    \"Moral Posture\": 0–5,\n"
            "    \"Interpretive Complexity\": 0–5\n"
            "  },\n"
            "  \"together_we_are_all_stronger\": \"...\",\n"
            "  \"total_score\": 0–25\n"
            "}"
        )

        full_input = f"Context: {context}\nComment: {comment}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_input}
            ]
        )

        raw_output = response.choices[0].message.content
        print("\n--- RAW GPT OUTPUT ---\n", raw_output, "\n")

        if not raw_output:
            raise ValueError("GPT returned an empty response.")

        ai_response = raw_output.strip()

        # Save to local file if possible (for local debugging)
        try:
            with open("last_gpt_response.json", "w", encoding="utf-8") as f:
                f.write(ai_response)
        except:
            pass  # Ignore if on Render

        # Parse GPT response as JSON
        data = json.loads(ai_response)

        # Validate structure
        required_main_keys = ["evaluations", "scores", "together_we_are_all_stronger"]
        for key in required_main_keys:
            if key not in data:
                raise ValueError(f"Missing key: {key}")

        required_subkeys = [
            "Emotional Proportion",
            "Personal Attribution",
            "Cognitive Openness",
            "Moral Posture",
            "Interpretive Complexity"
        ]
        for key in required_subkeys:
            if key not in data["evaluations"] or key not in data["scores"]:
                raise ValueError(f"Missing category: {key}")

        return render_template('result.html',
            intro=data.get("intro", "TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation."),
            comment_excerpt=data.get("comment_excerpt", truncated_comment),
            evaluations=data["evaluations"],
            scores=data["scores"],
            total_score=data["total_score"],
            together_we_are_all_stronger=data["together_we_are_all_stronger"]
        )

    except Exception as e:
        print("ERROR:", e)
        return render_template('result.html',
            intro="TrueFace is currently unavailable due to a system error.",
            comment_excerpt=truncated_comment,
            evaluations={
                "Emotional Proportion": "System error.",
                "Personal Attribution": "System error.",
                "Cognitive Openness": "System error.",
                "Moral Posture": "System error.",
                "Interpretive Complexity": "System error."
            },
            scores={
                "Emotional Proportion": 0,
                "Personal Attribution": 0,
                "Cognitive Openness": 0,
                "Moral Posture": 0,
                "Interpretive Complexity": 0
            },
            total_score=0,
            together_we_are_all_stronger="(OpenAI Error: " + str(e) + ")"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
