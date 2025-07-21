import boto3
import os
import re

# === Configuration ===
bucket_name = 'automuse-output'
region = 'ap-south-1'
output_dir = 'outputs'
s3 = boto3.client('s3', region_name=region)

# === Helpers ===
def s3_key_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False

# === Get latest .wav file ===
files = [f for f in os.listdir(output_dir) if f.endswith(".wav")]
if not files:
    print("❌ No .wav files found in outputs/")
    exit()

latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(output_dir, f)))
base_name = os.path.splitext(latest_file)[0]
sanitized_base = re.sub(r'[^a-zA-Z0-9-_]+', '-', base_name.lower()).strip('-')

filename = sanitized_base + ".wav"
s3_key = f"generated_tracks/{filename}"
local_path = os.path.join(output_dir, latest_file)

# === Avoid S3 overwrite ===
counter = 2
while s3_key_exists(bucket_name, s3_key):
    filename = f"{sanitized_base}-{counter}.wav"
    s3_key = f"generated_tracks/{filename}"
    counter += 1

# === Upload ===
print(f"☁ Uploading {latest_file} as {filename}...")
s3.upload_file(local_path, bucket_name, s3_key)
print(f"✅ Uploaded to s3://{bucket_name}/{s3_key}")
print(f"🔗 Public URL: https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}")
