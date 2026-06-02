from flask import Flask, request, jsonify

from AgentsForSoftwareDevelopment.CreateModules.task import structure_transcript
from AIDevTools.YouTubeVideoPlayer.main import index
from AIDevTools.Video2Transcript.task import transcribe_youtube_video

app = Flask(__name__)

app.add_url_rule('/', 'index', index)

@app.route('/modules', methods=['GET'])
def modules():
    try:
        video_id = request.args.get('video_id', '')
        if not video_id:
            return jsonify(error="Video ID is required"), 400

        video_transcript = transcribe_youtube_video(f'https://www.youtube.com/watch?v={video_id}')
        modules = None # TODO: call structure_transcript function
        return jsonify(modules=modules)

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
