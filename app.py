from flask import Flask, request, redirect, render_template, send_file
import zipfile
import numpy as np
import concurrent.futures
from pytube import YouTube
from pydub import AudioSegment
from pydub.utils import make_chunks
import os
from youtube_search import YoutubeSearch
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        singer = request.form['singer']
        Number_vid = int(request.form['Number_vid'])
        duration = int(request.form['duration'])
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(process_audio, singer, Number_vid, duration)

        return redirect("/success")
    return render_template('index.html')

def process_audio(singer, Number_vid, duration):
    results1 = YoutubeSearch(singer, max_results=Number_vid).to_dict()
    data = pd.DataFrame(results1)
    for i in range(1, (data['url_suffix'].count())):
        data['url_suffix'][i] = "https://www.youtube.com" + data['url_suffix'][i]
    links = data['url_suffix']
    for i in links:
        yt = YouTube(i, use_oauth=True, allow_oauth_cache=True)
        video = yt.streams.filter(file_extension='mp4', only_audio=True).first()
        out_file = video.download()
        base, ext = os.path.splitext(out_file)
        new_file = base + '.mp4'
        os.rename(out_file, new_file)
    audio_files = []
    for file in os.listdir():
        if file.endswith(".mp4"):
            audio = AudioSegment.from_file(file, "mp4")
            audio_file = file.replace(".mp4", ".wav")
            audio.export(audio_file, format="wav")
            audio_files.append(audio_file)
    chunks = []
    for audio_file in audio_files:
        chunk = make_chunks(AudioSegment.from_file(audio_file, format="wav"), chunk_length=duration * 1000)
        id = np.random.randint(0, len(chunk))
        chunk = chunk[id]
        chunks.append(chunk)
    merged = AudioSegment.empty()
    for chunk in chunks:
        merged += chunk
    merged.export('output.mp3', format="mp3")
    dir = os.getcwd()
    print(dir)
    test = os.listdir(dir)
    zip_file_path = "/opt/render/project/src/output.zip"
    for item in test:
        if item.endswith(".mp4") or item.endswith(".wav"):
            os.remove(os.path.join(dir, item))
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        zipf.write('output.mp3')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/download')
def download():
    zip_path = "/opt/render/project/src/output.zip"
    return send_file(zip_path, as_attachment=True)
if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=5000)
