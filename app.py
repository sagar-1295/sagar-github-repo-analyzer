import re

import streamlit as st

from agent import MODEL, run_agent


def parse_repo_input(value: str) -> tuple[str, str]:
    cleaned = (value or "").strip().strip("/")
    if not cleaned:
        return "", ""

    if cleaned.startswith(("http://", "https://")):
        match = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", cleaned)
        if match:
            return match.group(1), match.group(2)
        return "", ""

    parts = [part for part in cleaned.split("/") if part]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return "", ""


st.set_page_config(page_title="GitHub Repo Analyzer", page_icon="🧠", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("Sagar's GitHub Repo Analyzer")
st.caption(f"Using {MODEL} via LiteLLM and MCP tools")

with st.sidebar:
    st.header("Settings")
    repo_input = st.text_input(
        "Repository",
        value="https://github.com/facebook/react",
        help="Enter a full GitHub URL or an owner/repo value.",
    )
    owner, repo = parse_repo_input(repo_input)
    if owner and repo:
        st.success(f"Repository detected: {owner}/{repo}")
    else:
        st.warning("Enter a valid GitHub URL or owner/repo value.")
    st.info(f"Active model: {MODEL}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about this repository...")
if prompt:
    if not owner or not repo:
        st.error("Please provide a valid GitHub repository URL or owner/repo value.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing the repository..."):
            response = run_agent(prompt, owner, repo)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
