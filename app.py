import streamlit as st

from pdf_utils import extract_text_from_pdf


st.set_page_config(page_title="Study Coach Agent", page_icon="📚")

st.title("📚 Study Coach Agent")
st.caption("Step 1 · Upload a PDF and preview its text")

uploaded_file = st.file_uploader("Upload your course PDF", type=["pdf"])

if uploaded_file is None:
    st.info("Please upload a PDF to begin.")
else:
    try:
        with st.spinner("Reading the PDF..."):
            pages = extract_text_from_pdf(uploaded_file)

        total_characters = sum(len(page["text"]) for page in pages)
        st.success(
            f"Finished: {len(pages)} pages, {total_characters:,} characters extracted."
        )

        if total_characters == 0:
            st.warning(
                "No text was found. This may be a scanned PDF; OCR will be added later."
            )
        else:
            page_number = st.selectbox(
                "Choose a page to preview",
                options=[page["page_number"] for page in pages],
            )
            selected_page = next(
                page for page in pages if page["page_number"] == page_number
            )
            st.text_area(
                "Extracted text",
                value=selected_page["text"],
                height=420,
            )
    except Exception as error:
        st.error(f"The PDF could not be read: {error}")

