import os
import json
import logging
import bleach
import re
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
        # Pre-encode comment and context for clean URLs
        comment = quote(form.comment.data, safe='')
        context = quote(form.context.data or '', safe='')
        return redirect(url_for('evaluate', comment=comment, context=context))
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
                             context_excerpt="",
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
                        "You are a wise, impartial assistant dedicated to fostering humane, connected discourse in a polarized world. "
                        "Respond ONLY with a valid JSON object containing three keys: "
                        "'scores' (a dictionary with categories 'Clarity', 'Empathy', 'Logic', 'Respect', 'Constructiveness' and integer scores 0-5 for the comment only), "
                        "'evaluations' (a dictionary with the same categories and concise, specific string explanations addressing the comment's content directly, using 'Your comment...' and referencing the context where relevant), "
                        "and 'together_we_are_all_stronger' (a detailed, inspiring string offering tactful, evidence-based feedback). "
                        "Evaluate the comment in light of the provided context (e.g., the conversation it responds to), but do not score the context itself. "
                        "In 'evaluations' and 'together_we_are_all_stronger', explicitly reference the context when it informs the comment’s intent, tone, or impact (e.g., 'Given your context..., your comment...'), noting if it merits scrutiny, understanding, or affirmation. "
                        "Tie explanations to the comment’s specific claims or tone, reflecting contemporary political, social, and cultural realities (e.g., polarization, media dynamics). "
                        "For 'together_we_are_all_stronger', address the commenter personally ('Your comment...'); analyze specific claims or assumptions with objective context (e.g., cultural trends, public records); "
                        "pose constructive questions rooted in psychological and social sciences (e.g., 'Is it fair to dismiss all dialogue?', 'What builds meaningful connection?'); "
                        "challenge dismissive or divisive attitudes to reduce tribalism; and inspire actionable steps to build bridges, emphasizing truth, mutual understanding, and human dignity. "
                        "Maintain a tone that is clear, tactful, and encouraging, grounded in logic and goodwill. "
                        "Do not include text outside the JSON object."
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
        # Strip markdown code fences
        cleaned_response = re.sub(r'^```json\n|```$', '', raw_response, flags=re.MULTILINE).strip()
        data = json.loads(cleaned_response)

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
            context_excerpt=context[:160] + "..." if len(context) > 160 else context,
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
                             context_excerpt=context,
                             humanity_scale=humanity_scale)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}. Raw response: {raw_response}")
        return render_template("result.html",
                             intro="Error: Unable to parse evaluation response. Please try again.",
                             comment_excerpt=comment,
                             context_excerpt=context,
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
                             context_excerpt=context,
                             humanity_scale=humanity_scale)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template("result.html",
                             intro="Unexpected error occurred during evaluation.",
                             comment_excerpt=comment,
                             context_excerpt=context,
                             humanity_scale=humanity_scale)

if __name__ == "__main__":
    app.run(debug=True)