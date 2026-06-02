from flask import Flask, request, jsonify

from AgentsForSoftwareDevelopment.QuizzesGenerator.task import get_quiz
from AIDevTools.YouTubeVideoPlayer.main import index
from AgentsForSoftwareDevelopment.AddModules.task import modules

app = Flask(__name__)

app.add_url_rule('/', 'index', index)
app.add_url_rule('/modules', 'modules', modules)


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
