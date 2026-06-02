from flask import Flask, request, jsonify

from AIDevTools.YouTubeVideoPlayer.main import index
from AIDevTools.Video2Transcript.task import transcribe_youtube_video

app = Flask(__name__)

app.add_url_rule('/', 'index', index)

@app.route('/transcription', methods=['GET'])
def transcription():
    try:
        video_id = request.args.get('video_id', '')
        video_transcript = transcribe_youtube_video(video_id)

        if video_transcript is None:
            return jsonify(error="Failed to transcribe video"), 500

        transcript_data = video_transcript.get('transcript') if video_transcript else None
        if transcript_data is None:
            return jsonify(error="Invalid transcript format"), 500

        return jsonify(transcription=transcript_data)

    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
