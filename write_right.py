import os
import re
import json
import difflib
from datetime import datetime

import streamlit as st
import pandas as pd
import google.generativeai as genai

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("⚠️ Gemini API key not found. Please set GEMINI_API_KEY in your .env file.")

# --------------------------- CONFIG ---------------------------
st.set_page_config(page_title="WriteRight — Gemini", page_icon="📝", layout="wide")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    st.warning("Set environment variable **GEMINI_API_KEY** to use the app.")
genai.configure(api_key=GEMINI_API_KEY)

DEFAULT_MODEL = "gemini-1.5-flash"

# --------------------------- STYLES ---------------------------
st.markdown("""
<style>
/* Background Image */
[data-testid="stAppViewContainer"] {
    background-image: url("https://wallpapers.com/images/featured/dark-gradient-background-6bly12umg2d4psr2.jpg");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

/* Transparent header */
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

/* Sidebar with dark overlay */
[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.7);
}

/* Title & subtitle */
.big-title { font-size: 34px; font-weight: 800; color: #7DC079; letter-spacing: -0.02em; }
.subtitle { color: #D4A79C; } 

/* Card boxes 
    background: rgba(0, 0, 0, 0.8); 
    border: 1px solid #374151; 
    border-radius: 16px; 
    padding: 16px; 
    color: #f9fafb; /* White text */
}

/* Result text */
.result { 
   color: #000000;;
    white-space: pre-wrap; 
    line-height: 1.7; 
    font-size: 1.04rem; 
    color: #f9fafb; 
}

/* Side by side layout */
.side-by-side { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

/* Highlight styles */
.hl-err {
    background: #ffe2e2;
    color: #b91c1c;  
    border-radius: 6px; 
    padding: 0 4px;
}
.hl-sug {
    background: #e6ffe6;
    color: #166534;  
    border-radius: 6px; 
    padding: 0 4px;
}

/* Tooltip styles */
.tooltip {
    background: #ffe2e2;
    color: #111827;
    border-radius:6px; 
    padding:0 4px; 
    position:relative; 
    cursor:help; 
}
.tooltip:hover::after {
    content: attr(data-tip);
    position:absolute; left:0; top:100%;
    background:#111827; color:#fff; padding:8px 10px;
    border-radius:8px; font-size:12px; white-space:pre-wrap; width:300px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15); z-index:5; margin-top:6px;
}

/* Badge */
small.badge { 
    border:1px solid #e2e8f0; 
    border-radius:999px; 
    padding:2px 8px; 
    color:#f9fafb;
}

/* Center button */
.center-button {
    display: flex;
    justify-content: center;
    align-items: center;
}


</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Options")
    model_name = st.selectbox("Model", [DEFAULT_MODEL, "gemini-1.5-pro"], index=0)
    max_retries = st.slider("Max retries (JSON enforcement)", 1, 5, 3)
    show_table = st.toggle("Show mistakes table", True)
    show_highlights = st.toggle("Show inline highlights", True)
    show_side_by_side = st.toggle("Show Original vs Corrected", True)
    show_semantics = st.toggle("Show semantic issues", True)
    st.markdown("---")
    if st.button("🧹 Clear Chat / Reset"):
        st.session_state.clear()
        st.rerun()

# --------------------------- HELPERS ---------------------------
def build_prompt(text: str) -> str:
    return f"""
You are a strict grammar checker.

Task:
- Find EVERY grammar, spelling, tense, plural/singular, punctuation, and sentence structure mistake.
- Return JSON ONLY.

Schema:
{{
  "corrected_text": "full corrected paragraph",
  "mistakes": [
    {{
      "error": "exact wrong word/phrase",
      "type": "Grammar/Spelling/Tense/Structure/Punctuation/Style",
      "suggestion": "the correct replacement",
      "explanation": "short reason"
    }}
  ]
}}

Text:
{text}
""".strip()

def build_semantic_prompt(text: str) -> str:
    return f"""
Check if the following text makes logical/semantic sense.
- If there is a contradiction or illogical statement, suggest a corrected version.
- Otherwise return "No semantic issues".

Text: "{text}"
""".strip()

def extract_json_loose(s: str) -> str:
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.MULTILINE).strip()
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return s[start:end+1]
    return s

def call_gemini_json(text: str, model_name: str, max_retries: int = 3) -> dict:
    model = genai.GenerativeModel(model_name)
    prompt = build_prompt(text)
    last_error = None
    for _ in range(max_retries):
        try:
            resp = model.generate_content(prompt)
            raw = (resp.text or "").strip()
            cleaned = extract_json_loose(raw)
            data = json.loads(cleaned)
            corrected = data.get("corrected_text", "").strip() or text
            mistakes = data.get("mistakes", [])
            if corrected.strip() == text.strip():
                last_error = "Validation: unchanged text"
                continue
            return {"corrected_text": corrected, "mistakes": mistakes}
        except Exception as e:
            last_error = str(e)
            continue
    return {"corrected_text": text, "mistakes": [{"error": "System", "type": "Parsing", "suggestion": "Retry", "explanation": last_error}]}

def call_gemini_semantic(text: str, model_name: str) -> str:
    model = genai.GenerativeModel(model_name)
    resp = model.generate_content(build_semantic_prompt(text))
    return (resp.text or "").strip()

def safe_inline_highlights(original: str, mistakes: list) -> str:
    spans, text = [], original
    for m in mistakes:
        err, sug, exp = m.get("error", ""), m.get("suggestion", ""), m.get("explanation", "")
        if not err: continue
        pattern = re.escape(err)
        for match in re.finditer(pattern, text):
            spans.append({"start": match.start(), "end": match.end(), "error": err, "suggestion": sug, "explanation": exp})
            break
    spans.sort(key=lambda x: x["start"])
    filtered, last_end = [], -1
    for s in spans:
        if s["start"] >= last_end:
            filtered.append(s); last_end = s["end"]
    out, idx = [], 0
    for s in filtered:
        out.append(original[idx:s["start"]])
        tip = f"✅ {s['suggestion']}\n— {s['explanation']}"
        out.append(f"<span class='tooltip' data-tip='{tip}'>{original[s['start']:s['end']]}</span>")
        idx = s["end"]
    out.append(original[idx:])
    return "".join(out)

def diff_html(a: str, b: str) -> tuple[str, str]:
    sm = difflib.SequenceMatcher(None, a, b)
    left, right = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            left.append(a[i1:i2]); right.append(b[j1:j2])
        elif tag == "replace":
            if i1 != i2: left.append(f"<span class='hl-err'>{a[i1:i2]}</span>")
            if j1 != j2: right.append(f"<span class='hl-sug'>{b[j1:j2]}</span>")
        elif tag == "delete":
            left.append(f"<span class='hl-err'>{a[i1:i2]}</span>")
        elif tag == "insert":
            right.append(f"<span class='hl-sug'>{b[j1:j2]}</span>")
    return "".join(left), "".join(right)

# --------------------------- UI ---------------------------
st.markdown("<div class='big-title'>📝 WriteRight — AI Grammar + Semantic Corrector</div>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Fix grammar, spelling, tense, & logical mistakes</p>", unsafe_allow_html=True)

text = st.text_area("✍️ Paste Your Paragraph:", value=st.session_state.get("last_text"), height=180, key="input_text")

if st.button("✨ Analyze & Correct"):
    text_in = text.strip()
    if not text_in:
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Analyzing your text…"):
            result = call_gemini_json(text_in, model_name=model_name, max_retries=max_retries)
            corrected = result.get("corrected_text", text_in)
            mistakes = result.get("mistakes", [])
            semantic_feedback = call_gemini_semantic(corrected, model_name) if show_semantics else "No semantic issues"

        st.session_state["last_text"] = text_in
        st.session_state["last_corrected"] = corrected

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Issues detected", f"{len(mistakes)}")
        with c2: st.metric("Words (in → out)", f"{len(text_in.split())} → {len(corrected.split())}")
        with c3: st.metric("Chars (in → out)", f"{len(text_in)} → {len(corrected)}")

        st.markdown("#### ✅ Corrected Paragraph")
        st.markdown(f"<div class='card result'>{corrected}</div>", unsafe_allow_html=True)

        if show_side_by_side:
            left_html, right_html = diff_html(text_in, corrected)
            st.markdown("#### 🧭 Original vs Corrected")
            st.markdown(f"<div class='side-by-side'><div class='card result'>{left_html}</div><div class='card result'>{right_html}</div></div>", unsafe_allow_html=True)

        if show_table:
            st.markdown("#### 🔍 Detected Mistakes")
            if mistakes and not (len(mistakes) == 1 and mistakes[0].get('type') == 'Parsing'):
                st.dataframe(pd.DataFrame(mistakes), use_container_width=True, hide_index=True)
            else:
                st.info("No major grammar mistakes found.")

        if show_highlights:
            st.markdown("#### 📌 Highlights")
            if mistakes: 
                hl_html = safe_inline_highlights(text_in, mistakes)
                st.markdown(f"<div class='card result'>{hl_html}</div>", unsafe_allow_html=True)
            else:
                st.info("Nothing to highlight.")

        if show_semantics and semantic_feedback != "No semantic issues":
            st.markdown("#### 🔎 Semantic Issues Found")
            st.markdown(f"<div class='card result'>{semantic_feedback}</div>", unsafe_allow_html=True)

        st.download_button(
            label="💾 Download Corrected Text",
            data=corrected,
            file_name=f"corrected_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )