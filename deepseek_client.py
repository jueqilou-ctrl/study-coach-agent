import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from retriever import search_chunks


load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise RuntimeError(
        "没有找到 DEEPSEEK_API_KEY，请检查 .env 文件。"
    )


client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_course",
            "description": (
                "Search the uploaded course PDF for chunks related to a topic "
                "or question. Use short and specific search terms."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords or a concise search query.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_course_content",
            "description": (
                "Read a broad selection of the uploaded PDF. Use this for "
                "summaries, study plans, quizzes, or when keyword search fails."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "purpose": {
                        "type": "string",
                        "description": "Why the course content is needed.",
                    }
                },
                "required": ["purpose"],
            },
        },
    },
]


def _search_course(
    query: str,
    chunks: list[dict[str, int | str]],
) -> tuple[str, list[dict[str, int | str]]]:
    """Execute the existing local retrieval function."""

    results = search_chunks(
        query=query,
        chunks=chunks,
        top_k=4,
    )

    if not results:
        return (
            json.dumps(
                {
                    "message": (
                        "No exact keyword match was found. "
                        "Try another query or call read_course_content."
                    ),
                    "results": [],
                },
                ensure_ascii=False,
            ),
            [],
        )

    return (
        json.dumps(
            {
                "results": [
                    {
                        "chunk_id": result["chunk_id"],
                        "text": result["text"],
                    }
                    for result in results
                ]
            },
            ensure_ascii=False,
        ),
        results,
    )


def _read_course_content(
    chunks: list[dict[str, int | str]],
    max_characters: int = 24_000,
) -> tuple[str, list[dict[str, int | str]]]:
    """Return course content while limiting API cost and context size."""

    selected_chunks: list[dict[str, int | str]] = []
    total_characters = 0

    for chunk in chunks:
        text = str(chunk["text"])

        if selected_chunks and total_characters + len(text) > max_characters:
            break

        selected_chunks.append(chunk)
        total_characters += len(text)

    content = {
        "note": (
            "The content may be truncated for a very large PDF."
            if len(selected_chunks) < len(chunks)
            else "All available chunks are included."
        ),
        "results": [
            {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
            }
            for chunk in selected_chunks
        ],
    }

    return (
        json.dumps(content, ensure_ascii=False),
        selected_chunks,
    )


def run_study_agent(
    user_message: str,
    chunks: list[dict[str, int | str]],
    conversation_history: list[dict[str, Any]] | None = None,
) -> tuple[str, list[dict[str, int | str]], list[str]]:
    """Let DeepSeek choose tools and return a grounded final response."""

    system_prompt = (
        "You are Study Coach, a conversational learning agent. "
        "Answer in the same language as the student. "
        "For any request about the uploaded course PDF, you must call a tool "
        "before answering. Use search_course for a focused question and "
        "read_course_content for summaries, quizzes, or study plans. "
        "If a search returns no match, try a better short query or call "
        "read_course_content. Explain concepts clearly and help the student "
        "take the next step. When course content is used, mention supporting "
        "chunk numbers such as [Chunk 2]. Never invent information that is "
        "not present in the tool result."
    )

    messages: list[Any] = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    for message in (conversation_history or [])[-8:]:
        if message.get("role") in {"user", "assistant"}:
            messages.append(
                {
                    "role": message["role"],
                    "content": str(message.get("content", "")),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    used_sources: list[dict[str, int | str]] = []
    used_tools: list[str] = []

    # Limit the loop so an unexpected response cannot call tools forever.
    for _ in range(3):
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            tools=AGENT_TOOLS,
            tool_choice="auto",
            stream=False,
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:
            answer = assistant_message.content or (
                "I could not generate an answer. Please try again."
            )
            return answer, used_sources, used_tools

        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments or "{}"
                )
            except json.JSONDecodeError:
                arguments = {}

            if tool_name == "search_course":
                tool_output, sources = _search_course(
                    query=str(arguments.get("query", user_message)),
                    chunks=chunks,
                )

            elif tool_name == "read_course_content":
                tool_output, sources = _read_course_content(chunks)

            else:
                tool_output = json.dumps(
                    {"error": f"Unknown tool: {tool_name}"}
                )
                sources = []

            used_tools.append(tool_name)
            used_sources.extend(sources)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )

    return (
        "The agent reached its tool-call limit. Please ask a more specific question.",
        used_sources,
        used_tools,
    )


def ask_deepseek(question: str, context: str) -> str:
    """Keep the original helper available for simple direct calls."""

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一名学习教练。"
                    "请只根据提供的课程资料回答问题。"
                    "如果资料不足，请明确说明无法从资料中找到答案。"
                    "请使用与学生问题相同的语言回答。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"课程资料：\n{context}\n\n"
                    f"学生问题：\n{question}"
                ),
            },
        ],
        stream=False,
    )

    return response.choices[0].message.content or ""
