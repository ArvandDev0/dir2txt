# dir2txt

A lightweight Python tool that converts an entire project (or folder) into a single .txt file, optimized for Large Language Models (LLMs) such as ChatGPT, Claude, or Gemini.

---

## 📥 Installation

```bash
git clone https://github.com/ArvandDev0/dir2txt
cd dir2txt/src
```

---

## 🔧 Requirements  
- Python **3.8+**  
- No external libraries required. 

---

## 🚀 Usage

```bash
python3 dir2txt.py <input_directory> <output_file> [options]
```

Options

`-i`, `--ignore` → Comma-separated list of ignored files/folders.

`-d`, `--description` → Add a description at the end of the output.

---

### Example

```bash
python3 dir2txt.py . myproject.txt -i /.venv/ -d "Hi GPT. What is the problem with my code?"
```

Sample Output:

```text
Project structure
. Files that were selected:
|
├── main.py
├── README.md
└── utils/
    └── helper.py

2 directories, 3 files

---

Description
Hi GPT. What is the problem with my code?

---

./main.py
[content file]

---

./utils/helper.py
[content file]

---

./README.md
[content file]

``` 

---

## 💡 Features

- Merge all project files into one text file.

- Generate a tree view of the project structure (with directory & file counts).

- Ignore unwanted files or directories (`.git`, `__pycache__`, `.venv`, etc.).

- Add a custom project description at the end of the output.

- Supports reading from compressed archives (`.zip`, `.tar`, `.gz`, `.bz2`, `.xz`).

- Handles large files by skipping, truncating, or limiting the number of lines (configurable).

- Output format is designed to be clean, Markdown-friendly, and AI-readable.

- Pure Python, no external dependencies (standard library only).

---

## ✅ Why is this useful for LLMs?  
- LLMs perform best when the **entire codebase is in one file**.  
- The **tree view** helps AI understand the **project structure**.  
- Large/binary files are automatically summarized → avoids token overload.  
- Markdown formatting ensures the output is **clean and structured** for AI parsing.  
- Works great for **AI code review, debugging, documentation, or refactoring**.  

---

👉 With `dir2txt`, preparing your projects for AI assistance becomes simple and efficient.  