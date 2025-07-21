from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import boto3
from datetime import datetime
import time

# === CONFIGURATION ===
bucket_name = 'automuse-output'
region = 'ap-south-1'
description = ["an ambient futuristic synthwave tune"]  # You can change this prompt
wait_time = 60 * 60  # 1 hour (change if needed)

def generate_and_upload():
    print("\n🎼 Starting new generation cycle...")

    # Load model
    model = MusicGen.get_pretrained('facebook/musicgen-small')
    model.set_generation_params(duration=10)

    # Generate music
    print("🎶 Generating music...")
    wav = model.generate(description)

    # Generate timestamp and file paths
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_basename = f"auto_track_{timestamp}"
    final_file = f"{file_basename}.wav"

    # Save locally
    audio_write(file_basename, wav[0].cpu(), model.sample_rate, strategy="loudness")
    print(f"✅ Music generated and saved: {final_file}")

    # Upload to S3
    try:
        print("☁ Uploading to S3...")
        s3 = boto3.client('s3', region_name=region)
        s3.upload_file(final_file, bucket_name, f"generated_tracks/{final_file}")
        print(f"✅ Uploaded to s3://{bucket_name}/generated_tracks/{final_file}")
        print(f"🔗 Public URL: https://{bucket_name}.s3.{region}.amazonaws.com/generated_tracks/{final_file}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

# === Main Loop ===
if __name__ == "__main__":
    while True:
        generate_and_upload()
        print(f"⏳ Waiting {wait_time//60} minutes for next cycle...")
        time.sleep(wait_time)
