<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrueFace 2.0 Evaluation Portal</title>
    <meta property="og:title" content="TrueFace | Reveal the Real" />
    <meta property="og:description" content="Online social media comment evaluator based on truth, logic, and human dignity." />
    <meta property="og:image" content="TrueFace3.png" />
    <meta property="og:url" content="https://truefaceworld.com" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="icon" href="favicon.png" type="image/png">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 40px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: #fff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
        }
        label {
            font-weight: bold;
        }
        textarea, input[type="submit"] {
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }
        input[type="submit"] {
            background-color: #007bff;
            color: white;
            cursor: pointer;
            border: none;
        }
        input[type="submit"]:hover {
            background-color: #0056b3;
        }
        .result {
            white-space: pre-wrap;
            background-color: #e8f4ff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #cce0f5;
            margin-top: 20px;
        }
        #copyButton {
            display: none;
            margin-top: 10px;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        #copyButton:hover {
            background-color: #45a049;
        }
        .social-icons {
            text-align: center;
            margin-top: 30px;
        }
        .social-icons a {
            display: inline-block;
            margin: 0 10px;
        }
        .social-icons img {
            width: 32px;
            height: 32px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="TrueFace3.png" alt="TrueFace Logo" style="max-width: 250px;">
        </div>
        <h1>TrueFace 2.0 Evaluation</h1>
        <form id="evaluationForm">
            <label for="comment">Comment for Evaluation:</label>
            <textarea id="comment" name="comment" rows="6" placeholder="Paste the comment you want evaluated..."></textarea>

            <label for="context">Original Comment (for Context):</label>
            <textarea id="context" name="context" rows="4" placeholder="Paste the comment this is replying to..."></textarea>

            <input type="submit" value="Submit for Evaluation">
        </form>
        <div id="evaluationResult" class="result"></div>
        <button id="copyButton">Copy to Clipboard</button>
    </div>

    <div style="text-align: center; margin-top: 40px; font-size: 14px;">
        <p>
            TrueFace is going to revolutionize the quality of human relationships through social media.<br>
            Please share your feedback and/or contact us for investment opportunities:
            <a href="mailto:Revolution@TrueFaceWorld.com">Revolution@TrueFaceWorld.com</a>
        </p>
    </div>

    <div class="social-icons">
        <a href="https://www.facebook.com/sharer/sharer.php?u=https://truefaceworld.com" target="_blank" title="Share on Facebook">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/facebook.svg" alt="Facebook">
        </a>
        <a href="https://twitter.com/intent/tweet?url=https://truefaceworld.com&text=Check%20out%20TrueFace%20%7C%20Reveal%20the%20Real" target="_blank" title="Share on Twitter">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/twitter.svg" alt="Twitter">
        </a>
        <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://truefaceworld.com" target="_blank" title="Share on LinkedIn">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/linkedin.svg" alt="LinkedIn">
        </a>
        <a href="https://www.instagram.com/" target="_blank" title="Share on Instagram">
            <img src="https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/instagram.svg" alt="Instagram">
        </a>
    </div>

    <script>
        const form = document.getElementById('evaluationForm');
        const resultDiv = document.getElementById('evaluationResult');
        const copyButton = document.getElementById('copyButton');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const comment = document.getElementById('comment').value;
            const context = document.getElementById('context').value;

            resultDiv.textContent = 'Evaluating...';
            resultDiv.style.display = 'block';
            copyButton.style.display = 'none';

            try {
                const res = await fetch('https://trueface-flask-app-1.onrender.com/evaluate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ comment, context })
                });

                const data = await res.json();
                if (data.evaluation) {
                    resultDiv.textContent = `Below is a TrueFace 2.0 evaluation of your comment.\n\nTrueFace is a nonpartisan AI model built to elevate public conversation through truth, logic, and human dignity. Grounded in classical reasoning, social psychology, ethical philosophy, and communication science.\n\nTrueFace evaluates public comments across five core categories—reasoning, tone, engagement, impact, and truth alignment. Each is rated from 0 to 5. A higher score reflects a greater contribution to truthful, respectful, and constructive dialogue across differences.\n\nLearn more or submit your own at: https://TrueFaceWorld.com\n\n${data.evaluation}`;
                    copyButton.style.display = 'inline-block';
                } else {
                    resultDiv.textContent = 'Error: ' + (data.error || 'Unexpected error.');
                }
            } catch (err) {
                resultDiv.textContent = 'Network error or backend unavailable.';
            }
        });

        copyButton.addEventListener('click', () => {
            navigator.clipboard.writeText(resultDiv.textContent).then(() => {
                alert('Evaluation copied to clipboard!');
            });
        });
    </script>
</body>
</html>
