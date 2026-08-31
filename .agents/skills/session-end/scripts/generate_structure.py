import os
import re
from datetime import datetime

# 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../../../"))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "ai_docs", "structure.md")
IGNORE_DIRS = {".git", "node_modules", "dist", ".vscode", "ai_docs", "reference", ".agents", "docs", ".venv", "venv", "__pycache__"}
TARGET_EXTENSIONS = {".js", ".ts", ".py"}

def get_tree(dir_path, prefix=""):
    tree_str = ""
    try:
        items = sorted(os.listdir(dir_path))
    except PermissionError:
        return ""
    
    items = [i for i in items if i not in IGNORE_DIRS]
    for index, item in enumerate(items):
        path = os.path.join(dir_path, item)
        is_last = (index == len(items) - 1)
        connector = "└── " if is_last else "├── "
        tree_str += f"{prefix}{connector}{item}\n"
        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            tree_str += get_tree(path, prefix=prefix + extension)
    return tree_str

def extract_functions(file_path):
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # JS, TS, PY 함수 추출
            pattern = re.compile(r'(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(|(?:async\s+)?function\s+([a-zA-Z_$][0-9a-zA-Z_$]*)\s*\(|const\s+([a-zA-Z_$][0-9a-zA-Z_$]*)\s*=\s*(?:async\s+)?\(?[^)]*\)?\s*=>')
            matches = pattern.findall(content)
            for m in matches:
                func_name = next((g for g in m if g), None)
                if func_name:
                    functions.append(func_name)
    except Exception:
        pass
    return list(dict.fromkeys(functions))

def generate_doc():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 🏗️ LG Aircon Raspberry Pi PoC Project Structure\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("### 🌳 Folder Tree\n```text\n")
        f.write(f"{os.path.basename(os.path.abspath(PROJECT_ROOT))}/\n")
        f.write(get_tree(PROJECT_ROOT))
        f.write("```\n\n")
        
        f.write("### 📂 주요 함수 목록\n")
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    funcs = extract_functions(file_path)
                    if funcs:
                        rel_path = os.path.relpath(file_path, PROJECT_ROOT).replace('\\', '/')
                        f.write(f"\n**[{rel_path}]**\n")
                        for func in funcs:
                            f.write(f"- {func}\n")
                        f.write("\n")

if __name__ == "__main__":
    generate_doc()
    print(f"Structure document generated at: {OUTPUT_FILE}")
    print("완료되었습니다.")