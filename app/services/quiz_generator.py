import os
import json
import google.generativeai as genai  # type: ignore # pip install google-generativeai
import httpx # type: ignore

from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

async def fetch_real_news() -> str:
    """Fetch today's top world news headlines."""
    try:
        if NEWS_API_KEY and NEWS_API_KEY != "your_newsapi_key_here":
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": NEWS_API_KEY,
                "language": "en",
                "pageSize": 10,
                "category": "general"
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                data = resp.json()
                if data.get("status") == "ok":
                    articles = data.get("articles", [])
                    headlines = []
                    for a in articles:
                        title = a.get("title", "")
                        desc = a.get("description", "") or ""
                        if title:
                            headlines.append(f"- {title}. {desc[:100]}")
                    return "\n".join(headlines[:10])
    except Exception as e:
        print(f"News API failed: {e}")

    # Fallback: use GNews free API (no key needed)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://gnews.io/api/v4/top-headlines?lang=en&max=10&token=free",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            data = resp.json()
            articles = data.get("articles", [])
            if articles:
                headlines = [f"- {a['title']}. {a.get('description','')[:100]}" for a in articles]
                return "\n".join(headlines)
    except Exception:
        pass

    # Static fallback if all APIs fail
    return """
    - World leaders meet at G7 summit to discuss global economy and climate policy.
    - Technology companies announce major AI breakthroughs in healthcare and science.
    - Space agencies prepare for next moon mission with international collaboration.
    - Global markets respond to new trade agreements between major economies.
    - Climate scientists warn of accelerating glacier melt and rising sea levels.
    - New renewable energy records set as solar and wind power expand worldwide.
    - International health organizations monitor new disease outbreaks globally.
    - Education reforms announced in several countries to improve learning outcomes.
    - Sports world reacts to major championship results and athlete records.
    - Cultural festivals celebrate diversity and international artistic exchange.
    """


async def generate_questions_from_news(custom_news: str = None, num_questions: int = 10) -> list:
    """Generate quiz questions using Gemini AI from real news."""

    # Get news
    if custom_news:
        news_text = custom_news
    else:
        news_text = await fetch_real_news()

    model = genai.GenerativeModel("gemini-flash-latest")

    prompt = f"""You are a quiz master. Based on these real world news headlines:

{news_text}

Generate exactly {num_questions} multiple-choice quiz questions about current world events.

IMPORTANT RULES:
1. Each question must be based on real facts (not the exact headlines, but general knowledge related to those topics)
2. Make questions educational and interesting
3. Difficulty: mix of easy, medium, hard
4. Topics: politics, science, technology, environment, sports, culture

Return ONLY a valid JSON array. No extra text, no markdown, no explanation.
Format:
[
  {{
    "question_text": "What is the name of the international summit where world leaders discuss global economy?",
    "option_a": "G7 Summit",
    "option_b": "NATO Conference",
    "option_c": "UN Assembly",
    "option_d": "ASEAN Forum",
    "correct_answer": "A",
    "difficulty": "easy",
    "topic": "Politics",
    "explanation": "The G7 is a group of seven major advanced economies whose leaders meet annually to discuss global issues."
  }}
]"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up markdown if Gemini adds it
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        questions = json.loads(text)

        # Validate structure
        validated = []
        for q in questions:
            if all(k in q for k in ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer"]):
                q["correct_answer"] = q["correct_answer"].upper().strip(".")
                validated.append(q)

        return validated[:num_questions]

    except Exception as e:
        print(f"Gemini generation failed: {e}")
        raise Exception(f"AI question generation failed: {str(e)}")


# Keep backward compatibility
SAMPLE_NEWS = "Today's world news covering politics, technology, science, environment, and culture."
