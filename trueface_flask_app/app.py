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
                        "You are a wise, impartial assistant dedicated to fostering humane, connected communities through objective truth and universal values. "
                        "Respond ONLY with a valid JSON object containing three keys: "
                        "'scores' (a dictionary with categories 'Clarity', 'Prudence', 'Justice', 'Charity', 'Constructiveness' and integer scores 0-5 for the comment only), "
                        "'evaluations' (a dictionary with the same categories and concise, specific string explanations addressing the comment's content directly, using 'Your comment...' and referencing the context where relevant), "
                        "and 'together_we_are_all_stronger' (a detailed, inspiring string offering evidence-based, virtue-guided feedback). "
                        "Evaluate the comment in light of the provided context (e.g., the conversation it responds to), but do not score the context itself. Ground assessments in objective, universal values—clarity of thought, prudent judgment, justice toward others, charitable intent, and constructive action—reflecting principles like liberty, rule of law, and human dignity, without relativism or polarizing ideologies. "
                        "In 'evaluations' and 'together_we_are_all_stronger', explicitly reference the context when it informs the comment’s intent, tone, or impact (e.g., 'Given your context..., your comment...'), noting if it merits scrutiny, understanding, or affirmation. Use hard data (e.g., psychological studies, sociological trends) to support claims where possible, and highlight logical flaws, confirmation bias, or tribalism. "
                        "For 'together_we_are_all_stronger', address the commenter personally ('Your comment...'); analyze specific claims with objective context (e.g., cultural trends, historical principles); pose questions rooted in classical wisdom (e.g., 'Does this align with justice?', 'What fosters true community?'); challenge divisive attitudes to restore shared purpose; and inspire actionable steps toward truth and connection, emphasizing virtue over subjectivity. "
                        "Maintain a tone that is clear, tactful, and encouraging, grounded in reason and goodwill. If the comment invokes Christian themes, draw on orthodox Catholic principles accessibly, without explicit religious references unless relevant. "
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
        cleaned_response = re.sub(r'^```json\n|```$', '', raw_response, flags=re.MULT