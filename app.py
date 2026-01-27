"""
Ghostbuster Web Interface
A Streamlit app for detecting fake job postings
"""
import streamlit as st
from ghostbuster import Ghostbuster
import config

# Page configuration
st.set_page_config(
    page_title="👻 Ghostbuster - Job Posting Analyzer",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling with dark mode support
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #ffffff;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #b0b0b0;
        margin-bottom: 2rem;
    }
    .score-container {
        text-align: center;
        padding: 2rem;
        border-radius: 10px;
        margin: 2rem 0;
    }
    .score-high {
        background-color: #1a4d2e;
        border: 3px solid #4ade80;
        color: #ffffff;
    }
    .score-medium {
        background-color: #4d3800;
        border: 3px solid #fbbf24;
        color: #ffffff;
    }
    .score-low {
        background-color: #4d1a1a;
        border: 3px solid #ef4444;
        color: #ffffff;
    }
    .score-number {
        font-size: 4rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .verdict {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1rem;
        color: #ffffff;
    }
    .red-flag {
        background-color: #4d3800;
        padding: 0.5rem 1rem;
        border-left: 4px solid #fbbf24;
        margin: 0.5rem 0;
        color: #ffffff;
    }
    .info-box {
        background-color: #1a3a52;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
        color: #ffffff;
    }
    .good-box {
        background-color: #1a4d2e;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #4ade80;
        margin: 1rem 0;
        color: #ffffff;
    }
    .warning-box {
        background-color: #4d3800;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #fbbf24;
        margin: 1rem 0;
        color: #ffffff;
    }
    .danger-box {
        background-color: #4d1a1a;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report' not in st.session_state:
    st.session_state.report = None

# Sidebar with information
with st.sidebar:
    st.markdown("## 📊 About Ghostbuster")
    st.markdown("""
    **What are Ghost Jobs?**
    
    According to Forbes, ~45% of job postings may be "ghost jobs" - 
    positions companies post with no intention of actually hiring.
    
    **Why do companies post fake jobs?**
    - Appear to be growing for investors
    - Collect resumes for future use
    - Test the job market
    - Keep employees motivated
    
    **How Ghostbuster helps:**
    - Analyzes job descriptions
    - Researches company information
    - Detects suspicious patterns
    - Gives you a confidence score
    """)
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    st.markdown(f"**High Confidence:** {config.CONFIDENCE_THRESHOLD_HIGH}+")
    st.markdown(f"**Low Confidence:** <{config.CONFIDENCE_THRESHOLD_LOW}")
    
    st.markdown("---")
    st.markdown("### 🔍 Red Flags We Check")
    st.markdown("""
    - Generic job descriptions
    - Missing salary information
    - Vague requirements
    - Company stage mismatches
    - Unrealistic requirements
    - Limited company info
    """)

# Main header
st.markdown('<div class="main-header">👻 Ghostbuster</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Detect Fake Job Postings with AI-Powered Analysis</div>', unsafe_allow_html=True)

# Check if API key is configured
if not config.PERPLEXITY_API_KEY or config.PERPLEXITY_API_KEY == 'your_api_key_here':
    st.error("⚠️ **Perplexity API key not configured!**")
    st.markdown("""
    Please add your Perplexity API key to the `.env` file:
    ```
    PERPLEXITY_API_KEY=pplx-your-actual-key-here
    ```
    Then restart the app.
    """)
    st.stop()

# Main input section
st.markdown("## 🔗 Enter Job Posting URL")
st.markdown('<div class="info-box">💡 Paste the URL of any job posting you want to analyze. We\'ll scrape the posting, research the company, and give you a confidence score.</div>', unsafe_allow_html=True)

job_url = st.text_input(
    "Job Posting URL",
    placeholder="https://www.example.com/jobs/12345",
    label_visibility="collapsed"
)

# Analysis button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button("🔍 Analyze This Job", use_container_width=True, type="primary")

# Run analysis when button is clicked
if analyze_button:
    if not job_url:
        st.error("❌ Please enter a job posting URL")
    else:
        st.session_state.analysis_complete = False
        st.session_state.report = None
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize Ghostbuster
            status_text.text("🚀 Initializing Ghostbuster...")
            progress_bar.progress(10)
            gb = Ghostbuster()
            
            # Step 1: Scrape job posting
            status_text.text("🔍 Scraping job posting...")
            progress_bar.progress(25)
            job_data = gb.scrape_job_posting(job_url)
            
            if not job_data:
                st.error("❌ Could not scrape the job posting. The URL might be invalid or the site might be blocking scrapers.")
                st.stop()
            
            # Step 2: Research company
            status_text.text("🔬 Researching company with Perplexity AI...")
            progress_bar.progress(50)
            company_research = gb.research_company(job_data['company'], job_data['title'])
            
            # Step 3: Analyze job description
            status_text.text("📝 Analyzing job description for red flags...")
            progress_bar.progress(75)
            red_flags = gb.analyze_job_description(job_data['full_text'])
            
            # Step 4: Calculate score
            status_text.text("📊 Calculating confidence score...")
            progress_bar.progress(90)
            score, reasons = gb.calculate_confidence_score(job_data, company_research, red_flags)
            
            # Step 5: Generate report
            status_text.text("✅ Generating report...")
            progress_bar.progress(100)
            
            # Create report
            report = {
                'score': score,
                'job_data': job_data,
                'company_research': company_research,
                'red_flags': red_flags,
                'reasons': reasons
            }
            
            st.session_state.report = report
            st.session_state.analysis_complete = True
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            st.stop()

# Display results if analysis is complete
if st.session_state.analysis_complete and st.session_state.report:
    report = st.session_state.report
    score = report['score']
    job_data = report['job_data']
    company_research = report['company_research']
    red_flags = report['red_flags']
    reasons = report['reasons']
    
    st.markdown("---")
    st.markdown("## 📊 Analysis Results")
    
    # Job Information
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 📋 {job_data['title']}")
        st.markdown(f"**🏢 Company:** {job_data['company']}")
    with col2:
        st.markdown(f"**🔗 URL:**")
        st.markdown(f"[View Original Posting]({job_data['url']})")
    
    st.markdown("---")
    
    # Confidence Score Display
    if score >= config.CONFIDENCE_THRESHOLD_HIGH:
        score_class = "score-high"
        verdict = "✅ LIKELY LEGITIMATE"
        verdict_emoji = "👍"
        verdict_color = "#28a745"
    elif score >= config.CONFIDENCE_THRESHOLD_LOW:
        score_class = "score-medium"
        verdict = "⚠️ PROCEED WITH CAUTION"
        verdict_emoji = "🤔"
        verdict_color = "#ffc107"
    else:
        score_class = "score-low"
        verdict = "🚨 LIKELY FAKE/GHOST JOB"
        verdict_emoji = "👻"
        verdict_color = "#dc3545"
    
    st.markdown(f"""
        <div class="score-container {score_class}">
            <div style="font-size: 1.5rem;">Confidence Score</div>
            <div class="score-number" style="color: {verdict_color};">{score}/100</div>
            <div class="verdict">{verdict_emoji} {verdict}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Interpretation
    st.markdown("### 💡 What This Score Means")
    if score >= config.CONFIDENCE_THRESHOLD_HIGH:
        st.markdown("""
        <div class="good-box">
        <strong>This job posting appears legitimate!</strong> The company seems real, the job description is detailed, 
        and we found positive signals about their hiring activity. It's likely worth applying.
        </div>
        """, unsafe_allow_html=True)
    elif score >= config.CONFIDENCE_THRESHOLD_LOW:
        st.markdown("""
        <div class="warning-box">
        <strong>This job posting has some concerning signs.</strong> While it might be legitimate, there are red flags 
        that suggest caution. Do additional research on the company before applying.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="danger-box">
        <strong>This job posting shows multiple signs of being fake or a ghost job.</strong> Consider looking for 
        other opportunities instead of spending time on this application.
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed Analysis
    st.markdown("---")
    st.markdown("### 📝 Detailed Analysis")
    
    # Reasons/Scoring breakdown
    with st.expander("🔢 **Score Breakdown**", expanded=True):
        if reasons:
            for reason in reasons:
                st.markdown(f"- {reason}")
        else:
            st.markdown("No specific adjustments to base score.")
    
    # Red Flags
    with st.expander("⚠️ **Red Flags Detected**", expanded=True):
        if red_flags:
            for flag, value in red_flags.items():
                if value:
                    flag_name = flag.replace('_', ' ').title()
                    st.markdown(f'<div class="red-flag">🚩 {flag_name}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="good-box">✅ No major red flags detected in the job description!</div>', unsafe_allow_html=True)
    
    # Company Research
    with st.expander("🔬 **Company Research Summary**", expanded=False):
        if company_research:
            st.markdown(company_research['research'])
        else:
            st.markdown('<div class="warning-box">⚠️ Could not complete company research.</div>', unsafe_allow_html=True)
    
    # Job Description Preview
    with st.expander("📄 **Job Description Preview**", expanded=False):
        st.text(job_data['full_text'][:1000] + "...")
    
    st.markdown("---")
    
    # Action recommendations
    st.markdown("### 🎯 Recommended Actions")
    if score >= config.CONFIDENCE_THRESHOLD_HIGH:
        st.markdown("""
        1. ✅ **Apply for this job** - It appears legitimate
        2. 🔍 Visit the company website to learn more
        3. 📧 Try to find the hiring manager on LinkedIn
        4. 📝 Customize your resume and cover letter
        """)
    elif score >= config.CONFIDENCE_THRESHOLD_LOW:
        st.markdown("""
        1. 🔍 **Research the company further** - Check reviews on Glassdoor
        2. 🌐 Verify the company website and social media presence
        3. 💼 Look for the job on LinkedIn or the company's careers page
        4. 📞 Consider calling the company to verify the position
        5. ⚖️ Weigh pros and cons before applying
        """)
    else:
        st.markdown("""
        1. 🚫 **Consider skipping this job** - High likelihood it's fake
        2. 🔍 If you really want to apply, do thorough research first
        3. 💼 Look for the same role on the company's official careers page
        4. 📧 Try to contact someone at the company directly
        5. ⏰ Don't waste too much time on this opportunity
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>👻 <strong>Ghostbuster</strong> - Helping job seekers avoid fake postings</p>
    <p style="font-size: 0.9rem;">Remember: This tool provides guidance, but always do your own research before making decisions.</p>
</div>
""", unsafe_allow_html=True)