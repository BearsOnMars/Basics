# app.py
import re
import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from PIL import Image
from pathlib import Path

# ---------- Parsing ----------
def parse_clippings(file_path):
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    entries = content.split("==========")
    data = []
    for entry in entries:
        lines = [line.strip("﻿").strip() for line in entry.strip().splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        book_line = lines[0]
        meta_line = lines[1].lower()
        kind = next((t.capitalize() for t in ["highlight", "note", "bookmark"] if t in meta_line), "Unknown")
        loc_match = re.search(r'location ([\d-]+)', meta_line)
        location = loc_match.group(1) if loc_match else "0"
        date_match = re.search(r'added on (.*)', meta_line)
        date = date_match.group(1).strip() if date_match else ""
        text = "\n".join(lines[2:]).strip()
        if not text or "you have reached the clipping limit" in text.lower():
            continue
        data.append({
            "Book": book_line,
            "Type": kind,
            "Location": location,
            "Date Added": date,
            "Text": text
        })
    df = pd.DataFrame(data)
    if not df.empty:
        df.drop_duplicates(subset=["Book", "Type", "Location", "Text"], inplace=True)
        df["NumericLocation"] = df["Location"].apply(lambda x: int(x.split('-')[0]) if x else 0)
        df.sort_values(by=["Book", "NumericLocation"], inplace=True)
    return df

# ---------- Cached Parsing ----------
@st.cache_data(show_spinner=False)
def get_parsed_clippings(file_path):
    return parse_clippings(file_path)

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def fetch_cover(book_title):
    try:
        resp = requests.get(f"https://openlibrary.org/search.json?title={requests.utils.quote(book_title)}", timeout=8)
        data = resp.json()
        if "docs" in data and len(data["docs"]) > 0:
            doc = data["docs"][0]
            cover_id = doc.get("cover_i")
            if cover_id:
                img_data = requests.get(f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg", timeout=8).content
                return Image.open(BytesIO(img_data))
        gbooks_resp = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(book_title)}", timeout=8)
        gbooks = gbooks_resp.json()
        if "items" in gbooks and len(gbooks["items"]) > 0:
            img_url = gbooks["items"][0]["volumeInfo"].get("imageLinks", {}).get("thumbnail")
            if img_url:
                img_data = requests.get(img_url, timeout=8).content
                return Image.open(BytesIO(img_data))
    except Exception:
        pass
    return None

# ---------- Display ----------
def show_random_highlight(df, search_query=""):
    if df.empty:
        return
    highlight = df.sample(1).iloc[0]
    emoji = {"Highlight": "🖊️", "Note": "📓", "Bookmark": "📍"}.get(highlight["Type"], "📘")
    text = highlight['Text']
    if search_query:
        text = re.sub(f"({re.escape(search_query)})", r"<mark>\1</mark>", text, flags=re.I)
    st.markdown("### 🎲 Random Highlight")
    st.markdown(f"**{emoji} {highlight['Type']} — {highlight['Book']} — Location {highlight['Location']}**")
    st.markdown(f"> {text}", unsafe_allow_html=True)
    st.markdown("---")

def render_book_list(df, search_query=""):
    books = sorted(df["Book"].unique())
    if not books:
        st.info("No books found.")
        return

    for idx, book in enumerate(books):
        book_df = df[df["Book"] == book]
        if search_query:
            highlights_matching = book_df[book_df["Text"].str.contains(search_query, case=False, na=False)]
        else:
            highlights_matching = book_df

        highlights_count = len(highlights_matching)
        if highlights_matching.empty:
            continue

        first_highlight = highlights_matching.iloc[0]["Text"]
        sneak_preview = first_highlight if len(first_highlight) <= 100 else first_highlight[:97] + "..."

        if search_query:
            sneak_preview = re.sub(f"({re.escape(search_query)})", r"<mark>\1</mark>", sneak_preview, flags=re.I)

        cover = fetch_cover(book)
        cols = st.columns([1, 4])
        with cols[0]:
            if cover:
                st.image(cover, width="stretch")
            else:
                st.image("https://via.placeholder.com/100x150?text=No+Cover", width="stretch")
        with cols[1]:
            st.markdown(f"### {book}")
            st.caption(f"🖊️ {highlights_count} highlight(s) matching")
            st.markdown(f"> {sneak_preview}", unsafe_allow_html=True)
            if st.button("View Highlights", key=f"btn_{idx}"):
                st.session_state.selected_book = book

        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

def show_book_highlights(df, book, search_query=""):
    st.markdown('<a id="top"></a>', unsafe_allow_html=True)

    if st.button("⬅ Back to Library"):
        st.session_state.selected_book = None
        return

    book_df = df[df["Book"] == book].sort_values(by="NumericLocation")
    if search_query:
        book_df = book_df[book_df["Text"].str.contains(search_query, case=False, na=False)]

    st.markdown(f"## {book}")
    st.markdown(f"**Total notes/highlights:** {len(book_df)}")
    st.markdown("---")

    for _, row in book_df.iterrows():
        emoji = {"Highlight": "🖊️", "Note": "📓", "Bookmark": "📍"}.get(row["Type"], "📘")
        text = row["Text"]
        if search_query:
            text = re.sub(f"({re.escape(search_query)})", r"<mark>\1</mark>", text, flags=re.I)
        st.markdown(f"**{emoji} {row['Type']} — _Location {row['Location']}_ — {row['Date Added']}**")
        st.markdown(f"> {text}", unsafe_allow_html=True)
        st.markdown("---")

    st.markdown('<a href="#top"><button style="padding:5px 10px;">🔝 Go to Top</button></a>', unsafe_allow_html=True)

    st.download_button(
        "💾 Download Highlights as CSV",
        data=book_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{book.replace('/', '_')}_highlights.csv",
        mime="text/csv"
    )

    markdown_text = f"# {book}\n\n"
    for _, row in book_df.iterrows():
        emoji = {"Highlight": "🖊️", "Note": "📓", "Bookmark": "📍"}.get(row["Type"], "📘")
        markdown_text += f"**{emoji} {row['Type']} (Location {row['Location']}) — _{row['Date Added']}_**\n\n"
        markdown_text += f"> {row['Text']}\n\n---\n\n"

    st.download_button(
        "💾 Download Highlights as Markdown",
        data=markdown_text.encode("utf-8"),
        file_name=f"{book.replace('/', '_')}_highlights.md",
        mime="text/markdown"
    )

def show_flat_search_results(df, query):
    if df.empty:
        st.info("No highlights found for this search term.")
        return
    st.markdown(f"### 🔎 All Highlights for '{query}'")
    st.markdown(f"**Total matching highlights:** {len(df)}")
    for _, row in df.iterrows():
        emoji = {"Highlight": "🖊️", "Note": "📓", "Bookmark": "📍"}.get(row["Type"], "📘")
        highlighted_text = re.sub(f"({re.escape(query)})", r"<mark>\1</mark>", row["Text"], flags=re.I)
        st.markdown(f"**{emoji} {row['Type']} — {row['Book']} — Location {row['Location']} — {row['Date Added']}**")
        st.markdown(f"> {highlighted_text}", unsafe_allow_html=True)
        st.markdown("---")

# ---------- Main ----------
def main():
    st.set_page_config(page_title="Kindle Highlights Hub", layout="centered")

    st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] { margin-top: 4px; margin-bottom: 4px; padding: 2px 0px; }
    hr { margin: 2px 0px; }
    mark { background-color: #ffff00; color: black; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📚 Kindle Highlights Hub")
    st.caption("Local, searchable viewer for your Kindle 'My Clippings.txt'")

    uploaded = st.file_uploader("Upload your My Clippings.txt", type="txt")
    if uploaded:
        tmp_path = Path("uploaded_clippings.txt")
        tmp_path.write_bytes(uploaded.getbuffer())
        source_path = tmp_path
    else:
        local = Path("My Clippings.txt")
        source_path = local if local.exists() else None

    if not source_path:
        st.info("No clippings file found. Upload one or place it locally.")
        return

    df = get_parsed_clippings(source_path)
    if df.empty:
        st.warning("Parsed 0 entries. Check file validity.")
        return

    st.sidebar.header("Filters & Options")
    q = st.sidebar.text_input("Search text")
    book_query = st.sidebar.text_input("Filter by title/author")
    type_filter = st.sidebar.multiselect("Type", sorted(df["Type"].unique()), default=list(df["Type"].unique()))

    df_filtered = df[df["Type"].isin(type_filter)]
    if book_query:
        df_filtered = df_filtered[df_filtered["Book"].str.contains(book_query, case=False, na=False)]

    st.sidebar.write(f"Entries: {len(df_filtered)}")

    if "selected_book" not in st.session_state:
        st.session_state.selected_book = None

    # If a book is selected
    if st.session_state.selected_book and st.session_state.selected_book in df_filtered["Book"].unique():
        show_book_highlights(df_filtered, st.session_state.selected_book, search_query=q)
    else:
        # Show random highlight filtered by search term if any
        if q:
            df_search = df_filtered[df_filtered["Text"].str.contains(q, case=False, na=False)]
            show_random_highlight(df_search, search_query=q)
            st.subheader("Library (Books with matches)")
            render_book_list(df_filtered, search_query=q)
            show_flat_search_results(df_search, q)
        else:
            show_random_highlight(df_filtered)
            st.subheader("Library")
            render_book_list(df_filtered)

if __name__ == "__main__":
    main()
