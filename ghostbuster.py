"""
Ghostbuster - A tool to detect fake job postings
"""
import sys
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import anthropic
from pydantic import BaseModel
from typing import List
import config
from datetime import datetime
import re
from urllib.parse import urlparse

# Permitted URL schemes and a blocklist of private/internal address prefixes
_ALLOWED_SCHEMES = {'http', 'https'}
_BLOCKED_HOSTS = {
    'localhost', '127.0.0.1', '0.0.0.0', '::1',
    '169.254.169.254',  # AWS/GCP/Azure instance metadata
    '100.100.100.200',  # Alibaba Cloud metadata
}


def _validate_url(url: str) -> str:
    """
    Validate that a URL is safe to fetch.
    Returns the (unchanged) URL on success, raises ValueError on failure.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("Invalid URL")

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme '{parsed.scheme}' is not allowed. Only http/https are permitted.")

    host = parsed.hostname or ""
    if host in _BLOCKED_HOSTS:
        raise ValueError(f"Requests to '{host}' are not permitted.")

    # Block private IPv4 ranges (10.x, 172.16-31.x, 192.168.x)
    import socket
    try:
        ip = socket.gethostbyname(host)
        parts = ip.split('.')
        if len(parts) == 4:
            a, b = int(parts[0]), int(parts[1])
            if (a == 10
                    or (a == 172 and 16 <= b <= 31)
                    or (a == 192 and b == 168)
                    or ip == '127.0.0.1'):
                raise ValueError("Requests to private/internal addresses are not permitted.")
    except socket.gaierror:
        pass  # Can't resolve — let requests handle it

    return url


class JobAnalysis(BaseModel):
    """Structured output from Claude's job legitimacy analysis."""
    score: int                      # 0–100 confidence this is a real job
    hiring_triggers: List[str]      # positive signals found
    concerns: List[str]             # red flags / negative signals
    reasoning: str                  # 2–3 sentence verdict explanation


class Ghostbuster:
    def __init__(self):
        """Initialize Ghostbuster with Perplexity (research) and Claude (analysis) clients."""
        if not config.PERPLEXITY_API_KEY or config.PERPLEXITY_API_KEY == 'your_api_key_here':
            raise ValueError("Perplexity API key is not configured. Add PERPLEXITY_API_KEY to your .env file.")
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key is not configured. Add ANTHROPIC_API_KEY to your .env file.")

        self.perplexity = OpenAI(
            api_key=config.PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai"
        )
        self.claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def scrape_job_posting(self, url):
        """
        Scrape job posting content from URL.
        Returns: dict with job details, or None on failure.
        """
        print(f"🔍 Scraping job posting from: {url}")

        try:
            # Validate URL before making any network request (SSRF prevention)
            _validate_url(url)

            headers = {'User-Agent': config.USER_AGENT}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)

            # Try to find job title
            title = soup.find('h1')
            job_title = title.get_text(strip=True) if title else "Unknown Title"

            # Try to find company name — fall back to page title then domain
            company_elem = soup.find('meta', property='og:site_name')
            if company_elem and company_elem.get('content'):
                company_name = company_elem['content']
            else:
                page_title = soup.find('title')
                if page_title:
                    company_name = page_title.get_text(strip=True)
                else:
                    parsed = urlparse(url)
                    company_name = parsed.hostname or "Unknown Company"

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

    # ------------------------------------------------------------------
    # Perplexity research
    # ------------------------------------------------------------------

    def _perplexity_search(self, query: str) -> str:
        """Run a single Perplexity web-search query and return the text result."""
        response = self.perplexity.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant with access to real-time web search. "
                        "Provide factual, concise answers citing specific facts, dates, and sources "
                        "where available. If you cannot find relevant information, say so clearly."
                    )
                },
                {"role": "user", "content": query}
            ],
            timeout=30
        )
        return response.choices[0].message.content

    def research_company(self, company_name: str, job_title: str) -> dict:
        """
        Run three targeted Perplexity searches to gather evidence on:
          1. Hiring trigger events (funding, contracts, expansion)
          2. Active hiring and growth signals (Glassdoor, LinkedIn, headcount)
          3. Negative signals (layoffs, downsizing, financial difficulties)

        Returns: dict with three research sections, or None on failure.
        """
        print(f"\n🔬 Researching {company_name} with Perplexity...")

        try:
            print("  Searching for hiring trigger events...")
            hiring_triggers = self._perplexity_search(
                f'Find recent (2023–2025) funding rounds, venture capital investment, IPO filings, '
                f'major new contracts, client wins, partnerships, or expansion announcements for '
                f'"{company_name}". What is their current funding stage and investor backing? '
                f'Include dates and amounts where available.'
            )

            print("  Searching for growth and hiring signals...")
            growth_signals = self._perplexity_search(
                f'What is the current employee headcount for "{company_name}" and are they actively '
                f'hiring? Search for recent Glassdoor reviews mentioning hiring pace, team growth, '
                f'or recruitment activity. Check LinkedIn for recent new hires in roles similar to '
                f'"{job_title}". Is there evidence of real people actually being hired there recently?'
            )

            print("  Searching for negative signals...")
            negative_signals = self._perplexity_search(
                f'Are there any reports of layoffs, downsizing, hiring freezes, financial difficulties, '
                f'bankruptcy filings, or company closure at "{company_name}" in the last 2 years? '
                f'Any news suggesting the company is struggling, contracting, or has paused hiring?'
            )

            print("✅ Company research complete")
            return {
                'company_name': company_name,
                'hiring_triggers': hiring_triggers,
                'growth_signals': growth_signals,
                'negative_signals': negative_signals,
                'researched_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error researching company: {e}")
            return None

    # ------------------------------------------------------------------
    # Claude analysis
    # ------------------------------------------------------------------

    def analyze_with_claude(self, job_data: dict, company_research: dict) -> JobAnalysis:
        """
        Send the job description and all Perplexity research to Claude Opus 4.6.
        Claude returns a structured JobAnalysis with a confidence score, hiring
        triggers found, concerns, and a reasoning paragraph.
        """
        print("\n🤖 Analyzing with Claude AI...")

        # Build the research block for Claude's context
        if company_research:
            research_block = (
                f"--- HIRING TRIGGER EVENTS (funding, contracts, expansion) ---\n"
                f"{company_research.get('hiring_triggers', 'No data available.')}\n\n"
                f"--- GROWTH & HIRING ACTIVITY (Glassdoor, LinkedIn, headcount) ---\n"
                f"{company_research.get('growth_signals', 'No data available.')}\n\n"
                f"--- NEGATIVE SIGNALS (layoffs, downsizing, financial difficulties) ---\n"
                f"{company_research.get('negative_signals', 'No data available.')}"
            )
        else:
            research_block = "No company research available."

        response = self.claude.messages.parse(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system="""You are an expert at identifying "ghost jobs" — job postings that companies post with no real intention of filling.

Ghost jobs are commonly posted to:
- Appear to be growing (for investor or board optics)
- Build a passive resume pipeline for future hypothetical roles
- Keep existing employees motivated or suppress salary negotiations
- Test market compensation benchmarks without real hiring intent

When assessing legitimacy, look for:

POSITIVE signals (real job indicators):
- Recent funding rounds, IPO, or major new contracts (companies that just raised money hire)
- Glassdoor or LinkedIn evidence of actual recent hires in similar roles
- Specific, detailed job description with clear team context and concrete responsibilities
- Salary range or compensation information included
- Company is in a known, verifiable growth phase

NEGATIVE signals (ghost job indicators):
- No recent funding, growth news, or hiring activity found anywhere online
- Glassdoor or LinkedIn shows stagnant or declining headcount
- Layoffs or downsizing reported in the last 12 months
- Extremely vague or generic job description with buzzwords but no substance
- No salary information provided
- Company is difficult to find credible information about
- The absence of any positive hiring signals is itself a red flag

Score from 0–100 where:
  100 = almost certainly a genuine open role actively being filled
    0 = almost certainly a ghost job with no real hiring intent

Be appropriately skeptical. Most job boards are flooded with ghost postings.""",
            messages=[{
                "role": "user",
                "content": (
                    f'Analyze this job posting for "{job_data.get("title", "Unknown Role")}" '
                    f'at "{job_data.get("company", "Unknown Company")}".\n\n'
                    f"--- JOB DESCRIPTION ---\n"
                    f"{job_data.get('full_text', 'No job description available.')}\n\n"
                    f"--- COMPANY RESEARCH ---\n"
                    f"{research_block}\n\n"
                    f"Assess the likelihood that this is a genuine open role vs. a ghost job. "
                    f"List the specific hiring triggers and concerns you found, then give your verdict."
                )
            }],
            output_format=JobAnalysis,
        )

        analysis = response.parsed_output
        print(f"  ✓ Analysis complete — confidence score: {analysis.score}/100")
        return analysis

    # ------------------------------------------------------------------
    # Report generation (CLI)
    # ------------------------------------------------------------------

    def generate_report(self, analysis: JobAnalysis, job_data: dict, company_research: dict):
        """Generate a human-readable CLI report."""
        print("\n" + "=" * 60)
        print("👻 GHOSTBUSTER REPORT")
        print("=" * 60)

        print(f"\n📋 Job Posting: {job_data['title']}")
        print(f"🏢 Company: {job_data['company']}")
        print(f"🔗 URL: {job_data['url']}")

        print(f"\n🎯 CONFIDENCE SCORE: {analysis.score}/100")

        if analysis.score >= config.CONFIDENCE_THRESHOLD_HIGH:
            verdict = "✅ LIKELY LEGITIMATE"
            emoji = "👍"
        elif analysis.score >= config.CONFIDENCE_THRESHOLD_LOW:
            verdict = "⚠️  PROCEED WITH CAUTION"
            emoji = "🤔"
        else:
            verdict = "🚨 LIKELY FAKE/GHOST JOB"
            emoji = "👻"

        print(f"{emoji} {verdict}")

        print(f"\n💡 Reasoning:\n  {analysis.reasoning}")

        if analysis.hiring_triggers:
            print("\n✅ Positive Signals Found:")
            for trigger in analysis.hiring_triggers:
                print(f"  + {trigger}")

        if analysis.concerns:
            print("\n⚠️  Concerns:")
            for concern in analysis.concerns:
                print(f"  - {concern}")

        if company_research:
            print("\n🔬 Research Summary (Perplexity):")
            print("-" * 60)
            print("Hiring Triggers:")
            print(company_research.get('hiring_triggers', '')[:400] + "...")
            print("\nGrowth Signals:")
            print(company_research.get('growth_signals', '')[:400] + "...")

        print("\n" + "=" * 60)

        return {
            'score': analysis.score,
            'verdict': verdict,
            'job': job_data,
            'company_research': company_research,
            'hiring_triggers': analysis.hiring_triggers,
            'concerns': analysis.concerns,
            'reasoning': analysis.reasoning,
        }

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------

    def analyze(self, job_url: str):
        """Main analysis function — orchestrates the entire pipeline."""
        print("=" * 60)
        print("👻 GHOSTBUSTER - Job Posting Analyzer")
        print("=" * 60)

        # Step 1: Scrape the job posting
        job_data = self.scrape_job_posting(job_url)
        if not job_data:
            print("❌ Could not analyze job posting")
            return None

        # Step 2: Research the company with Perplexity (3 targeted searches)
        company_research = self.research_company(job_data['company'], job_data['title'])

        # Step 3: Claude analyzes the job + research and produces a structured verdict
        analysis = self.analyze_with_claude(job_data, company_research)

        # Step 4: Generate report
        report = self.generate_report(analysis, job_data, company_research)

        return report


def main():
    """Main entry point for the script."""
    print("\n👻 Welcome to Ghostbuster!\n")

    if len(sys.argv) > 1:
        job_url = sys.argv[1]
    else:
        job_url = input("📎 Paste the job posting URL: ").strip()

    if not job_url:
        print("❌ No URL provided. Exiting.")
        return

    try:
        gb = Ghostbuster()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return

    report = gb.analyze(job_url)

    if report:
        print("\n✅ Analysis complete!")
    else:
        print("\n❌ Analysis failed.")


if __name__ == "__main__":
    main()
