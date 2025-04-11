import os
import json
import logging
import bleach
from flask import Flask, request, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from openai import OpenAI, OpenAIError
from urllib.parse import quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging for Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define form with explicit length validators
class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(min=1, max=1000, message="Comment must be 1–1000 characters.")])
    context = TextAreaField('Context', validators=[Length(max=1000, message="Context must be 0–1000 characters.")])
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
    # Decode and sanitize inputs
    comment = bleach.clean(request.args.get('comment', ''))
    context = bleach.clean(request.args.get('context', ''))

    if not comment:
        logger.warning("No comment provided for evaluation")
        return render_template("result.html",
                             intro="Error: No comment provided.",
                             comment_excerpt="",
                             humanity_scale={})  # Empty dict as fallback

    logger.info(f"Evaluating comment (first 50 chars): {comment[:50]}...")

    # Define humanity scale (moved outside try block to ensure availability)
    humanity_scale = {
        0: ("0_cave_echo", "Cave Echo", "Trapped in reactive noise, no original thought."),
        1: ("1_torch_waver", "Torch Waver", "Carries passion but fuels fire more than light."),
        2: ("2_tribal_shouter", "Tribal Shouter", "Speaks for a side, not to be understood."),
        3: ("3_debater", "Debater", "Engages ideas but still seeks to win."),
        4: ("4_bridge_builder", "Bridge Builder", "Invites dialogue and genuine clarity."),
        5: ("5_fully_alive", "Fully Alive", "Models truth with logic, love, and humility.")
    }

    try:
        # Call OpenAI API with stricter JSON enforcement
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an analytical assistant trained to evaluate comments. "
                        "Respond ONLY with a valid JSON object containing three keys: "
                        "'scores' (a dictionary with categories 'Clarity', 'Empathy', 'Logic', 'Respect', 'Constructiveness' and integer scores 0-5), "
                        "'evaluations' (a dictionary with the same categories and string explanations), "
                        "and 'together_we_are_all_stronger' (a summary string encouraging constructive dialogue). "
                        "Do not include any text outside the JSON object. Example: "
                        '{"scores": {"Clarity": 4, "Empathy": 3, "Logic": 4, "Respect": 2, "Constructiveness": 3}, '
                        '"evaluations": {"Clarity": "Clear points made.", "Empathy": "Some understanding shown.", '
                        '"Logic": "Reasoning is solid.", "Respect": "Tone could be more respectful.", '
                        '"Constructiveness": "Offers critique but lacks solutions."}, '
                        '"together_we_are_all_stronger": "Let’s focus on constructive ideas to unite us."}'
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

        # Log raw response for debugging
        raw_response = response.choices[0].message.content
        logger.info(f"Raw OpenAI response: {raw_response[:200]}...")

        # Parse JSON response
        data = json.loads(raw_response)

        # Validate response structure
        required_keys = ['scores', 'evaluations', 'together_we_are_all_stronger']
        if not all(key in data for key in required_keys):
            raise ValueError("Invalid response format: missing required keys")

        scores = data["scores"]
        evaluations = data["evaluations"]
        summary = data["together_we_are_all_stronger"]

        # Validate scores
        valid_scores = {}
        for category, score in scores.items():
            try:
                score_int = int(score)
                if 0 <= score_int <= 5 and category in evaluations:
                    valid_scores[category] = score_int
                else:
                    logger.warning(f"Invalid score for {category}: {score}")
            except (ValueError, TypeError):
                logger.warning(f"Non-integer score for {category}: {score}")

        if not valid_scores:
            raise ValueError("No valid scores provided")

        # Calculate total score
        total_score = sum(valid_scores.values())
        final_humanity_score = min(5, max(0, total_score // len(valid_scores)))

        # Render results
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
                             humanity_scale=humanity_scale)  # Pass humanity_scale
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}. Raw response: {raw_response}")
        return render_template("result.html",
                             intro="Error: Unable to parse evaluation response. Please try again.",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale,  # Pass humanity_scale
                             scores={},  # Fallback for template
                             evaluations={},
                             total_score=0,
                             final_humanity_score=0,
                             summary="We couldn’t process this comment, but together we can improve.")
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return render_template("result.html",
                             intro=f"Error: {str(e)}",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale)  # Pass humanity_scale
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template("result.html",
                             intro="Unexpected error occurred during evaluation.",
                             comment_excerpt=comment,
                             humanity_scale=humanity_scale)  # Pass humanity_scale

if __name__ == "__main__":
    app.run(debug=True)