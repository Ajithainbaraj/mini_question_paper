# Question Paper Generator

A web-based application for generating customized question papers using AI. Supports both university exam formats and competitive exam preparation (NEET/JEE style).

## Features

### 📚 University Question Papers
- Generate MCQs, short answer, and long answer questions
- Support for different subjects, semesters, and exam types
- Bloom's taxonomy integration for question classification
- PDF export with proper formatting
- Answer key generation

### 🏆 Competitive Exam Preparation
- NEET/JEE style question generation
- Topic analysis and concept identification
- Comprehensive question sets with explanations
- Subject-wise question banks

### 📄 Document Processing
- Upload and process multiple file formats:
  - PDF files
  - Word documents (.docx)
  - Text files (.txt)
- Automatic text extraction and content analysis

### 🎯 AI-Powered Generation
- Uses Google's Gemini 2.5 Flash model
- Intelligent question generation based on content
- Customizable question parameters

## Tech Stack

- **Backend**: Python Flask
- **AI**: Google Generative AI (Gemini)
- **PDF Generation**: ReportLab
- **Document Processing**: PyPDF2, python-docx
- **Frontend**: HTML, CSS, Jinja2 templates

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ajithainbaraj/mini_question_paper.git
   cd mini_question_paper
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   Navigate to `http://localhost:5000`

## Usage

### University Question Papers
1. Upload syllabus documents (PDF, DOCX, or TXT)
2. Enter college, subject, semester, and exam details
3. Configure question parameters (number of questions, Bloom's levels)
4. Generate and download PDF question paper

### Competitive Exams
1. Select competitive exam mode
2. Enter subject and topics
3. Generate comprehensive question sets
4. Review with answer explanations

## Project Structure

```
├── app.py                 # Main Flask application
├── question_generator.py  # AI question generation logic
├── utils.py              # Helper functions
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── static/
│   └── style.css         # CSS styles
├── templates/
│   ├── index.html        # Home page
│   ├── result.html       # Results page
│   ├── competitive.html  # Competitive exam interface
│   └── competitive_result.html  # Competitive results
├── uploads/              # Uploaded files directory
├── papers/               # Generated papers directory
└── test_gemini.py        # API testing script
```

## API Configuration

The application uses Google's Gemini AI API. To get an API key:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file as `GEMINI_API_KEY`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to use and modify as needed.

## Support

For issues or questions, please create an issue in the GitHub repository.