import os
import json
import logging
import bleach
from flask import Flask, request, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from openai import OpenAI, OpenAIError
from urllib.parse import quote, unquote
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000)])
    context = TextAreaField('Context', validators=[Length(max=1000)])
    submit = SubmitField('Evaluate')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CommentForm()
    if form.validate_on_submit():
        return redirect(url_for('evaluate',
                              comment=quote(form.comment.data),
                              context=quote(form.context.data or '')))
    return render_template('index.html', form=form)

@app.route('/evaluate', methods=['GET'])
def evaluate():
    comment = bleach.clean(unquote(request.args.get('comment', '')))
    context = bleach.clean(unquote(request.args.get('context', '')))

    if not comment:
        logger.warning("No comment provided for evaluation")
        return render_template("result.html",
                             intro="Error: No comment provided.",
                             comment_excerpt="",
                             humanity_scale={})

    logger.info(f"Evaluating comment (first 50 chars): {comment[:50]}...")

    humanity_scale = {
        0: ("0_cave_echo", "Cave Echo", "Trapped in reactive noise, no original thought."),
        1: ("1_torch_waver", "Torch Waver", "Carries passion but fuels fire more than light."),
        2: ("2_tribal_shouter", "Tribal Shouter", "Speaks for a side, not to be understood."),
        3: ("3_debater", "Debater", "Engages ideas but still seeks to win."),
        4: ("4_bridge_builder", "Bridge Builder", "Invites dialogue and genuine clarity."),
        5: ("5_fully_alive", "Fully Alive", "Models truth with logic, love, and humility.")
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an analytical assistant trained to evaluate comments with wisdom, charity, and psychological insight. "
                        "Respond ONLY with a valid JSON object containing three keys: "
                        "'scores' (a dictionary with categories 'Clarity', 'Empathy', 'Logic', 'Respect', 'Constructiveness' and integer scores 0-5), "
                        "'evaluations' (a dictionary with the same categories and concise string explanations), "
                        "and 'together_we_are_all_stronger' (a detailed, constructive string offering wise, direct feedback). "
                        "For 'together_we_are_all_stronger', identify logical flaws, confirmation bias, or errors of judgment; address factual claims with objective insight; "
                        "suggest specific improvements and explain their importance for fostering meaningful relationships, grounded in psychology, virtue, and goodwill. "
                        "Do not include text outside the JSON object. Example: "
                        '{"scores": {"Clarity": 4, "Empathy": 3, "Logic": 4, "Respect": 2, "Constructiveness": 3}, '
                        '"evaluations": {"Clarity": "Clear points made.", "Empathy": "Some understanding shown.", '
                        '"Logic": "Reasoning is solid.", "Respect": "Tone could be more respectful.", '
                        '"Constructiveness": "Critiques but lacks solutions."}, '
                        '"together_we_are_all_stronger": "Your passion is clear, but the argument leans on hyperbole, risking confirmation bias by assuming intent without evidence. '
                        'Consider grounding claims in verifiable facts—e.g., specific quotes or events—and inviting dialogue with questions rather than assertions. '
                        'This builds trust and understanding, key to relationships, as psychology shows we connect best through mutual respect and curiosity."}'
                    )
                },
                {
                    "role": "user",
                    "content": f"Evaluate this comment in context: Context: '{context}'. Comment: '{comment}'."
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        raw_response = response.choices[0].message.content
        logger.info(f"Raw OpenAI response: {raw_response[:200]}...")
        data = json.loads(raw_response)

        required_keys = ['scores', 'evaluations', 'together_we_are_all_stronger']
        if not all(key in data for key in required_keys):
            raise ValueError("Invalid response format: missing required keys")

        scores = data["scores"]
        evaluations = data["evaluations"]
        summary = data["together_we_are_all_stronger"]

        valid_scores = {}
        for category, score in scores.items():
            try:
                score_int = int(score)
                if 0 <= score_int <= 5 and category in evaluations:
                    valid_scores[category] = score_int
            except (ValueError, TypeError):
                logger.warning(f"Non-integer score for {category}: {score}")

        if not valid_scores:
            raise ValueError("No valid scores provided")

        total_score = sum(valid_scores.values())
        final_humanity_score = min(5, max(0, total_score // len(valid_scores)))

        return render_template(
            "result.html",
            comment_excerpt=comment[:160] + "..." if len(comment) > 160 else comment,
            scores=valid_scores,
            evaluations=evaluations,
            total_score=total_score,
            final_humanity_score=final_humanity_score,
            humanity_scale=humanity_scale,
            summary=summary,
            intro="TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity."
        )

    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return render_template("result.html",
                             intro=f"OpenAI API error: {str(e)}",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}. Raw response: {raw_response}")
        return render_template("result.html",
                             intro="Error: Unable to parse evaluation response. Please try again.",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale,
                             scores={},
                             evaluations={},
                             total_score=0,
                             final_humanity_score=0,
                             summary="We couldn’t process this comment, but together we can improve.")
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return render_template("result.html",
                             intro=f"Error: {str(e)}",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template("result.html",
                             intro="Unexpected error occurred during evaluation.",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale)

if __name__ == "__main__":
    app.run(debug=True)