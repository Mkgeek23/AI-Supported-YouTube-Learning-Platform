from flask import Flask, request, jsonify, render_template

from transcriber import transcribe_youtube_video
from modules import structure_transcript
from quizzes import get_quiz

app = Flask(__name__)


@app.route('/')
def index():
    # Using a video that's publicly available
    # Default video ID and start time
    default_video_id = "UEtBMyzLBFY"  # JetBrains AI CLub Intro as an example
    start_time = request.args.get('t', 0, type=int)
    return render_template('index.html', video_id=default_video_id, start_time=start_time)


@app.route('/modules', methods=['GET'])
def modules():
    try:
        video_id = request.args.get('video_id', '')
        if not video_id:
            return jsonify(error="Video ID is required"), 400

        video_transcript = transcribe_youtube_video(f'https://www.youtube.com/watch?v={video_id}')
        modules = structure_transcript(video_transcript)
        return jsonify(modules=modules)

    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/generate_quiz', methods=['GET'])
def generate_quiz():
    try:
        video_id = request.args.get('video_id', '')
        module_title = request.args.get('module_title', '')
        difficulty = request.args.get('difficulty', 'medium')

        if not video_id or not module_title:
            return jsonify(error="Both video_id and module_title are required"), 400

        quiz = get_quiz(video_id, module_title, difficulty)
        return jsonify(quiz=quiz)

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
