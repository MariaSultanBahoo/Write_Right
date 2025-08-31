
# ✍️ Write Right – AI Grammar & Style Corrector

**Write Right** is a Streamlit-based web app that helps users **detect and correct grammatical, spelling, and stylistic errors** in their writing.  
Powered by **Google Gemini API**, it not only fixes mistakes but also **highlights errors and corrections interactively** with tooltips for better learning.  

---

## 🚀 Features
- ✅ **Grammar & Spell Checking** – identifies common mistakes.  
- ✅ **Style Suggestions** – improves sentence flow and clarity.  
- ✅ **Interactive Highlights** – mistakes (🔴 red) and corrections (🟢 green).  
- ✅ **Tooltip Explanations** – hover to see why it’s wrong.  
- ✅ **Side-by-Side View** – compare original vs corrected text.  
- ✅ **Custom Background & Styling** – clean UI with skin-colored background image.  

---

## ⚙️ Tech Stack
- **Python 3.9+**
- **Streamlit** (frontend framework)  
- **Google Gemini API** (for grammar/style correction)  
- **CSS** (for background + highlights)  

---

## 🔑 Setup Instructions

### 1️⃣ Clone the repo
```bash
git clone https://github.com/your-username/write-right.git
cd write-right
````

### 2️⃣ Create & activate virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements
```

### 4️⃣ Add API Key

Create a `.env` file in the root directory and add:

```
GEMINI_API_KEY=your_api_key_here
```

### 5️⃣ Run the app

```bash
streamlit run app.py
```

---

## 💡 Usage

1. Enter your paragraph in the text box.
2. Click **Analyze** to detect mistakes.
3. View **Original vs Corrected text** side by side.
4. Hover on highlights to see explanations.
5. Use **Clear Chat** to reset and try again.

---

## 🎯 Future Improvements

* 🌍 Multi-language support
* 📑 Export to Word/PDF
* 🔍 Plagiarism detection
* 🎨 More UI customization

---

## 👩‍💻 Author

Developed by **\[Maria Sultan]** 
