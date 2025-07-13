# VideoVault

VideoVault is a full-stack desktop application for Windows, macOS, and Linux that allows you to securely embed and extract files within video containers. It's built with a modern Electron.js frontend for a user-friendly interface and a powerful Python backend to handle all file processing and video manipulation. The project offers three distinct methods for data concealment: a fast "Append" method that attaches a password-protected archive to a video, a classic "Steganography (LSB)" method that hides data in the pixel information of video frames, and a unique "Data-Reel" method that converts files into a brand new, self-contained data-video. This tool provides a complete encode/decode cycle, enabling users to both hide and recover their data seamlessly.

---

# ✨ Core Features

- Multi-Method Concealment: Choose from three different techniques to hide your data.
- Full Encode/Decode Cycle: Securely encode files and easily decode them back to their original form.
- Password Protection: Encrypt your hidden data with a user-provided password.
- Cross-Platform: Built with Electron, the application can be packaged for major desktop operating systems.

---

# 🛠️ Tech Stack & Architecture

- Frontend: [Electron.js](https://www.electronjs.org/) (Plain HTML, CSS, JavaScript)
- Backend: [Python](https://www.python.org/)
- Core Libraries: [OpenCV](https://opencv.org/), [NumPy](https://numpy.org/)
- Packaging: [Electron Forge](https://www.electronforge.io/) & [PyInstaller](https://pyinstaller.org/)

---

# 🚀 Getting Started

Prerequisites: Node.js, npm, and Python must be installed.

1.  Clone & Navigate:
    ```sh
    git clone https://github.com/YourUsername/VideoVault.git
    cd VideoVault
    ```
2.  Install Dependencies:
    ```sh
    # Install Node.js packages
    npm install

    # Set up Python virtual environment and install packages
    python -m venv venv
    # Windows: .\venv\Scripts\activate | macOS/Linux: source venv/bin/activate
    pip install -r backend/requirements.txt
    ```
3.  Run in Development Mode:
    ```sh
    npm start
    ```

---

# 📦 Building the Application

To create a distributable package:

1.  Bundle the Python Backend:
    ```sh
    pyinstaller --onefile --noconsole --name engine backend/engine.py
    ```
    Then, copy the generated executable from `dist/` into the `backend/` folder.

2.  Build the Electron App:
    ```sh
    npm run make
    ```
    The final application will be in the `out/` directory.

---

# 🚧 Project Status & Future Goals

This project is currently under active development. The core encoding and decoding functionalities are implemented but may contain bugs (notably within the Steganography method). The primary focus is on stabilizing these features before moving forward.

Future roadmap includes several exciting enhancements:

- Bug Fixes: Resolve all known issues with the existing encoding/decoding methods to ensure 100% reliability along with issues with passowrd protecting files.
- Gemini API Integration:
  - AI Password Muse: Add a feature to generate secure, memorable passwords for the user. Feature added but isn't working
  - Smart Manifest: Automatically generate a text summary of the hidden files, allowing a user to "peek inside" a video without a full decode.
  - Steganography Analyzer: Use Gemini Vision to analyze a carrier video's suitability for hiding data.
- Enhanced UI/UX: Improve user feedback, add a dedicated settings page, and refine the overall user experience.