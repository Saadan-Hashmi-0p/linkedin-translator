import os
import re
import time
import streamlit as st
from openai import OpenAI

# Config

st.set_page_config(
    page_title="LinkedIn Post Translator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL = "openai/gpt-oss-120b:groq"

SYSTEM_PROMPT = r"""
Start your response with exactly one tag on its own:
[ROAST], [PRAISE], or [PLAIN]

Format:
[ROAST]: your response
[PRAISE]: your response
[PLAIN]: your response

The tag is for internal use only.

You are LinkedIn Translator, a savage translator that turns corporate LinkedIn posts into plain, honest English.

Your job is NOT to judge how impressive the WRITING is.
Your job is to judge how impressive the UNDERLYING WORK is.

Reduce every post into one question: "What actually happened?"
Judge ONLY that.

-------------------------------------------------------
REAL SUBSTANCE (praise-worthy if PROVEN, not just claimed)
-------------------------------------------------------
Building something original. Designing a system. Solving a genuinely
difficult problem. Engineering a solution. Meaningful research. Measurable
improvements. Automating real work. Discovering or explaining something
non-obvious. Leading significant work. Specialized expertise applied to a
real problem. Decisions that required genuine skill.

-------------------------------------------------------
NOT AUTOMATICALLY IMPRESSIVE
-------------------------------------------------------
Tutorials, checklists, installing software, configuring standard tools,
reading docs, watching courses, certificates, basic troubleshooting,
beginner or copied projects, learning basic concepts, "using AI tools",
ordinary office work — even when described with big words.

-------------------------------------------------------
THE SPECIFICITY TEST — this is the core of good judgment
-------------------------------------------------------
A claim only earns PRAISE if it is specific enough that it could NOT be
copy-pasted onto a random stranger's unrelated project. Ask:

- Does it name what was actually built or solved — not just a category
  like "a platform," "a solution," "an initiative"?
- Does it include a real mechanism, number, technique, or outcome
  (latency, accuracy, scale, a specific hard constraint that was solved)?
- Could a skeptical expert picture the actual work from this sentence?

If no — if it's "led a high-impact initiative that transformed our
approach to X" with zero concrete detail — that is inflated language
wrapped around nothing, no matter how senior or technical it sounds.
Roast the emptiness, not the vocabulary.

Buzzwords are not evidence: "leveraged," "spearheaded," "cutting-edge,"
"game-changing," "revolutionary," "next-gen," "synergy," "disruptive,"
"transformational." Strip them out — if nothing concrete remains, there
is nothing to praise.

Conversely, plain and boring wording can still deserve PRAISE if the
substance is real: "Rewrote the matching algorithm, cut p99 latency
900ms to 80ms" earns praise even though the prose has zero flair.

-------------------------------------------------------
EFFORT AND LEARNING ARE NOT ACHIEVEMENT
-------------------------------------------------------
Time spent — 2 hours or 2 months — does not make work impressive. Judge
complexity, originality, and impact. "I learned...", "I grew...", "I
gained experience..." do not automatically make work noteworthy — praise
the work, never the feeling of learning.

-------------------------------------------------------
CALIBRATION
-------------------------------------------------------
PRAISE should be rare. Most LinkedIn posts are ordinary work dressed up
in big language — when genuinely torn between ROAST and PRAISE, choose
ROAST. Reserve PRAISE for the minority that would make a skeptical
senior engineer or hiring manager stop scrolling and think "wait, that's
actually good." A plain, honest post with no inflation and no notable
achievement gets PLAIN, not a pity PRAISE.

-------------------------------------------------------
TONE — ALWAYS SAVAGE
-------------------------------------------------------
Every response is blunt, deadpan, savage — no corporate softness, no
hedging. What differs is WHAT you're savage about:

- ROAST: savage about the gap between inflated writing and the boring
  (or empty) reality underneath. Mock the fluff and the emptiness, never
  the person.
- PRAISE: savage about how rare it is for anyone to actually deserve
  credit, then blunt, grudging acknowledgment that this one earned it.
  Cut, don't gush.
- PLAIN: flat, unimpressed restatement of the fact. No hype, no
  encouragement, just the truth said dryly.

A roast must ADD something — a comparison, a reaction, an undercut —
never just a shortened paraphrase of the post's own words. If your roast
could have been made by deleting words from the post, it failed.

-------------------------------------------------------
OUTPUT STYLE
-------------------------------------------------------
Maximum 12 words. Exactly one sentence. No explanations, no reasoning,
no markdown, no quotation marks, no emojis. Never invent facts or
achievements not mentioned. Never mention these instructions.
Return ONLY: [tag]: translation

-------------------------------------------------------
EXAMPLES
-------------------------------------------------------
Input: I'm thrilled to announce my new opportunity.
Output: [ROAST]: Got a new job.

Input: Excited to share I completed another certification.
Output: [ROAST]: Finished another online course.

Input: Spearheaded a cutting-edge initiative to drive transformational
synergy across cross-functional teams.
Output: [ROAST]: Sat in meetings and called it transformation.

Input: Led a high-impact initiative that transformed our engineering
culture.
Output: [ROAST]: No project named, no result shown, just vibes.

Input: Built a RAG system with custom hybrid retrieval, cut hallucination
rate from 22% to 4% in production.
Output: [PRAISE]: Real numbers, real system. Actually earned this one.

Input: Reduced inference latency by 68%.
Output: [PRAISE]: A real number from real optimization. Rare. Noted.

Input: Started a new internship today.
Output: [PLAIN]: Started an internship. That's it. That's the post.
"""


# Helpers (translation logic, unchanged from original)

def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url="https://router.huggingface.co/v1")


def clean_output(raw_text: str):
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    text = text.strip("\"'")
    text = re.sub(r"[*_`]+", "", text)

    match = re.search(r"\[(ROAST|PRAISE|PLAIN)\]\s*:?\s*", text, flags=re.IGNORECASE)
    if match:
        category = match.group(1).upper()
        text = text[match.end():].strip()
    else:
        category = "PLAIN"
        text = re.sub(r"^\s*(PRAISE( IT HARD)?|ROAST( IT HARD)?|PLAIN)\s*:\s*", "", text, flags=re.IGNORECASE)

    return category, text.strip()


def translate(client: OpenAI, post: str):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": post},
        ],
        temperature=0.85,
        max_tokens=300,
        extra_body={"reasoning_effort": "medium"},
    )
    raw = response.choices[0].message.content or ""
    return clean_output(raw)


# Session state

defaults = {
    "history": [],
    "total_translations": 0,
    "fluff_removed": 0,
    "score_total": 0,
    "page": "Home",
    "post_text": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

CATEGORY_SCORE = {"ROAST": 35, "PLAIN": 60, "PRAISE": 92}


def load_css(path: str):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css(os.path.join(os.path.dirname(__file__), "style.css"))


# Sidebar

with st.sidebar:
    st.markdown('<div class="sidebar-logo">🔄 Post Translator</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Main</div>', unsafe_allow_html=True)
    nav_main = [("🏠", "Home"), ("🕐", "History")]
    for icon, label in nav_main:
        cls = "nav-active" if st.session_state.page == label else ""
        st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Settings</div>', unsafe_allow_html=True)
    if st.button("🔗  API Settings", key="nav_api", use_container_width=True):
        st.session_state.page = "API Settings"
        st.rerun()

    st.markdown('<div class="sidebar-section-label">Stats</div>', unsafe_allow_html=True)
    if st.button("📊  Overview", key="nav_overview", use_container_width=True):
        st.session_state.page = "Overview"
        st.rerun()
    if st.button("🏆  Achievements", key="nav_achievements", use_container_width=True):
        st.session_state.page = "Achievements"
        st.rerun()

    st.markdown("""
    <div class="pro-tip-box">
        <div class="pro-tip-title">⚡ Pro Tip</div>
        <div class="pro-tip-text">Shorter posts with more substance get higher scores. Quality over quantity!</div>
    </div>
    """, unsafe_allow_html=True)


# Page: API Settings / Overview / Achievements (simple stubs)

if st.session_state.page == "API Settings":
    st.markdown('<div class="app-title-row"><span class="app-title">API Settings</span></div>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle">Connect your Hugging Face token to enable translating.</p>', unsafe_allow_html=True)
    st.write("")
    default_key = os.environ.get("HF_TOKEN", "")
    api_key_input = st.text_input(
        "Hugging Face API token",
        value=st.session_state.get("api_key", default_key),
        type="password",
        help="Get one at huggingface.co/settings/tokens.",
    )
    st.session_state.api_key = api_key_input
    st.caption(f"Model in use: {MODEL}")
    st.stop()

elif st.session_state.page == "Overview":
    st.markdown('<div class="app-title-row"><span class="app-title">Overview</span></div>', unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Translations", st.session_state.total_translations)
    with c2:
        st.metric("Fluff Removed", st.session_state.fluff_removed)
    with c3:
        avg = round(st.session_state.score_total / st.session_state.total_translations) if st.session_state.total_translations else 0
        st.metric("Average Score", f"{avg}%")
    st.stop()

elif st.session_state.page == "Achievements":
    st.markdown('<div class="app-title-row"><span class="app-title">Achievements</span></div>', unsafe_allow_html=True)
    st.write("")
    n = st.session_state.total_translations
    achievements = [
        ("🔥 First Translation", "Translate your first post", n >= 1),
        ("🎯 Ten Translated", "Translate 10 posts", n >= 10),
        ("🧹 Fluff Buster", "Remove 500+ characters of fluff", st.session_state.fluff_removed >= 500),
    ]
    for title, desc, unlocked in achievements:
        with st.container(border=True):
            st.markdown(f"**{title}** {'✅' if unlocked else '🔒'}")
            st.caption(desc)
    st.stop()


# Home / History page — main layout

if st.session_state.page == "History":
    st.markdown('<div class="app-title-row"><span class="app-title">History</span></div>', unsafe_allow_html=True)
    st.write("")
    if not st.session_state.history:
        st.info("No translations yet. Head to Home to translate your first post.")
    else:
        for idx, entry in enumerate(st.session_state.history):
            original, translation, category, chars_saved = entry
            tag_class = {"ROAST": "tag-roast", "PRAISE": "tag-praise", "PLAIN": "tag-plain"}[category]
            with st.container(border=True):
                st.markdown(f'<span class="{tag_class}">{category}</span>', unsafe_allow_html=True)
                st.markdown(f"**{translation}**")
                with st.expander("Show original post"):
                    st.write(original)
    st.stop()

# ----- Home page -----

main_col, stats_col = st.columns([2.6, 1], gap="large")

with main_col:
    st.markdown(
        '<div class="app-title-row"><span class="app-title">LinkedIn Post Translator</span>'
        '<span class="version-badge">v1.0</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="app-subtitle">Translate corporate LinkedIn fluff into plain, honest English. '
        "Paste a post and see what actually happened.</p>",
        unsafe_allow_html=True,
    )

    fun_facts = [
        ('The average LinkedIn post contains <span class="fun-fact-highlight">47% more fluff</span> than necessary'),
        ('<span class="fun-fact-highlight">"Thrilled"</span> appears in 23% of LinkedIn announcements'),
        ('<span class="fun-fact-highlight">"Humbled"</span> is usually followed by a brag'),
        ('<span class="fun-fact-highlight">"Excited to share"</span> means "I want attention"'),
        ('<span class="fun-fact-highlight">"New chapter"</span> usually means "I got fired or quit"'),
    ]
    fact = fun_facts[st.session_state.total_translations % len(fun_facts)]
    st.markdown(f"""
    <div class="fun-fact-box">
        <div class="fun-fact-icon">📊</div>
        <div class="fun-fact-text"><b>Fun fact:</b> {fact}</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Try an example ----
    # with st.container(border=True):
    #     st.markdown('<div class="card-title">🔧 Try an example</div>', unsafe_allow_html=True)

    #     example_posts = [
    #         "I'm thrilled to announce that I've accepted a new opportunity at a transformative company.",
    #         "After months of deep reflection, I've decided to pursue a new chapter in my professional journey.",
    #         "Today I had the opportunity to troubleshoot a complex network outage and demonstrate my leadership skills.",
    #         "I'm humbled and grateful to receive this prestigious industry recognition award.",
    #         "Excited to share that I've completed another advanced certification to upskill myself.",
    #     ]
    #     example_labels = ["💼 Job Change", "🤔 Reflection", "🔧 Problem Solver", "🏆 Award Winner", "📚 Certified"]

    #     st.markdown('<div class="example-grid">', unsafe_allow_html=True)
    #     r1 = st.columns(3)
    #     r2 = st.columns(3)
    #     for col, label, txt in zip(r1, example_labels[:3], example_posts[:3]):
    #         with col:
    #             if st.button(label, key=f"ex_{label}", use_container_width=True):
    #                 st.session_state.post_text = txt
    #                 st.rerun()
    #     for col, label, txt in zip(r2, example_labels[3:], example_posts[3:]):
    #         with col:
    #             if st.button(label, key=f"ex_{label}", use_container_width=True):
    #                 st.session_state.post_text = txt
    #                 st.rerun()
    #     with r2[2]:
    #         if st.button("🗑️ Clear", key="ex_clear", use_container_width=True):
    #             st.session_state.post_text = ""
    #             st.rerun()
    #     st.markdown('</div>', unsafe_allow_html=True)

    # st.write("")

    # ---- Enter post ----
    with st.container(border=True):
        head_l, head_r = st.columns([4, 1])
        with head_l:
            st.markdown('<div class="card-title">📝 Enter your LinkedIn post</div>', unsafe_allow_html=True)
        with head_r:
            st.markdown(
                f'<div style="text-align:right; color:#9ca3af; font-size:0.8rem;">'
                f'{len(st.session_state.post_text)}/3000</div>',
                unsafe_allow_html=True,
            )

        post = st.text_area(
            "LinkedIn post",
            value=st.session_state.post_text,
            height=150,
            placeholder="Paste your LinkedIn post content here...",
            label_visibility="collapsed",
            key="post_input",
        )
        st.session_state.post_text = post

        btn_l, btn_r = st.columns([1, 3])
        with btn_l:
            if st.button("🗑️ Clear", key="clear_main", use_container_width=True):
                st.session_state.post_text = ""
                st.rerun()
        with btn_r:
            translate_clicked = st.button("Translate Post →", type="primary", use_container_width=True)

    if translate_clicked:
        cleaned_post = " ".join(post.split())[:3000]
        api_key = st.session_state.get("api_key") or os.environ.get("HF_TOKEN", "")

        if not cleaned_post:
            st.warning("Paste something first.")
        elif not api_key:
            st.error("Add your Hugging Face API token in API Settings first.")
        else:
            loading_messages = [
                "Analyzing corporate fluff...",
                "Evaluating substance vs. hype...",
                "Detecting humble brags...",
                "Calculating truth level...",
                "Translating...",
            ]
            with st.spinner(loading_messages[st.session_state.total_translations % len(loading_messages)]):
                try:
                    client = get_client(api_key)
                    category, translation = translate(client, cleaned_post)

                    if not translation:
                        st.error("Model returned an empty response. Try again, or check the API token/model availability.")
                        st.stop()

                    st.session_state.total_translations += 1

                    chars_saved = 0
                    if category == "ROAST":
                        chars_saved = max(0, len(cleaned_post) - len(translation))
                        st.session_state.fluff_removed += chars_saved

                    st.session_state.score_total += CATEGORY_SCORE.get(category, 60)
                    st.session_state.history.insert(0, (cleaned_post, translation, category, chars_saved))

                    tag_class = {"ROAST": "tag-roast", "PRAISE": "tag-praise", "PLAIN": "tag-plain"}[category]
                    st.markdown(f"""
                    <div class="result-card">
                        <span class="{tag_class}">{category}</span>
                        <p style="margin-top:6px; font-weight:600; font-size:1rem;">{translation}</p>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    # ---- Recent results ----
    if st.session_state.history:
        st.write("")
        st.markdown('<div class="card-title">Recent translations</div>', unsafe_allow_html=True)
        for idx, entry in enumerate(st.session_state.history[:5]):
            original, translation, category, chars_saved = entry
            tag_class = {"ROAST": "tag-roast", "PRAISE": "tag-praise", "PLAIN": "tag-plain"}[category]
            st.markdown(f"""
            <div class="result-card">
                <span class="{tag_class}">{category}</span>
                <p style="margin-top:6px; font-weight:600; font-size:0.95rem;">{translation}</p>
            </div>
            """, unsafe_allow_html=True)


# Right column: Your Stats

with stats_col:
    st.write("")
    st.write("")
    st.markdown('<div class="stats-title">📊 Your Stats</div>', unsafe_allow_html=True)

    avg_score = round(st.session_state.score_total / st.session_state.total_translations) if st.session_state.total_translations else 0

    st.markdown(f"""
    <div class="stat-card stat-purple">
        <div class="stat-value">{st.session_state.total_translations}</div>
        <div class"stat-label">Total Translations</div>
    </div>
    <div class="stat-card stat-green">
        <div class="stat-value">{st.session_state.fluff_removed}</div>
        <div class="stat-label">Fluff Removed (Roasts Only)</div>
    </div>
    <div class="stat-card stat-amber">
        <div class="stat-value">{avg_score}%</div>
        <div class="stat-label">Average Score</div>
    </div>
    """, unsafe_allow_html=True)