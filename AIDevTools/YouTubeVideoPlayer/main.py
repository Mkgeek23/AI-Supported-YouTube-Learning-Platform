from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    # Using a video that's publicly available
    # Default video ID and start time
    default_video_id = "UEtBMyzLBFY"
    start_time = request.args.get('t', 0, type=int)
    return render_template('index.html', video_id=default_video_id, start_time=start_time)


@app.route('/watch')
def watch():
    video_id = request.args.get('v', '')
    start_time = request.args.get('t', 0, type=int)
    return render_template('index.html', video_id=video_id, start_time=start_time)


if __name__ == '__main__':
    app.run(debug=True)
