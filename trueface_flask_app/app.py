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
    comment = TextAreaField('Comment', validators=[DataRequired(message="Comment is required"), Length(min=1, max=1000)])
    context = TextAreaField('Context', validators=[Length(max=1000)])
    submit = SubmitField('Evaluate')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = CommentForm()
    if request.method == 'POST':
        logger.info(f"Received POST request, form data: {form.data}")
        if form.validate_on_submit():
            logger.info("Form validated, redirecting to evaluate")
            comment = quote(form.comment.data.strip(), safe='')
            context = quote(form.context.data.strip() if form.context.data else '', safe='')
            return redirect(url_for('evaluate', comment=comment, context=context))
        else:
            logger.warning(f"Form validation failed, errors: {form.errors}")
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
                        "You are a wise, impartial assistant dedicated to fostering humane, connected communities through objective truth and universal values, grounded in classical virtues like justice, prudence, charity, and flourishing. "
                        "Respond ONLY with a valid JSON object containing four keys: "
                        "'scores' (a dictionary with categories 'Clarity', 'Prudence', 'Justice', 'Charity', 'Constructiveness' and integer scores 0-5 for the comment only), "
                        "'evaluations' (a dictionary with the same categories and concise, specific string explanations addressing the comment's content directly, using 'Your comment...' and referencing the context where relevant), "
                        "'together_we_are_all_stronger' (a detailed, inspiring string offering evidence-based, virtue-guided feedback), "
                        "and 'wise_personal_coach' (a short, pithy string affirming the user’s good intent and suggesting one growth action in 10-15 words, tagged with 'In the thought of [wise figure like G.K. Chesterton, C.S. Lewis, Stephen Covey]', matching the comment’s theme, e.g., 'You’re a seeker of truth—temper it with charity. In the thought of C.S. Lewis.'). "
                        "Evaluate the comment in light of the provided context, but do not score the context itself. Ground assessments strictly in objective truth and good, as defined by classical virtues and natural law, never endorsing 'diversity' or inclusivity as standalone values unless they align with universal moral standards (e.g., reject harmful actions like violence outright). "
                        "Assume the commenter seeks some common good; interpret their intent charitably while explicitly identifying logical flaws (e.g., false dichotomy, confirmation bias, overgeneralization) or factual errors that undermine human dignity (e.g., dismissing diverse motives without evidence). Reference specific elements from the comment and context (e.g., named individuals like Trump, policies like border security, events like arrests or deportations) in 'evaluations' and 'together_we_are_all_stronger' (e.g., 'Given your context about Trump’s arrest celebration..., your comment...'). "
                        "In 'together_we_are_all_stronger', balance critique with recognition of real-world complexities (e.g., governance is messy but can yield measurable goods like reduced fentanyl deaths or child trafficking, alongside errors like wrongful deportations that may be corrected). Use specific data to support claims (e.g., 'DEA stats show a 15% drop in fentanyl deaths from 2017-2020', 'Pew Research notes 60% support for border security', 'FBI data on trafficking declines'), and affirm positive actions (e.g., policy successes, rectified mistakes) while addressing errors or biases (e.g., assuming support equals complicity risks confirmation bias). Pose 2-3 questions rooted in classical virtues (e.g., 'Does justice dismiss all support, or weigh actions like trafficking prevention?', 'Is prudence served by assuming complicity?', 'Does assuming immorality reflect confirmation bias?') to challenge uncritical assumptions and promote reflection. Suggest actionable steps (e.g., 'Ask about policy outcomes to understand motives') to foster dialogue that unites rather than divides. "
                        "For 'Clarity', assess how clearly the comment conveys its intent. For 'Prudence', evaluate sound judgment and evidence-weighing. For 'Justice', measure fairness and respect for dignity. For 'Charity', judge goodwill and truth-bound empathy, rejecting error while seeking understanding. For 'Constructiveness', assess whether the comment advances flourishing through actionable, truth-seeking dialogue, contributing to communal good. "
                        "For 'wise_personal_coach', affirm the user with a positive trait tied to their intent (e.g., 'You’re a seeker of justice...'), suggest one specific action linked to the comment/context (e.g., 'weigh Trump’s policies fairly...'), and tag with a wise figure whose style matches the theme (e.g., justice for Lewis, truth for Chesterton, community for Covey). Keep it secular unless Christian themes are invoked, then draw on orthodox Catholic principles accessibly, emphasizing charity, truth, and redemption. "
                        "Score generously for good intent (e.g., 4-5 for clarity if clear), moderately for uncritical assumptions or logical flaws (e.g., 3-4 for prudence if contextually relevant), and lower for divisive tone or affronts to dignity (e.g., 2-3 for charity if harsh), aiming for a balanced total (e.g., 15-18/25 for nuanced comments). Maintain a tone that is clear, tactful, and encouraging, affirming shared values, celebrating truth, and reframing division as opportunities for unity, inspired by a style that acknowledges human brokenness alongside potential for redemption and measurable good. "
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
        cleaned_response = re.sub(r'^```json\n|```$', '', raw_response, flags=re.MULTILINE).strip()
        data = json.loads(cleaned_response)

        required_keys = ['scores', 'evaluations', 'together_we_are_all_stronger', 'wise_personal_coach']
        if not all(key in data for key in required_keys):
            raise ValueError("Invalid response format: missing required keys")

        scores = data["scores"]
        evaluations = data["evaluations"]
        summary = data["together_we_are_all_stronger"]
        coach = data["wise_personal_coach"]

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

        return render_template("result.html",
                              comment_excerpt=comment[:160] + "..." if len(comment) > 160 else comment,
                              context_excerpt=context[:160] + "..." if len(context) > 160 else context,
                              scores=valid_scores,
                              evaluations=evaluations,
                              total_score=total_score,
                              final_humanity_score=final_humanity_score,
                              humanity_scale=humanity_scale,
                              summary=summary,
                              coach=coach,
                              intro="TrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity.")

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