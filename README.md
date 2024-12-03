# ImgGenAPI

A Flask-based AI image generation application using Stable Diffusion XL.

## Features

- Generate AI images with custom prompts
- Choose image size and number of images
- View recent generations
- Download generated images
- Responsive UI with loading states
- Image history storage

## Getting Started

To use this project, follow these steps:

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```
4. Access the Application:
   Open a web browser and go to http://localhost:8080

## Requirements

Create a requirements.txt file with:
- Flask
- Pillow
- requests
- sqlite3

## Configuration

The application uses SQLite for storing image history and Flask's static folder for storing generated images.

Enjoy generating images with ImgGenAPI!
