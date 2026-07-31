import os
import re
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# ---------------------------------------------
# Config
# ---------------------------------------------

st.set_page_config(
    page_title="LinkedIn Translator",
    page_icon="💀",
    layout="centered",
)

MODEL = "Qwen/Qwen2.5-7B-Instruct"

SYSTEM_PROMPT = """
You are LinkedIn Translator.

Your job is to translate ridiculously overdramatic LinkedIn posts into
what the author actually means.

The humour comes from exposing unnecessary corporate fluff.

RULES

- Maximum 12 words.
- Return ONE sentence only.
- Funny.
- Dry humour.
- Sarcastic.
- Roast the writing style, NOT the person.
- Never invent facts.
- Never accuse someone of crimes unless explicitly stated.
- Never explain the joke.
- Never output reasoning.
- Never output <think>.
- Never use quotation marks.
- Return ONLY the translation.


Examples

Input:
I'm thrilled to announce that I've accepted a new opportunity.

Output:
Found a better-paying job.

Input:
After months of reflection, I've decided to pursue a new chapter.

Output:
I quit.

Input:
Today I had the opportunity to troubleshoot a network outage.

Output:
The Wi-Fi broke. I fixed it.

Input:
I'm humbled to receive this prestigious award.

Output:
Please congratulate me.

Input:
Excited to share that I've completed another certification.

Output:
I passed another online course.

Input:
Building something exciting in stealth.

Output:
I have an idea.

Input:
Reflecting on my incredible journey...

Output:
Here's my life story.

Input:
Grateful for this amazing opportunity.

Output:
Lucky me.

Input:
Proud to announce...

Output:
Need some LinkedIn likes.

Input:
Leadership isn't about titles...

Output:
I got promoted.

Input:
Every challenge is an opportunity to grow.

Output:
Work was annoying today.

Be clever.
Be concise.
Be savage.
"""


# ---------------------------------------------
# Helpers
# ---------------------------------------------

def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://router.huggingface.co/v1")


def clean_output(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text.strip("\"'")


def translate(client: OpenAI, post: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": post},
        ],
        temperature=0.7,
        max_tokens=40,
    )
    return clean_output(response.choices[0].message.content)


# ---------------------------------------------
# Session state
# ---------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []  # list of (post, translation)


# ---------------------------------------------
# Sidebar
# ---------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    try:
        secret_key = st.secrets.get("HF_TOKEN", "")
    except Exception:
        secret_key = ""
    default_key = secret_key or os.environ.get("HF_TOKEN", "")
    api_key = st.text_input(
        "Hugging Face API token",
        value=default_key,
        type="password",
        help="Get one at huggingface.co/settings/tokens. "
             "You can also set it as the HF_TOKEN environment variable.",
    )

    st.divider()
    if st.button("🗑️ Clear history"):
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption(f"Model: `{MODEL}`")


# ---------------------------------------------
# Main UI
# ---------------------------------------------

LOGO_SVG = """
<svg width="90" height="90" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <!-- Skull -->
  <ellipse cx="50" cy="40" rx="28" ry="26" fill="#f2f2f2" stroke="#111" stroke-width="2.5"/>
  <path d="M 24 42 Q 20 60 32 66 L 32 58 Q 24 54 24 42 Z" fill="#f2f2f2" stroke="#111" stroke-width="2.5"/>
  <path d="M 76 42 Q 80 60 68 66 L 68 58 Q 76 54 76 42 Z" fill="#f2f2f2" stroke="#111" stroke-width="2.5"/>
  <path d="M 34 62 Q 50 72 66 62 L 64 78 Q 50 84 36 78 Z" fill="#f2f2f2" stroke="#111" stroke-width="2.5"/>
  <ellipse cx="38" cy="38" rx="7" ry="9" fill="#111"/>
  <ellipse cx="62" cy="38" rx="7" ry="9" fill="#111"/>
  <path d="M 50 44 L 46 54 L 54 54 Z" fill="#111"/>
  <line x1="40" y1="70" x2="40" y2="78" stroke="#111" stroke-width="2"/>
  <line x1="46" y1="72" x2="46" y2="80" stroke="#111" stroke-width="2"/>
  <line x1="54" y1="72" x2="54" y2="80" stroke="#111" stroke-width="2"/>
  <line x1="60" y1="70" x2="60" y2="78" stroke="#111" stroke-width="2"/>
  <!-- Crossbones -->
  <g stroke="#f2f2f2" stroke-width="6" stroke-linecap="round">
    <line x1="10" y1="78" x2="90" y2="92" stroke="#111" stroke-width="8"/>
    <line x1="90" y1="78" x2="10" y2="92" stroke="#111" stroke-width="8"/>
    <line x1="10" y1="78" x2="90" y2="92" stroke-width="5"/>
    <line x1="90" y1="78" x2="10" y2="92" stroke-width="5"/>
  </g>
  <circle cx="10" cy="78" r="5" fill="#f2f2f2" stroke="#111" stroke-width="2"/>
  <circle cx="10" cy="92" r="5" fill="#f2f2f2" stroke="#111" stroke-width="2"/>
  <circle cx="90" cy="78" r="5" fill="#f2f2f2" stroke="#111" stroke-width="2"/>
  <circle cx="90" cy="92" r="5" fill="#f2f2f2" stroke="#111" stroke-width="2"/>
</svg>
"""

components.html(
    f"""
    <div style="text-align:center; background:transparent; margin:0; padding:0;">
        {LOGO_SVG}
        <h1 style="font-family: 'Source Sans Pro', sans-serif; color:#fafafa; margin:0;">
            💼 LinkedIn Translator
        </h1>
        <p style="font-family: 'Source Sans Pro', sans-serif; color:#a3a8b8; margin:4px 0 0 0;">
            Paste overdramatic LinkedIn fluff. Get the truth. 💀
        </p>
    </div>
    """,
    height=220,
)

post = st.text_area(
    "Paste a LinkedIn post",
    height=150,
    placeholder="I'm beyond humbled and overjoyed to announce...",
)

col1, col2 = st.columns([1, 4])
with col1:
    translate_clicked = st.button("Translate", type="primary", use_container_width=True)

if translate_clicked:
    cleaned_post = " ".join(post.split())[:2500]

    if not cleaned_post:
        st.warning("Paste something first.")
    elif not api_key:
        st.error("Add your Hugging Face API token in the sidebar first.")
    else:
        with st.spinner("Translating..."):
            try:
                client = get_client(api_key)
                translation = translate(client, cleaned_post)
                st.session_state.history.insert(0, (cleaned_post, translation))
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ---------------------------------------------
# Results
# ---------------------------------------------

if st.session_state.history:
    st.divider()
    st.subheader("Translations")

    for original, translation in st.session_state.history:
        with st.container(border=True):
            st.markdown(f"**💀 {translation}**")
            with st.expander("Show original post"):
                st.write(original)
