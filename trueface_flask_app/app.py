import os
import json
import logging
import bleach
from flask import Flask, request, render_template, url_for, redirect
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/evaluate', methods=['POST'])
def evaluate():
    comment = bleach.clean(request.form.get('comment', ''))
    context = bleach.clean(request.form.get('context', ''))

    logger.info(f"Evaluating comment: {comment[:50]}...")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant trained to analyze and score comments. Return a JSON object with keys 'scores', 'evaluations', and 'together_we_are_all_stronger'."
                },
                {
                    "role": "user",
                    "content": f"Evaluate the following comment in context: '{context}' and the comment: '{comment}'"
                }
            ]
        )

        data = json.loads(response.choices[0].message.content)

        required_keys = ['scores', 'evaluations', 'together_we_are_all_stronger']
        if not all(key in data for key in required_keys):
            raise ValueError("Invalid response format")

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
            intro="TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity.",
            comment_excerpt=comment[:160] + "..." if len(comment) > 160 else comment,
            scores=scores,
            evaluations=evaluations,
            total_score=total_score,
            final_humanity_score=final_humanity_score,
            humanity_scale=humanity_scale,
            summary=summary
        )

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {e}")
        return render_template("result.html", intro=f"OpenAI API error: {str(e)}", comment_excerpt=comment)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Response parsing error: {e}")
        return render_template("result.html", intro=f"Error processing evaluation: {str(e)}", comment_excerpt=comment)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return render_template("result.html", intro="Unexpected error occurred.", comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)
