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
            "You are TrueFace 3.0, an AI model designed to evaluate public comments in response to an online article, post, or conversation (the context). "
            "Your job is to assess the COMMENT in light of the CONTEXT—not as a combination. Treat the context as background, helping you fairly assess how the comment responds in tone, logic, and moral posture.\n\n"
            "Evaluate the comment across five categories:\n"
            "- Emotional Proportion (5 = calm and reasoned, 0 = hostile and reactive)\n"
            "- Personal Attribution (5 = focuses on ideas and content, 0 = attacks people, motives, or character—even subtly, such as with sarcasm or insinuation)\n"
            "- Cognitive Openness (5 = invites understanding, 0 = dismisses all views)\n"
            "- Moral Posture (5 = acknowledges complexity and seeks common good, 0 = moral superiority or scorn)\n"
            "- Interpretive Complexity (5 = fair and nuanced, 0 = oversimplified or propagandistic)\n\n"
            "For each category:\n"
            "- Provide a short paragraph (2–4 sentences)\n"
            "- Give a score from 0 to 5\n\n"
            "Then conclude with a final section titled 'Together We Are All Stronger':\n"
            "- Begin with: 'Dear Commenter,'\n"
            "- Address the person respectfully and wisely\n"
            "- Gently challenge confirmation bias, misinformation, or unfair framing\n"
            "- Encourage respectful, truthful, constructive engagement\n"
            "- Where applicable, bring in relevant facts or logic that invite perspective\n"
            "- End with: **Together we are better.**\n\n"
            "Return your output as a valid JSON object in this format:\n"
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

        if not response.choices or not response.choices[0].message:
            raise ValueError("GPT did not return a valid message.")

        ai_response = response.choices[0].message.content
        print("\n--- RAW GPT OUTPUT ---\n", ai_response, "\n")

        if not ai_response or ai_response.strip() == "":
            raise ValueError("GPT response was empty.")

        json_start = ai_response.find('{')
        if json_start == -1:
            raise ValueError("No JSON object found in GPT response.")

        json_string = ai_response[json_start:]
        data = json.loads(json_string)

        required_keys = ["evaluations", "scores", "together_we_are_all_stronger"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing key: {key}")

        subkeys = [
            "Emotional Proportion",
            "Personal Attribution",
            "Cognitive Openness",
            "Moral Posture",
            "Interpretive Complexity"
        ]
        for key in subkeys:
            if key not in data["evaluations"] or key not in data["scores"]:
                raise ValueError(f"Missing subkey: {key}")

        # ✅ Auto-calculate total_score if not provided
        score_values = list(data["scores"].values())
        total_score = data.get("total_score", sum(score_values))

        return render_template('result.html',
            intro=data.get("intro", "TrueFace is an AI model designed to promote truth, logic, and human dignity in public conversation."),
            comment_excerpt=data.get("comment_excerpt", truncated_comment),
            evaluations=data["evaluations"],
            scores=data["scores"],
            total_score=total_score,
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
            together_we_are_all_stronger="(System Error: " + str(e) + ")"
        )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
