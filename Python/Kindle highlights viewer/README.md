# 📚 Kindle Highlights Viewer

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-%3E%3D1.20-orange)

A simple and intuitive local Streamlit app to view, search, and manage your Kindle `My Clippings.txt` highlights. Keep all your notes and highlights organised and accessible in one place.

---
<img width="1253" height="877" alt="Screenshot 2025-10-30 at 05 15 50" src="https://github.com/user-attachments/assets/19a3ab73-d42f-41a7-8dae-5a33f10e5bdb" />


## 🚀 Features

- **Random Highlight**: Displays a random highlight at the top.  
- **Library view**: Shows all books with cover images, total highlights, and a sneak peek of one highlight.  
- **Search & Filter**: Find highlights by keywords, book title, author, or type (Highlight, Note, Bookmark).  
- **Flat Search Results**: View all highlights matching a search term across all books.  
- **Download Options**: Export highlights as **CSV** or **Markdown**.  
- **Compact Layout**: Clean interface with optimized spacing.  
- **Navigation**: "Go to Top" button for easy scrolling.

---

## 📦 How to Use

1. **Download the project** from GitHub as a ZIP file and extract it anywhere on your computer.

2. **Install Python 3.10 or higher** if you don't have it:  
   [Python Downloads](https://www.python.org/downloads/)

3. **Install required packages**:

   Open a terminal or command prompt in the project folder and run:

   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app**:
   
   ```bash
   streamlit run app.py
   ```

5. **Upload your Kindle `My Clippings.txt`** file when prompted. The app will automatically parse and display your highlights.

---

## 🗂 Project Structure


```bash
Kindle-Highlights-Viewer/
├── app.py                 # Main Streamlit app
├── README.md              # This file
├── requirements.txt       # Python dependencies
└── My Clippings.txt       # Your Kindle highlights file (sample included in repo)
```
---

## 🔧 Dependencies

* Python 3.10+
* Streamlit
* pandas
* requests
* Pillow (PIL)

---

## 📄 License

This project is licensed under the MIT License.

---

`Tip: You can use your existing My Clippings.txt from your Kindle. No internet connection is required for the app to display your highlights, except to fetch book covers.`

---



























