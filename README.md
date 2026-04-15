# ✨ AI Mate

A modern, ultra-low latency web application for conversational AI via voice. AI Mate uses the GPT-5.4 family to allow real-time conversational STT/TTS (Speech-to-Text & Text-to-Speech), backed by a beautiful Glassmorphic frontend and a powerful Streamlit Admin Dashboard for persona management and history viewing.

## Core Features
1. **Ultra-Low Latency Streaming**: Text is streamed directly from the `gpt-5.4-mini` model, chunked, and synthesized into MP3 bytes on the fly. The browser natively plays this HTTP stream without waiting for the full generation payload.
2. **Glassmorphic Web Interface**: A premium dark-mode graphic UI featuring intuitive Push-To-Talk micro-animations. 
3. **Voice Style Selection**: Dynamically switch your AI Mate's voice with a UI dropdown supporting the full lineup of 13 built-in OpenAI TTS voices (Alloy, Nova, Echo, Shimmer, etc.).
4. **Animated AI Avatar**: Features a beautiful 2D digital avatar that automatically synchronizes its mouth movements and body bobbing to the generated speech audio stream in real-time.
5. **Streamlit Admin Dashboard**: Launch a dedicated internal dashboard (`/run_streamlit`) to visualize chat logs stored in Google BigQuery, manage your AI's persona parameters (`persona.json`), and clear histories dynamically.
6. **Cloud Run Ready**: Built on Flask and ready for highly scalable container deployments.

## Requirements
- Python 3.8+
- [OpenAI API key](https://platform.openai.com/)
- Google Cloud SDK (for BigQuery logs and Cloud Run deployment)

## Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/yourusername/ai_mate.git
   cd ai_mate
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Set your OpenAI token as an environment variable (note: the code expects `OPENAI_TOKEN`):
   ```sh
   $env:OPENAI_TOKEN="your-api-key"   # PowerShell
   # or
   export OPENAI_TOKEN="your-api-key" # Bash/Zsh
   ```

2. Run the Flask application locally:
   ```sh
   python main.py
   ```

3. Open your browser and go to `http://localhost:8080`.

4. **(Optional)** Open the Streamlit Admin dashboard by clicking the `Admin` gear icon in the footer, or navigating directly to `http://localhost:8501`.

## Deployment

To deploy on Google Cloud Run:

1. Make sure you are authenticated with Google Cloud and have set your project (this is also required for the BigQuery logger):
   ```sh
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. Deploy using the following command (replace parameters as needed):
   ```sh
   gcloud run deploy ai-mate --allow-unauthenticated --region=asia-northeast1 --project=YOUR_PROJECT_ID --source .
   ```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.