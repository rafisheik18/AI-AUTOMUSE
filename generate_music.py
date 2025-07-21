from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import boto3
from datetime import datetime
import os
import re

# === Configuration ===
bucket_name = 'automuse-output'
region = 'ap-south-1'
output_dir = 'outputs'
os.makedirs(output_dir, exist_ok=True)

# === Prompt ===
prompt = "ambient futuristic synthwave tune"

# === Helpers ===
def sanitize_filename(text):
    sanitized = re.sub(r'[^a-zA-Z0-9-_]+', '-', text.lower()).strip('-')
    return sanitized or "track"

def s3_key_exists(s3, bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False

# === Load Model ===
model = MusicGen.get_pretrained('facebook/musicgen-small')
model.set_generation_params(duration=20)

# === Generate ===
print(f"🎶 Generating music for prompt: '{prompt}'")
wav = model.generate([prompt])

# === Filename logic ===
s3 = boto3.client('s3', region_name=region)
base_name = sanitize_filename(prompt)
filename = base_name + ".wav"
s3_key = f"generated_tracks/{filename}"
local_path = os.path.join(output_dir, filename)

counter = 2
while s3_key_exists(s3, bucket_name, s3_key):
    filename = f"{base_name}-{counter}.wav"
    s3_key = f"generated_tracks/{filename}"
    local_path = os.path.join(output_dir, filename)
    counter += 1

# === Save locally ===
audio_write(local_path.replace('.wav', ''), wav[0].cpu(), model.sample_rate, strategy="loudness")
print(f"✅ Saved locally to {local_path}")

# === Upload to S3 ===
try:
    print(f"☁ Uploading to S3...")
    s3.upload_file(local_path, bucket_name, s3_key)
    print(f"✅ Uploaded: s3://{bucket_name}/{s3_key}")
    print(f"🔗 Public URL: https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}")
except Exception as e:
    print(f"❌ Upload failed: {e}")
