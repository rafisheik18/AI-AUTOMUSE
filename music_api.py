from flask import Flask, request, jsonify
from flask_cors import CORS
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import boto3
import os
import torch
import re

# === Configuration ===
bucket_name = 'automuse-output'
region = 'ap-south-1'
output_dir = 'outputs'
duration_seconds = 20  # ⏱ Fixed duration

os.makedirs(output_dir, exist_ok=True)

# === Initialize App ===
app = Flask(__name__)
CORS(app)

# === Load MusicGen model once ===
print("📦 Loading MusicGen model...")
model = MusicGen.get_pretrained('facebook/musicgen-small')
model.set_generation_params(duration=duration_seconds)

# === Helper: Sanitize filename ===
def sanitize_filename(text):
    sanitized = re.sub(r'[^a-zA-Z0-9-_]+', '-', text.lower()).strip('-')
    return sanitized or "track"

# === Helper: Check if object exists in S3 ===
def s3_key_exists(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False

# === POST /generate ===
@app.route('/generate', methods=['POST'])
def generate_music():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "ai ambient space track")

        print(f"🎶 Prompt: {prompt}")

        # Set duration and generate
        model.set_generation_params(duration=duration_seconds)
        wav = model.generate([prompt])

        # Sanitize filename
        base_name = sanitize_filename(prompt)
        filename = base_name + ".wav"
        s3_key = f"generated_tracks/{filename}"
        local_path = os.path.join(output_dir, filename)

        # Avoid S3 overwrite by adding -2, -3, etc. if file exists
        s3 = boto3.client('s3', region_name=region)
        counter = 2
        while s3_key_exists(s3, bucket_name, s3_key):
            filename = f"{base_name}-{counter}.wav"
            s3_key = f"generated_tracks/{filename}"
            local_path = os.path.join(output_dir, filename)
            counter += 1

        # Save audio locally
        audio_write(local_path.replace('.wav', ''), wav[0].cpu(), model.sample_rate, strategy="loudness")
        print(f"✅ Saved to: {local_path}")

        # Upload to S3
        s3.upload_file(local_path, bucket_name, s3_key)
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        print(f"☁ Uploaded to: {url}")

        return jsonify({"status": "success", "url": url})

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# === GET /list ===
@app.route('/list', methods=['GET'])
def list_music():
    try:
        s3 = boto3.client('s3', region_name=region)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix="generated_tracks/")

        tracks = []
        for obj in response.get('Contents', []):
            key = obj['Key']
            if key.endswith('.wav'):
                url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
                tracks.append(url)

        return jsonify({"tracks": tracks})

    except Exception as e:
        print(f"❌ List error: {e}")
        return jsonify({"error": str(e)}), 500

# === Run server ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
