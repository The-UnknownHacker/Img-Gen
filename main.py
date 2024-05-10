from PIL import Image, UnidentifiedImageError
from flask import Flask, render_template, request, send_file
import requests
import os
import tempfile
import io

app = Flask(__name__)


API_URL = "https://frightened-dove-turtleneck-shirt.cyclic.app/proxy/https://api-inference.huggingface.co/models/prompthero/openjourney"
HEADERS = {"Authorization": "Bearer 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"}

def query(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.content

@app.route('/', methods=['GET', 'POST'])
def generate_image():
    if request.method == 'POST':
        input_prompt = request.form.get("prompt")

        if not input_prompt:
            return "No prompt provided", 400

        try:
            image_bytes = query({"inputs": input_prompt})
            image = Image.open(io.BytesIO(image_bytes))

            img_dir = os.path.join(app.root_path, 'image')
            os.makedirs(img_dir, exist_ok=True)

            fd, temp_file_path = tempfile.mkstemp(suffix='.png', dir=img_dir)
            os.close(fd)

            image.save(temp_file_path, format='PNG')

            relative_path = os.path.relpath(temp_file_path, start=app.root_path)

            return send_file(relative_path, mimetype='image/png')

        except UnidentifiedImageError:
            error_message = "Sorry, we couldn't generate the image. Please try again later."
            return render_template("index.html", error_message=error_message)

        except requests.exceptions.RequestException as e:
            error_message = "Sorry, we couldn't generate the image. Please try again later."
            return render_template("index.html", error_message=error_message)

    else:
        return render_template('index.html')
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=5000, use_reloader=True) # Make it so if any error occurs it should restart
