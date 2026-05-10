import streamlit as st
import anthropic
import random
import os
import json
from datetime import datetime

from questions_db import QUESTIONS

st.set_page_config(
    page_title="RelationShit Question Generator",
    page_icon="💔",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: 800; color: #e63946; text-align: center; margin-bottom: 0.2rem; }
    .sub-title  { font-size: 1.1rem; color: #6c757d; text-align: center; margin-bottom: 2rem; }
    .question-card {
        background: #1e1e2e; border-radius: 12px; padding: 1.5rem;
        border-left: 4px solid #e63946; margin: 1rem 0;
        color: #cdd6f4; font-size: 1.05rem; line-height: 1.7;
    }
    .ep-header { color: #a6e3a1; font-weight: 600; font-size: 0.85rem; margin-bottom: 0.5rem; }
    .badge {
        display: inline-block; padding: 0.2rem 0.6rem;
        background: #313244; border-radius: 20px;
        color: #cba6f7; font-size: 0.78rem; margin: 0.1rem;
    }
    .chat-bubble-user {
        background: #e63946; color: white; border-radius: 18px 18px 4px 18px;
        padding: 0.75rem 1rem; margin: 0.5rem 0 0.5rem 20%; font-size: 0.95rem;
    }
    .chat-bubble-ai {
        background: #1e1e2e; color: #cdd6f4; border-radius: 18px 18px 18px 4px;
        padding: 0.75rem 1rem; margin: 0.5rem 20% 0.5rem 0; font-size: 0.95rem;
        border-left: 3px solid #e63946;
    }
    .chat-label { font-size: 0.75rem; color: #6c757d; margin-bottom: 2px; }
</style>
""", unsafe_allow_html=True)

MODEL = "claude-sonnet-4-6"

with st.sidebar:
    st.markdown("## 💔 RSA Question Generator")
    st.markdown("---")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            api_key = ""
    if not api_key:
        api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    else:
        st.success("✓ API key loaded")
    st.markdown("---")
    st.metric("Questions in DB", len(QUESTIONS))
    st.metric("Episodes covered", len(set(q["episode_num"] for q in QUESTIONS)))
    st.markdown("---")
    st.caption(f"Model: `{MODEL}`")
    st.caption("~$0.005 per generation")
    st.markdown("*Built for KSH — RelationSh!t Advice*")


@st.cache_resource
def get_client(key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=key)


def _save_to_sheets(theme: str, question: str):
    import requests as _req
    url = st.secrets.get("SHEETS_WEBAPP_URL", "")
    if not url:
        return
    try:
        _req.post(url, json={
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "theme": theme,
            "question": question,
        }, timeout=5)
    except Exception:
        pass


for _k, _v in [
    ("generated_question", ""),
    ("saved_questions", []),
    ("chat_history", []),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

THEMES = [
    "🎲 Random", "💔 Cheating & Betrayal", "💑 Long Distance",
    "👨‍👩‍👧 Family & Parents", "💌 Social Media & Apps", "💍 Marriage & Proposals",
    "🏠 Living Together", "🔞 Sex & Intimacy", "💰 Money & Career",
    "👫 Age Gap", "🤝 Friends & Exes", "💒 Arranged Marriage",
    "😮 Embarrassing Situations", "🤔 Misunderstandings", "🔑 Trust & Jealousy",
]

SYSTEM_PROMPT = """You are a writer for RelationSh!t Advice (RSA), a hugely popular Indian comedy relationship advice YouTube show hosted by Raunaq Rajani. Your job is to write authentic audience questions in the EXACT style of the show.

STRICT FORMAT RULES:
1. Start with "I'm [age][M/F]" (e.g. "I'm 27M." or "I'm 23F.") — OR start with "Dear Raunaq, I'm [age]..."
2. Write in first person throughout.
3. Set up the relationship situation with vivid, specific Indian cultural details.
4. Include ONE absurd, ironic, or comedic twist that makes it uniquely bizarre.
5. End with "What do I do?" or a close variant.
6. Length: 100–220 words. One or two paragraphs max.
7. The problem must feel real but have one element that makes the audience gasp or laugh.
8. Avoid generic problems — every detail should be specific.

TONE: Earnest, confused, slightly self-aware — the writer genuinely needs advice but doesn't realize how absurd their situation is."""


def generate_question(theme: str, client: anthropic.Anthropic) -> str:
    examples = random.sample(QUESTIONS, min(6, len(QUESTIONS)))
    examples_text = "\n\n---\n\n".join(
        [f"EXAMPLE {i+1}:\n{q['question']}" for i, q in enumerate(examples)]
    )
    theme_instruction = (
        "Pick a random relationship problem theme."
        if "Random" in theme
        else f"The question should be about: {theme.split(' ', 1)[1]}."
    )
    user_prompt = f"""Here are 6 real RSA audience questions to show you the exact style:

{examples_text}

---

Write ONE new original question in the EXACT SAME STYLE.
{theme_instruction}
Write ONLY the question — start directly with "I'm [age][M/F]." or "Dear Raunaq,"""

    resp = client.messages.create(
        model=MODEL, max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return resp.content[0].text.strip()


def chat_generate(user_message: str, client: anthropic.Anthropic) -> str:
    examples = random.sample(QUESTIONS, min(4, len(QUESTIONS)))
    examples_text = "\n\n".join([f"EXAMPLE:\n{q['question']}" for q in examples])

    system = SYSTEM_PROMPT + """

You are also an assistant who helps create RSA-style content. When given a freeform request, you:
1. Understand what kind of question they want (theme, characters, situation)
2. Generate ONE question in PERFECT RSA format

Write ONLY the question. No preamble, no panel responses, no explanations."""

    messages = []
    for msg in st.session_state.chat_history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": f"""Here are some real RSA questions for style reference:

{examples_text}

---

User request: {user_message}

Write ONE RSA-style question based on this request. Start directly with "I'm [age][M/F]." or "Dear Raunaq,"""})

    resp = client.messages.create(
        model=MODEL, max_tokens=600,
        system=system,
        messages=messages,
    )
    return resp.content[0].text.strip()


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">💔 RelationShit Question Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-powered question writer trained on 100+ episodes of RelationSh!t Advice</div>', unsafe_allow_html=True)

tab_chat, tab_gen, tab_browse, tab_saved, tab_feedback = st.tabs(["💬 Chat", "🎲 Generate", "📚 Browse", "⭐ Saved", "📝 Feedback"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("### Chat with the Question Generator")
    st.caption("Type anything — describe the situation, theme, characters, vibe. The AI will write the question for you.")

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-label">You</div><div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            content = msg["content"].replace("\n", "<br>")
            st.markdown(f'<div class="chat-label">RSA AI</div><div class="chat-bubble-ai">{content}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder='e.g. "cheating story set in Delhi" or "arranged marriage gone weird" or "give me something about social media"',
                label_visibility="collapsed",
            )
        with col_btn:
            send = st.form_submit_button("Send ➤", use_container_width=True, disabled=not api_key)

    if send and user_input.strip() and api_key:
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
        with st.spinner("Writing..."):
            try:
                client = get_client(api_key)
                reply = chat_generate(user_input.strip(), client)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                _save_to_sheets("💬 Chat", reply)
            except anthropic.AuthenticationError:
                st.error("Invalid API key.")
            except anthropic.RateLimitError:
                st.error("Rate limit hit — wait a moment and try again.")
            except anthropic.APIError as e:
                st.error(f"API error: {e}")
        st.rerun()

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("🎲 Surprise me", use_container_width=True, disabled=not api_key):
            prompts = [
                "Give me a wild cheating story with an unexpected twist",
                "Something about long distance relationship gone wrong",
                "Arranged marriage situation that's genuinely bizarre",
                "Social media / Instagram situation that spiralled out of control",
                "A situation involving families meddling in a relationship",
            ]
            st.session_state.chat_history.append({"role": "user", "content": random.choice(prompts)})
            with st.spinner("Writing..."):
                try:
                    client = get_client(api_key)
                    reply = chat_generate(st.session_state.chat_history[-1]["content"], client)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    _save_to_sheets("🎲 Surprise", reply)
                except Exception as e:
                    st.error(str(e))
            st.rerun()
    with col_b:
        if st.button("💾 Save last to Saved", use_container_width=True):
            ai_msgs = [m for m in st.session_state.chat_history if m["role"] == "assistant"]
            if ai_msgs:
                entry = {"question": ai_msgs[-1]["content"], "theme": "💬 Chat"}
                if entry not in st.session_state.saved_questions:
                    st.session_state.saved_questions.append(entry)
                    st.success("Saved!")
    with col_c:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GENERATE
# ══════════════════════════════════════════════════════════════════════════════
with tab_gen:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### Choose a Theme")
        selected_theme = st.selectbox("Theme", THEMES, label_visibility="collapsed")
        generate_btn = st.button("✨ Generate Question", type="primary", use_container_width=True, disabled=not api_key)

        if generate_btn and api_key:
            with st.spinner("Generating..."):
                try:
                    client = get_client(api_key)
                    q = generate_question(selected_theme, client)
                    st.session_state.generated_question = q
                    _save_to_sheets(selected_theme, q)
                except anthropic.AuthenticationError:
                    st.error("Invalid API key.")
                except anthropic.RateLimitError:
                    st.error("Rate limit hit — wait a moment.")
                except anthropic.APIError as e:
                    st.error(f"API error: {e}")

    with col2:
        if st.session_state.generated_question:
            st.markdown("### Generated Question")
            st.markdown(f'<div class="question-card">{st.session_state.generated_question}</div>', unsafe_allow_html=True)
            col_save, col_dl = st.columns(2)
            with col_save:
                if st.button("⭐ Save", use_container_width=True):
                    entry = {"question": st.session_state.generated_question, "theme": selected_theme}
                    if entry not in st.session_state.saved_questions:
                        st.session_state.saved_questions.append(entry)
                        st.success("Saved!")
            with col_dl:
                st.download_button("📋 Download", data=st.session_state.generated_question, file_name="rsa_question.txt", mime="text/plain", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — BROWSE
# ══════════════════════════════════════════════════════════════════════════════
with tab_browse:
    st.markdown("### Browse All Questions")
    bcol1, bcol2 = st.columns([2, 1])
    with bcol1:
        search_query = st.text_input("🔍 Search", placeholder="e.g. cheating, marriage, Instagram...")
    with bcol2:
        season_options = ["All Seasons"] + sorted(set(q["season"] for q in QUESTIONS))
        selected_season = st.selectbox("Season", season_options)

    filtered = QUESTIONS
    if search_query:
        filtered = [q for q in filtered if search_query.lower() in q["question"].lower()]
    if selected_season != "All Seasons":
        filtered = [q for q in filtered if q["season"] == selected_season]

    st.markdown(f"**{len(filtered)} questions found**")
    for q in filtered[:100]:
        with st.expander(f"Ep {q['episode_num']} Q{q['question_num']} — {q['episode_title']} | {q['date']}", expanded=False):
            st.markdown(f'<div class="ep-header">Panel: {q["panel"]} &nbsp;|&nbsp; <span class="badge">{q["season"]}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="question-card">{q["question"]}</div>', unsafe_allow_html=True)
    if len(filtered) > 100:
        st.info(f"Showing first 100 of {len(filtered)}. Refine your search.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SAVED
# ══════════════════════════════════════════════════════════════════════════════
with tab_saved:
    st.markdown("### Saved Questions")
    if not st.session_state.saved_questions:
        st.info("No saved questions yet. Generate some and click ⭐ Save!")
    else:
        st.markdown(f"**{len(st.session_state.saved_questions)} saved**")
        all_text = ("\n\n" + "=" * 60 + "\n\n").join(
            f"[{i+1}] {s['theme']}\n\n{s['question']}"
            for i, s in enumerate(st.session_state.saved_questions)
        )
        st.download_button("📥 Download All", data=all_text, file_name="rsa_saved_questions.txt", mime="text/plain")
        for i, saved in enumerate(st.session_state.saved_questions):
            with st.expander(f"[{i+1}] {saved['theme']} — {saved['question'][:60]}...", expanded=False):
                st.markdown(f'<div class="question-card">{saved["question"]}</div>', unsafe_allow_html=True)
                if st.button("🗑️ Remove", key=f"del_{i}"):
                    st.session_state.saved_questions.pop(i)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — FEEDBACK
# ══════════════════════════════════════════════════════════════════════════════
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "feedback_log.json")


def _get_supabase():
    try:
        from supabase import create_client
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None


def load_feedback():
    client = _get_supabase()
    if client:
        try:
            resp = client.table("feedback").select("*").order("created_at", desc=False).execute()
            return resp.data
        except Exception:
            pass
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_feedback(entry):
    client = _get_supabase()
    if client:
        try:
            client.table("feedback").insert(entry).execute()
            return
        except Exception:
            pass
    entries = load_feedback()
    entries.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(entries, f, indent=2)


with tab_feedback:
    st.markdown("### 📝 Team Feedback")
    st.caption("Rate generated questions, suggest improvements, and help make the AI better.")

    st.markdown("#### Submit Feedback on a Generated Question")

    with st.form("feedback_form"):
        fb_name = st.text_input("Your name / initials", placeholder="e.g. Raunaq, Team KSH, RR...")

        fb_question = st.text_area(
            "Paste the generated question here",
            placeholder="Paste the question you want to give feedback on...",
            height=120,
        )

        fb_rating = st.select_slider(
            "How good is this question? (1 = terrible, 5 = perfect)",
            options=[1, 2, 3, 4, 5],
            value=3,
        )

        fb_what_wrong = st.multiselect(
            "What's wrong with it? (select all that apply)",
            [
                "Not funny enough",
                "Too generic / boring",
                "Doesn't feel like a real RSA question",
                "Wrong format / structure",
                "Too short",
                "Too long",
                "Twist isn't surprising enough",
                "Not Indian enough",
                "Great — nothing wrong!",
            ],
        )

        fb_better_version = st.text_area(
            "Suggest a better version or what you'd change (optional)",
            placeholder="e.g. 'Make the twist more absurd' or paste a rewritten version...",
            height=100,
        )

        fb_theme_worked = st.radio(
            "Did the theme / prompt produce what you wanted?",
            ["Yes", "Partially", "No"],
            horizontal=True,
        )

        fb_extra = st.text_input("Anything else to improve the AI?", placeholder="Free text...")

        submitted = st.form_submit_button("Submit Feedback ✓", type="primary", use_container_width=True)

    if submitted:
        if not fb_question.strip():
            st.error("Please paste a question to give feedback on.")
        else:
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "name": fb_name.strip() or "Anonymous",
                "question": fb_question.strip(),
                "rating": fb_rating,
                "issues": fb_what_wrong,
                "better_version": fb_better_version.strip(),
                "theme_worked": fb_theme_worked,
                "extra_notes": fb_extra.strip(),
            }
            save_feedback(entry)
            st.success("Feedback saved!")
            st.balloons()

    st.markdown("---")

    all_fb = load_feedback()
    st.markdown(f"#### All Feedback ({len(all_fb)} entries)")

    if not all_fb:
        st.info("No feedback yet. Generate a question, then come here to rate it!")
    else:
        ratings = [f["rating"] for f in all_fb]
        avg = sum(ratings) / len(ratings)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Feedback", len(all_fb))
        col2.metric("Avg Rating", f"{avg:.1f} / 5")
        col3.metric("5-Star Count", ratings.count(5))

        from collections import Counter
        all_issues = [issue for f in all_fb for issue in f.get("issues", [])]
        if all_issues:
            st.markdown("**Most common issues:**")
            for issue, count in Counter(all_issues).most_common(5):
                st.markdown(f"- `{issue}` — {count}x")

        st.markdown("---")

        for i, fb in enumerate(reversed(all_fb)):
            stars = "⭐" * fb["rating"] + "☆" * (5 - fb["rating"])
            label = f"[{fb['timestamp']}] {fb['name']} — {stars} — {fb['question'][:50]}..."
            with st.expander(label, expanded=False):
                st.markdown(f"**Rating:** {stars} ({fb['rating']}/5)")
                st.markdown(f"**By:** {fb['name']} &nbsp;|&nbsp; **Theme worked:** {fb['theme_worked']}")
                if fb["issues"]:
                    st.markdown(f"**Issues:** {', '.join(fb['issues'])}")
                st.markdown("**Question rated:**")
                st.markdown(f'<div class="question-card">{fb["question"]}</div>', unsafe_allow_html=True)
                if fb.get("better_version"):
                    st.markdown("**Suggested improvement:**")
                    st.markdown(f'<div class="question-card">{fb["better_version"]}</div>', unsafe_allow_html=True)
                if fb.get("extra_notes"):
                    st.markdown(f"**Extra notes:** {fb['extra_notes']}")

        fb_text = json.dumps(all_fb, indent=2)
        st.download_button(
            "📥 Download All Feedback (JSON)",
            data=fb_text,
            file_name="rsa_feedback.json",
            mime="application/json",
        )
