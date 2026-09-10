import streamlit as st

from pdf_utils import extract_text_from_pdf, split_text_into_chunks
from retriever import search_chunks

st.set_page_config(
    page_title="Study Coach Agent",
    page_icon="📚"
)

st.title("📚 Study Coach Agent")
st.caption("Step 2 · Extract and split PDF text")

uploaded_file = st.file_uploader(
    "Upload your course PDF",
    type=["pdf"]
)

if uploaded_file is None:
    st.info("Please upload a PDF to begin.")

else:
    try:
        with st.spinner("Reading the PDF..."):
            pages = extract_text_from_pdf(uploaded_file)
            chunks = split_text_into_chunks(pages)

        total_characters = sum(
            len(page["text"]) for page in pages
        )

        st.success(
            f"Finished: {len(pages)} pages, "
            f"{total_characters:,} characters, "
            f"{len(chunks)} chunks."
        )

        if total_characters == 0:
            st.warning(
                "No text was found. "
                "This may be a scanned PDF."
            )

        else:
            st.subheader("Page preview")

            page_number = st.selectbox(
                "Choose a page",
                options=[
                    page["page_number"]
                    for page in pages
                ],
            )

            selected_page = next(
                page
                for page in pages
                if page["page_number"] == page_number
            )

            st.text_area(
                "Extracted page text",
                value=selected_page["text"],
                height=250,
            )

            st.divider()
            st.subheader("Chunk preview")

            chunk_id = st.selectbox(
                "Choose a chunk",
                options=[
                    chunk["chunk_id"]
                    for chunk in chunks
                ],
            )

            selected_chunk = next(
                chunk
                for chunk in chunks
                if chunk["chunk_id"] == chunk_id
            )

            st.text_area(
                "Chunk text",
                value=selected_chunk["text"],
                height=250,
            )

    except Exception as error:
        st.error(f"The PDF could not be read: {error}")

st.divider()
st.subheader("Search course content")

query = st.text_input(
    "Enter a keyword or question"
)

if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a question.")

    else:
        results = search_chunks(
            query=query,
            chunks=chunks,
            top_k=3,
        )

        if not results:
            st.info("No relevant content was found.")

        else:
            for result in results:
                title = (
                    f"Chunk {result['chunk_id']} "
                    f"· Score: {result['score']}"
                )

                with st.expander(title):
                    st.write(result["text"])