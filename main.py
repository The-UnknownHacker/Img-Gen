import requests
import io
from PIL import Image, UnidentifiedImageError
from flask import Flask, render_template, request, send_file, jsonify, url_for
import os
import tempfile
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Configuration
API_URL = "https://ghostunblocker.vercel.app//proxy/https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": "Bearer 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"}

# Initialize database
def init_db():
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  prompt TEXT,
                  filepath TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def query(payload):
    try:
        # Increase timeout to 180 seconds (3 minutes)
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=180)
        return response.content
    except requests.exceptions.Timeout:
        raise Exception("Image generation timed out. The server is probably busy, please try again.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")

@app.route("/", methods=["GET"])
def home():
    # Get recent images from database
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute("SELECT * FROM images ORDER BY created_at DESC LIMIT 8")
    recent_images = c.fetchall()
    conn.close()
    return render_template("index.html", recent_images=recent_images)

@app.route("/generate", methods=["POST"])
def generate():
    input_prompt = request.form.get("prompt")
    size = request.form.get("size", "512x512")
    num_images = min(int(request.form.get("num_images", 1)), 4)
    
    # Get additional parameters from form
    num_inference_steps = int(request.form.get("num_inference_steps", 30))
    guidance_scale = float(request.form.get("guidance_scale", 7.5))
    negative_prompt = request.form.get("negative_prompt", "blurry, bad quality, worst quality, low quality")

    if not input_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        width, height = map(int, size.split('x'))
        payload = {
            "inputs": input_prompt,
            "parameters": {
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "negative_prompt": negative_prompt,
                "num_outputs": num_images,
                "return_full_object": False
            }
        }

        # Get the response from the API
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=180)
        
        # Handle various error cases
        if response.status_code == 401:
            return jsonify({"error": "API Authorization failed. Please check your API token."}), 401
        elif response.status_code == 403:
            return jsonify({"error": "API access forbidden. Please verify your API token has correct permissions."}), 403
        elif response.status_code == 504:
            return jsonify({"error": "The request timed out. The server might be busy, please try again."}), 504
        elif response.status_code != 200:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_msg = response.json().get('error', error_msg)
            except:
                pass
            return jsonify({"error": error_msg}), response.status_code

        # Verify we got image data
        image_bytes = response.content
        if len(image_bytes) == 0:
            return jsonify({"error": "Received empty response from API"}), 500

        # Try to open the image data
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except UnidentifiedImageError:
            # If we can't open it as an image, try to get error message from response
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Invalid image data received')
            except:
                error_msg = 'Invalid image data received'
            return jsonify({"error": error_msg}), 500

        # Save image
        img_dir = os.path.join(app.static_folder, 'generated')
        os.makedirs(img_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.png"
        filepath = os.path.join(img_dir, filename)
        image.save(filepath, format='PNG')

        # Save to database
        conn = sqlite3.connect('images.db')
        c = conn.cursor()
        c.execute("INSERT INTO images (prompt, filepath) VALUES (?, ?)",
                 (input_prompt, f"generated/{filename}"))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "image_url": url_for('static', filename=f'generated/{filename}'),
            "prompt": input_prompt
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=8080)
