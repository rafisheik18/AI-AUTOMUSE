import time
import subprocess

print("🔁 AI Music Auto Generator Started")
while True:
    print("\n🎼 Starting new generation cycle...")

    try:
        subprocess.run(["python", "generate_music.py"], check=True)
        subprocess.run(["python", "upload_to_s3.py"], check=True)
        print("✅ Cycle done. Waiting 1 hour...\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during execution: {e}")

    time.sleep(3600)  # 1 hour delay
