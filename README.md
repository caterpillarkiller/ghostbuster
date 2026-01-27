# ghostbuster
A tool to verify the legitimacy of job postings

# 👻 Ghostbuster

A tool to detect fake and ghost job postings using AI-powered analysis.

## What is a Ghost Job?

According to Forbes, approximately 45% of job postings may be "ghost jobs" - positions that companies post with no intention of actually hiring. These fake postings are used to:
- Make investors think the company is growing
- Collect resumes for future use
- Test the job market
- Keep current employees motivated (by appearing busy/growing)

**Ghostbuster helps you identify these fake postings so you don't waste time applying.**

## How It Works

Ghostbuster analyzes job postings by:

1. **Scraping the job posting** - Extracts job title, company, and description
2. **Researching the company** - Uses Perplexity AI to find real-time info about company size, funding, hiring signals
3. **Detecting red flags** - Looks for suspicious patterns like generic language, missing salary, vague requirements
4. **Analyzing company fit** - Checks if the role makes sense for the company's stage and size
5. **Generating a confidence score** - Gives you a 0-100 score with detailed reasoning

## Installation

### Prerequisites
- Python 3.8+ (you have 3.9.6 ✅)
- Perplexity API key (get one at https://www.perplexity.ai/settings/api)

### Setup Steps

1. **Clone this repository**
   ```bash
   git clone https://github.com/yourusername/ghostbuster.git
   cd ghostbuster
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Perplexity API key**
   - Open the `.env` file
   - Replace `your_api_key_here` with your actual API key:
     ```
     PERPLEXITY_API_KEY=pplx-your-actual-key-here
     ```

## Usage

### Basic Usage

Run Ghostbuster with a job posting URL:

```bash
python ghostbuster.py
```

Then paste the URL when prompted.

### Command Line Usage

You can also pass the URL directly:

```bash
python ghostbuster.py "https://www.example.com/jobs/12345"
```

### Example Output

```
👻 GHOSTBUSTER REPORT
============================================================

📋 Job Posting: Senior Software Engineer
🏢 Company: TechCorp Inc
🔗 URL: https://example.com/jobs/12345

🎯 CONFIDENCE SCORE: 45/100
🚨 LIKELY FAKE/GHOST JOB

📝 Analysis Details:
  - No Salary: -5 points
  - Generic Description: -15 points
  - Company Size Mismatch: -20 points
  - Limited information about company: -25 points

🔬 Company Research Summary:
------------------------------------------------------------
TechCorp Inc is a small startup with 15 employees...
```

## Red Flags Detected

Ghostbuster looks for these warning signs:

- **Generic job descriptions** - Excessive buzzwords like "rockstar", "ninja", "fast-paced"
- **No salary information** - Legitimate companies usually provide salary ranges
- **Vague requirements** - Very short descriptions or unclear responsibilities  
- **Company research issues** - Can't find info about the company, or they're in trouble
- **Unrealistic requirements** - 10+ years experience for entry-level roles
- **Old postings** - Jobs that have been open for 30+ days

## Confidence Score Guide

- **75-100**: ✅ Likely legitimate - good to apply
- **40-74**: ⚠️ Proceed with caution - research more before applying
- **0-39**: 🚨 Likely fake/ghost job - probably not worth your time

## Configuration

You can adjust confidence thresholds in the `.env` file:

```
CONFIDENCE_THRESHOLD_HIGH=75
CONFIDENCE_THRESHOLD_LOW=40
```

## Limitations

- Web scraping may not work on all job sites (some block scrapers)
- Relies on Perplexity API for company research (costs ~$0.001 per analysis)
- Some legitimate jobs may trigger false positives
- Very new or stealth-mode companies may score lower

## Future Improvements

- [ ] Support for more job sites (LinkedIn, Indeed, Glassdoor)
- [ ] Track posting age automatically
- [ ] Compare multiple postings from same company
- [ ] Integration with job boards APIs
- [ ] Machine learning to improve detection over time
- [ ] Browser extension for instant analysis

## Contributing

This is a learning project! Contributions are welcome. Please open an issue or submit a PR.

## License

MIT License - feel free to use and modify!

## Disclaimer

Ghostbuster is a tool to help identify potential red flags. Always do your own research before deciding whether to apply for a job. A low score doesn't mean a job is definitely fake, and a high score doesn't guarantee it's legitimate.