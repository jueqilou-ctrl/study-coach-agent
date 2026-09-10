import html

import streamlit as st

from deepseek_client import run_study_agent
from pdf_utils import extract_text_from_pdf, split_text_into_chunks


st.set_page_config(
    page_title="Study Coach Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 85% 5%, rgba(124, 92, 255, 0.12), transparent 28%),
                radial-gradient(circle at 15% 95%, rgba(41, 182, 246, 0.10), transparent 26%),
                #f7f8fc;
        }
        .block-container {
            max-width: 980px;
            padding-top: 2rem;
            padding-bottom: 7rem;
        }
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.92);
            border-right: 1px solid #e8eaf1;
        }
        .hero-card {
            padding: 1.7rem 1.8rem;
            border: 1px solid rgba(124, 92, 255, 0.14);
            border-radius: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f3f0ff 100%);
            box-shadow: 0 14px 40px rgba(43, 38, 72, 0.08);
            margin-bottom: 1.3rem;
        }
        .hero-eyebrow {
            color: #6d5ce7;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .hero-title {
            color: #25243a;
            font-size: 2.25rem;
            font-weight: 750;
            line-height: 1.15;
            margin: 0.35rem 0 0.55rem;
        }
        .hero-copy {
            color: #65657a;
            font-size: 1rem;
            margin: 0;
        }
        .status-card {
            padding: 0.9rem 1rem;
            border-radius: 14px;
            background: #f4f1ff;
            border: 1px solid #e4ddff;
            color: #4d4675;
            margin: 0.5rem 0 1rem;
        }
        .source-card {
            padding: 0.8rem 0.9rem;
            border-radius: 12px;
            background: #f8f8fc;
            border: 1px solid #ececf3;
            margin-bottom: 0.6rem;
        }
        div[data-testid="stChatMessage"] {
            border: 1px solid rgba(224, 225, 235, 0.9);
            border-radius: 18px;
            padding: 0.35rem 0.55rem;
            background: rgba(255, 255, 255, 0.72);
        }
        div.stButton > button {
            border-radius: 12px;
            border: 1px solid #dedbea;
            min-height: 2.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def welcome_message(content: str) -> dict:
    return {
        "role": "assistant",
        "content": content,
        "sources": [],
        "tools": [],
    }


def initialise_state() -> None:
    """Create values that should survive Streamlit reruns."""

    if "messages" not in st.session_state:
        st.session_state.messages = [
            welcome_message(
                "你好，我是你的 Study Coach。上传课程 PDF 后，"
                "你可以让我解释知识点、总结资料、生成测验或制定学习计划。"
            )
        ]

    if "document_id" not in st.session_state:
        st.session_state.document_id = None

    if "pages" not in st.session_state:
        st.session_state.pages = []

    if "chunks" not in st.session_state:
        st.session_state.chunks = []


def reset_chat() -> None:
    st.session_state.messages = [
        welcome_message("对话已清空。你想从这份课程资料中学习什么？")
    ]


def unique_sources(
    sources: list[dict[str, int | str]],
) -> list[dict[str, int | str]]:
    """Remove repeated source chunks while keeping their original order."""

    seen_ids: set[int | str] = set()
    unique: list[dict[str, int | str]] = []

    for source in sources:
        chunk_id = source["chunk_id"]

        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique.append(source)

    return unique


def show_sources(sources: list[dict[str, int | str]]) -> None:
    """Display supporting chunks below an assistant response."""

    if not sources:
        return

    with st.expander(f"View {len(sources)} course sources"):
        for source in sources:
            safe_text = html.escape(str(source["text"]))
            st.markdown(
                (
                    '<div class="source-card">'
                    f"<strong>Chunk {source['chunk_id']}</strong><br>"
                    f"{safe_text}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def show_agent_actions(tools: list[str]) -> None:
    if not tools:
        return

    tool_labels = {
        "search_course": "searched relevant course sections",
        "read_course_content": "read the broader course content",
    }
    readable_tools = [
        tool_labels.get(tool, tool)
        for tool in dict.fromkeys(tools)
    ]
    st.caption("Agent action: " + " · ".join(readable_tools))


initialise_state()


with st.sidebar:
    st.markdown("## 📚 Study Coach")
    st.caption("Your course, explained your way")

    uploaded_file = st.file_uploader(
        "Upload course material",
        type=["pdf"],
        help="Text-based PDF files work best. Scanned PDFs need OCR.",
    )

    if uploaded_file is not None:
        document_id = f"{uploaded_file.name}:{uploaded_file.size}"

        if document_id != st.session_state.document_id:
            try:
                with st.spinner("Preparing your course..."):
                    pages = extract_text_from_pdf(uploaded_file)
                    chunks = split_text_into_chunks(pages)

                total_characters = sum(
                    len(str(page["text"]))
                    for page in pages
                )

                st.session_state.document_id = document_id
                st.session_state.pages = pages
                st.session_state.chunks = chunks
                reset_chat()

                if total_characters == 0:
                    st.warning(
                        "No text was found. This may be a scanned PDF."
                    )

            except Exception as error:
                st.session_state.document_id = None
                st.session_state.pages = []
                st.session_state.chunks = []
                st.error(f"The PDF could not be read: {error}")

        if st.session_state.chunks:
            st.markdown(
                (
                    '<div class="status-card">'
                    "<strong>✓ Course ready</strong><br>"
                    f"{len(st.session_state.pages)} pages · "
                    f"{len(st.session_state.chunks)} chunks"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            with st.expander("Preview extracted text"):
                preview_page = st.selectbox(
                    "Page",
                    options=[
                        page["page_number"]
                        for page in st.session_state.pages
                    ],
                )

                selected_page = next(
                    page
                    for page in st.session_state.pages
                    if page["page_number"] == preview_page
                )

                st.text_area(
                    "Page text",
                    value=str(selected_page["text"]),
                    height=220,
                    disabled=True,
                )

    else:
        st.session_state.document_id = None
        st.session_state.pages = []
        st.session_state.chunks = []
        st.info("Upload a PDF to activate the course tools.")

    st.divider()

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        reset_chat()
        st.rerun()

    st.caption(
        "Your API key stays in the local .env file and is not shown here."
    )


st.markdown(
    """
    <div class="hero-card">
        <div class="hero-eyebrow">AI LEARNING WORKSPACE</div>
        <div class="hero-title">Turn course material into understanding.</div>
        <p class="hero-copy">
            Ask naturally. Your agent can search, explain, summarise,
            create quizzes and plan your next study session.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


quick_prompt: str | None = None
quick_columns = st.columns(4)

quick_actions = [
    ("✨ Summarise", "请总结这份课程资料的核心内容，并列出重点。"),
    ("🧠 Explain", "请找出这份资料最重要的概念，并用简单例子解释。"),
    ("✅ Make a quiz", "请根据课程资料生成5道测验题，暂时不要给答案。"),
    ("🗓️ Study plan", "请根据课程资料制定一个3天学习计划。"),
]

for column, (label, prompt_text) in zip(
    quick_columns,
    quick_actions,
):
    with column:
        if st.button(
            label,
            use_container_width=True,
            disabled=not bool(st.session_state.chunks),
        ):
            quick_prompt = prompt_text


st.divider()


for message in st.session_state.messages:
    avatar = "🧑‍🎓" if message["role"] == "user" else "📚"

    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        show_agent_actions(message.get("tools", []))
        show_sources(message.get("sources", []))


typed_prompt = st.chat_input(
    (
        "Ask about your course, request a quiz, or make a study plan..."
        if st.session_state.chunks
        else "Upload a PDF in the sidebar to start chatting"
    ),
    disabled=not bool(st.session_state.chunks),
)

prompt = quick_prompt or typed_prompt


if prompt:
    history_before_prompt = list(st.session_state.messages)

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
            "sources": [],
            "tools": [],
        }
    )

    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="📚"):
        try:
            with st.spinner("Study Coach is working..."):
                answer, sources, tools = run_study_agent(
                    user_message=prompt,
                    chunks=st.session_state.chunks,
                    conversation_history=history_before_prompt,
                )

            sources = unique_sources(sources)
            st.markdown(answer)
            show_agent_actions(tools)
            show_sources(sources)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "tools": tools,
                }
            )

        except Exception as error:
            error_message = f"Study Coach request failed: {error}"
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "sources": [],
                    "tools": [],
                }
            )