import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from scraper import clean_url, fetch_website_links, fetch_website_contents

load_dotenv(override=True)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"

def get_engine_client(engine_choice: str):
    """Factory creating OpenAI-compatible client for Gemini or Ollama."""
    if engine_choice == "Gemini (Cloud)":
        return OpenAI(api_key=GOOGLE_API_KEY, base_url=GEMINI_BASE_URL), "gemini-2.5-flash"
    else:
        return OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL), "llama3.2"

LINK_SELECTION_SYSTEM_PROMPT = """You are an AI research assistant.
You are given a list of web links extracted from a company website.
Your objective is to identify the most relevant pages needed to create a comprehensive enterprise brochure
(e.g., About Us, Company Culture, Product/Solutions, Careers, Team).

You MUST respond strictly with valid JSON conforming to this schema:
{
    "links": [
        {"type": "about page", "url": "https://example.com/about"},
        {"type": "careers page", "url": "https://example.com/careers"}
    ]
}
Do not include Terms of Service, Privacy Policies, Legal Notices, or Login/Sign-up URLs.
"""

BROCHURE_SYSTEM_PROMPT = """You are an executive marketing and investment analyst.
Analyze the provided landing page and associated corporate subpages to synthesize a structured,
high-impact professional brochure in clean Markdown (no code blocks).

Structure requirements:
1. # Executive Overview & Value Proposition
2. ## Core Products, Solutions & Technology
3. ## Company Culture, Leadership & Careers
4. ## Target Audience & Strategic Impact
5. ## How to Engage / Connect
"""

def filter_relevant_links(url: str, engine_choice: str) -> list[dict]:
    """Asks the LLM to inspect extracted links and pick key company pages in JSON."""
    client, model = get_engine_client(engine_choice)
    all_links = fetch_website_links(url)
    if not all_links:
        return []

    user_prompt = f"Target Base URL: {url}\nCandidate links found:\n" + "\n".join(all_links)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": LINK_SELECTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("links", [])[:4]  # Top 4 most relevant links
    except Exception as e:
        print(f"[Link Filter Error] {e}")
        return []

def assemble_knowledge_context(company_name: str, url: str, engine_choice: str, status_callback=None) -> str:
    """Gathers landing page + subpages and constructs structured research context."""
    if status_callback:
        status_callback(f"Scanning landing page: {url}...")
    landing_text = fetch_website_contents(url, max_chars=3000)

    if status_callback:
        status_callback("Analyzing link architecture with LLM reasoning...")
    curated_links = filter_relevant_links(url, engine_choice)

    context = f"Company Name: {company_name}\n\n## Primary Landing Page:\n{landing_text}\n\n"
    for item in curated_links:
        sub_type = item.get("type", "Corporate Page")
        sub_url = item.get("url")
        if sub_url:
            if status_callback:
                status_callback(f"Crawling {sub_type}: {sub_url}...")
            sub_content = fetch_website_contents(sub_url, max_chars=2000)
            context += f"### Section: {sub_type.title()} ({sub_url})\n{sub_content}\n\n"

    # Context window guardrail: 12,000 characters
    return context[:12000]

def stream_enterprise_brochure(company_name: str, url: str, engine_choice: str):
    """Yields token-by-token streaming markdown for reactive UI updates."""
    clean_target_url = clean_url(url)
    
    yield "### 🔍 Phase 1: Scraping and discovering relevant corporate links..."
    context = assemble_knowledge_context(company_name, clean_target_url, engine_choice)

    yield f"### ✍️ Phase 2: Generating executive brochure using **{engine_choice}**...\n\n---\n\n"
    
    client, model = get_engine_client(engine_choice)
    user_prompt = f"Company: {company_name}\n\nResearch Dossier:\n{context}\n\nGenerate the full brochure now."

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            stream=True
        )
        
        brochure_text = ""
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            brochure_text += token
            yield brochure_text
    except Exception as e:
        yield f"❌ **Error generating brochure:** {e}"
