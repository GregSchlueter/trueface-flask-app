import os
import json
import logging
import bleach
from flask import Flask, request, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length
from openai import OpenAI, OpenAIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-fallback-secret-key')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging for debugging on Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define form class for CSRF protection and validation
class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(max=1000)])
    context = TextAreaField('Context', validators=[Length(max=1000)])
    submit = SubmitField('Evaluate')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CommentForm()
    if form.validate_on_submit():
        return redirect(url_for('evaluate', 
                                comment=form.comment.data, 
                                context=form.context.data))
    return render_template('index.html', form=form)

@app.route('/evaluate', methods=['GET'])
def evaluate():
    comment = bleach.clean(request.args.get('comment', ''))
    context = bleach.clean(request.args.get('context', ''))
    
    if not comment:
        return render_template("result.html", 
                               intro="Error: No comment provided.", 
                               comment_excerpt="")

    logger.info(f"Evaluating comment: {comment[:50]}...")

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
                        "You are a helpful assistant trained to analyze and score comments. "
                        "Return a JSON object with three keys: "
                        "'scores' (a dictionary with categories like 'Clarity', 'Empathy', etc., and integer scores 0-5), "
                        "'evaluations' (a dictionary with the same categories and string explanations), "
                        "and 'together_we_are_all_stronger' (a summary string encouraging constructive dialogue). "
                        "Respond ONLY with valid JSON, without commentary or extra text."
                    )
                },
                {
                    "role": "user",
                    "content": f"Evaluate the following comment in context: '{context}' and the comment: '{comment}'."
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        data = json.loads(response.choices[0].message.content)

        required_keys = ['scores', 'evaluations', 'together_we_are_all_stronger']
        if not all(key in data for key in required_keys):
            raise ValueError("Invalid response format from OpenAI")

        scores = data["scores"]
        evaluations = data["evaluations"]
        summary = data["together_we_are_all_stronger"]
        total_score = sum(int(score) for score in scores.values() if isinstance(score, (int, str)) and str(score).isdigit())
        final_humanity_score = min(5, max(0, total_score // 5))

        return render_template(
            "result.html",
            comment_excerpt=comment[:160] + "..." if len(comment) > 160 else comment,
            scores=scores,
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
                               comment_excerpt=comment)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return render_template("result.html", 
                               intro="Error: Invalid response format from evaluation.", 
                               comment_excerpt=comment)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return render_template("result.html", 
                               intro=f"Error: {str(e)}", 
                               comment_excerpt=comment)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template("result.html", 
                               intro="Unexpected error occurred during evaluation.", 
                               comment_excerpt=comment)

if __name__ == "__main__":
    app.run(debug=True)