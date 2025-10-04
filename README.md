# 🎵🔐 AudioStego Web App

## 📖 Description

A **web-based application** for **audio steganography on MP3 files** that supports both **embedding** and **extraction** of hidden messages. It combines the **n-LSB method** with an **Extended Vigenère Cipher** for secure and imperceptible data hiding.

### 🛠️ How It Works

This project takes advantage of the **MP3 compression structure**:

* 🎼 MP3 uses **Huffman encoding** to compress audio.
* ➕ The **sign bit** of the Huffman-encoded bitstream is stored separately and doesn’t affect sound perception much.
* 🕵️ Secret data is hidden inside these **sign bits**.
* 🎚️ To reduce audible changes, only bits from louder sounds are used — controlled by a **`mask_percentile` parameter**, detected from `global_gain` in MP3 metadata.
* 🔑 Before embedding, the secret message is **encrypted with an Extended Vigenère Cipher**, where the **key** also determines **deterministic positions** in each frame for embedding.

✨ Result: secure, hard-to-detect, and high-quality audio steganography.

---

## 🖥️ Tech Stack

* ⚛️ **Frontend**: HTML + CSS + Javascript with React.JS and Tailwind CSS Framework
* 🐍 **Backend**: Python powered with Flask Framework
* 📦 **Containerization**: Docker

---

## 📦 Dependencies

### Backend

* 🐍 Python 3.10+
* 🌐 Flask
* 🎶 pydub
* 🔢 numpy
* 🎼 mutagen
* ⚙️ ffmpeg

### Frontend

* 🟩 Node.js 18+
* ⚛️ React 18+

### Containerization

* 🐳 Docker Engine
* ⚙️ Docker Compose

---

## 🚀 How to Run

### 🐳 Using Docker (Recommended)

1. Clone the repository:

   ```bash
   git clone https://github.com/abdulrafirh/Tucil2-IF4020
   cd src
   ```
2. Build and run with Docker Compose:

   ```bash
   docker-compose up --build
   ```
3. Open the app in your browser 🌐:

   ```
   http://localhost:5173
   ```

---

### 🛠️ Manual Setup

#### Backend

1. Go to the backend directory:

   ```bash
   cd src/backend
   ```
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask server:

   ```bash
   flask run
   ```

#### Frontend

1. Go to the frontend directory:

   ```bash
   cd src/frontend
   ```
2. Install dependencies:

   ```bash
   npm install
   ```
3. Start the development server:

   ```bash
   npm run dev
   ```
4. Open the app in your browser 🌐:

   ```
   http://localhost:5173
   ```

Perfect 👍 Adding an **Authors** section with a table makes the README more polished. Here’s the updated snippet to extend your README (with emojis and a nice format):

---

## 👥 Authors

| Name                | NIM                                       | Role               |
| ------------------- | -------------------------------------------- | ------------------ |
| Farhan Nafis Rayhan | 13522037 | Frontend, Documentation, and Researching for Steganography Methods |
| Abdul Rafi Radityo Hutomo | 13522089 | Backend and Steganography Implementation |