# ai_mate

A web application for communicating with OpenAI's API using voice messages. This project demonstrates a simple Python web app with voice message support, suitable for deployment on Google Cloud Run.

## Features
- Communicate with OpenAI API
- Voice message support
- Simple web interface

## Requirements
- Python 3.8+
- [OpenAI API key](https://platform.openai.com/)
- Google Cloud SDK (for deployment)

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
1. Set your OpenAI API key as an environment variable:
   ```sh
   $env:OPENAI_API_KEY="your-api-key"  # PowerShell
   # or
   export OPENAI_API_KEY="your-api-key" # Bash
   ```
2. Run the application locally:
   ```sh
   python main.py
   ```
3. Open your browser and go to `http://localhost:5000`.

## Deployment
To deploy on Google Cloud Run:
1. Make sure you are authenticated with Google Cloud and have set your project:
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