"""
Ghostbuster - A tool to detect fake job postings
"""
import sys
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import config
from datetime import datetime
import re


class Ghostbuster:
    def __init__(self):
        """Initialize Ghostbuster with Perplexity API client"""
        if not config.PERPLEXITY_API_KEY or config.PERPLEXITY_API_KEY == 'your_api_key_here':
            print("⚠️  ERROR: Please add your Perplexity API key to the .env file")
            sys.exit(1)
        
        # Initialize Perplexity client
        self.client = OpenAI(
            api_key=config.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
    
    def scrape_job_posting(self, url):
        """
        Scrape job posting content from URL
        Returns: dict with job details
        """
        print(f"🔍 Scraping job posting from: {url}")
        
        try:
            headers = {'User-Agent': config.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Extract text content (this is a simple version - we'll improve it)
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Try to find job title
            title = soup.find('h1')
            job_title = title.get_text(strip=True) if title else "Unknown Title"
            
            # Try to find company name
            company_elem = soup.find('meta', property='og:site_name')
            company_name = company_elem['content'] if company_elem else "Unknown Company"
            
            job_data = {
                'url': url,
                'title': job_title,
                'company': company_name,
                'full_text': text_content[:5000],  # Limit to first 5000 chars
                'scraped_at': datetime.now().isoformat()
            }
            
            print(f"✅ Found job: {job_title} at {company_name}")
            return job_data
            
        except Exception as e:
            print(f"❌ Error scraping job posting: {e}")
            return None
    
    def research_company(self, company_name, job_title):
        """
        Use Perplexity to research the company
        Returns: dict with company insights
        """
        print(f"\n🔬 Researching {company_name}...")
        
        try:
            # Create a research query for Perplexity
            query = f"""Research the company "{company_name}" and provide:
1. Company size (number of employees)
2. Funding stage and recent funding rounds
3. Industry and what they do
4. Recent news about hiring or layoffs
5. Growth signals (expanding, stable, or contracting)
6. Whether they're actively hiring for roles like "{job_title}"

Please be concise and factual."""
            
            # Call Perplexity API
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that provides factual, concise company information."},
                    {"role": "user", "content": query}
                ]
            )
            
            research_results = response.choices[0].message.content
            print(f"✅ Research complete")
            
            return {
                'company_name': company_name,
                'research': research_results,
                'researched_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error researching company: {e}")
            return None
    
    def analyze_job_description(self, job_text):
        """
        Analyze the job description for red flags
        Returns: dict with red flags found
        """
        print("\n🔍 Analyzing job description for red flags...")
        
        red_flags = {}
        
        # Check for generic/vague language
        generic_phrases = [
            'fast-paced environment',
            'wear many hats',
            'self-starter',
            'dynamic team',
            'rockstar',
            'ninja',
            'guru'
        ]
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in job_text.lower())
        if generic_count >= 3:
            red_flags['generic_description'] = True
        
        # Check for salary mention
        salary_keywords = ['salary', '$', 'compensation', 'pay range', 'k/year', 'per hour']
        has_salary = any(keyword in job_text.lower() for keyword in salary_keywords)
        if not has_salary:
            red_flags['no_salary'] = True
        
        # Check for vague requirements
        if len(job_text) < 500:
            red_flags['vague_requirements'] = True
        
        # Check for unrealistic requirements
        years_experience = re.findall(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', job_text.lower())
        if years_experience and any(int(years) > 10 for years in years_experience):
            red_flags['unrealistic_requirements'] = True
        
        print(f"⚠️  Found {len(red_flags)} red flags in job description")
        return red_flags
    
    def calculate_confidence_score(self, job_data, company_research, red_flags):
        """
        Calculate confidence score that this is a real job
        Returns: int (0-100)
        """
        print("\n📊 Calculating confidence score...")
        
        # Start with base score of 100 (assume legitimate)
        score = 100
        reasons = []
        
        # Deduct points for each red flag
        for flag, value in red_flags.items():
            if value and flag in config.RED_FLAG_WEIGHTS:
                deduction = config.RED_FLAG_WEIGHTS[flag] * 5
                score -= deduction
                reasons.append(f"- {flag.replace('_', ' ').title()}: -{deduction} points")
        
        # Use Perplexity research to adjust score
        if company_research:
            research_text = company_research['research'].lower()
            
            # Positive signals
            if any(word in research_text for word in ['hiring', 'expanding', 'growth', 'funding']):
                score += 10
                reasons.append("+ Company shows growth signals: +10 points")
            
            # Negative signals
            if any(word in research_text for word in ['layoffs', 'downsizing', 'closing']):
                score -= 20
                reasons.append("- Company has negative signals (layoffs/downsizing): -20 points")
            
            # Can't find much info about company
            if 'no information' in research_text or 'unable to find' in research_text or len(research_text) < 100:
                score -= 25
                reasons.append("- Limited information about company: -25 points")
        
        # Ensure score stays within 0-100 range
        score = max(0, min(100, score))
        
        return score, reasons
    
    def generate_report(self, score, reasons, job_data, company_research):
        """
        Generate a human-readable report
        """
        print("\n" + "="*60)
        print("👻 GHOSTBUSTER REPORT")
        print("="*60)
        
        print(f"\n📋 Job Posting: {job_data['title']}")
        print(f"🏢 Company: {job_data['company']}")
        print(f"🔗 URL: {job_data['url']}")
        
        print(f"\n🎯 CONFIDENCE SCORE: {score}/100")
        
        # Interpret the score
        if score >= config.CONFIDENCE_THRESHOLD_HIGH:
            verdict = "✅ LIKELY LEGITIMATE"
            emoji = "👍"
        elif score >= config.CONFIDENCE_THRESHOLD_LOW:
            verdict = "⚠️  PROCEED WITH CAUTION"
            emoji = "🤔"
        else:
            verdict = "🚨 LIKELY FAKE/GHOST JOB"
            emoji = "👻"
        
        print(f"{emoji} {verdict}")
        
        print("\n📝 Analysis Details:")
        for reason in reasons:
            print(f"  {reason}")
        
        if company_research:
            print("\n🔬 Company Research Summary:")
            print("-" * 60)
            # Show first 500 chars of research
            print(company_research['research'][:500] + "...")
        
        print("\n" + "="*60)
        
        return {
            'score': score,
            'verdict': verdict,
            'job': job_data,
            'research': company_research,
            'reasons': reasons
        }
    
    def analyze(self, job_url):
        """
        Main analysis function - orchestrates the entire process
        """
        print("="*60)
        print("👻 GHOSTBUSTER - Job Posting Analyzer")
        print("="*60)
        
        # Step 1: Scrape the job posting
        job_data = self.scrape_job_posting(job_url)
        if not job_data:
            print("❌ Could not analyze job posting")
            return None
        
        # Step 2: Research the company
        company_research = self.research_company(job_data['company'], job_data['title'])
        
        # Step 3: Analyze job description
        red_flags = self.analyze_job_description(job_data['full_text'])
        
        # Step 4: Calculate confidence score
        score, reasons = self.calculate_confidence_score(job_data, company_research, red_flags)
        
        # Step 5: Generate report
        report = self.generate_report(score, reasons, job_data, company_research)
        
        return report


def main():
    """Main entry point for the script"""
    print("\n👻 Welcome to Ghostbuster!\n")
    
    # Get job URL from user
    if len(sys.argv) > 1:
        job_url = sys.argv[1]
    else:
        job_url = input("📎 Paste the job posting URL: ").strip()
    
    if not job_url:
        print("❌ No URL provided. Exiting.")
        return
    
    # Create Ghostbuster instance and analyze
    gb = Ghostbuster()
    report = gb.analyze(job_url)
    
    if report:
        print("\n✅ Analysis complete!")
    else:
        print("\n❌ Analysis failed.")


if __name__ == "__main__":
    main()