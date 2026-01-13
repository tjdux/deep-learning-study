import os
import re
import json
import urllib.parse

# 설정
README_PATH = "README.md"
TOC_HEADER = "## 목차 (Table of Contents)"
TOC_MARKER_START = "<!-- TOC START -->"
TOC_MARKER_END = "<!-- TOC END -->"

def get_ipynb_files(root_dir='.'):
    files = []
    for f in os.listdir(root_dir):
        if f.endswith('.ipynb'):
            files.append(f)
    return sorted(files)

def parse_ipynb_headings(filepath):
    headings = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'markdown':
                    for line in cell.get('source', []):
                        # 주피터 노트북 소스는 리스트 형태일 수 있으므로 줄바꿈 처리
                        clean_line = line.strip()
                        match = re.match(r'^(#{1,6})\s+(.*)', clean_line)
                        if match:
                            headings.append({'level': len(match.group(1)), 'title': match.group(2).strip()})
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return headings

def generate_toc_string():
    files = get_ipynb_files()
    lines = [TOC_MARKER_START, TOC_HEADER]

    if not files:
        lines.append("\n_목차에 표시할 파일이 없습니다._")

    for filename in files:
        # 파일 이름에만 링크 연결
        file_link = urllib.parse.quote(filename)
        lines.append(f"\n### [{filename}]({file_link})")

        headings = parse_ipynb_headings(filename)

        for h in headings:
            # 들여쓰기 처리
            indent = "  " * (h['level'] - 1)
            # 소제목은 링크 없이 텍스트만 출력
            lines.append(f"{indent}- {h['title']}")

    lines.append("\n" + TOC_MARKER_END)
    return "\n".join(lines)

def update_readme():
    new_toc_content = generate_toc_string()
    
    if not os.path.exists(README_PATH):
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_toc_content)
        return

    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(f"{re.escape(TOC_MARKER_START)}.*?{re.escape(TOC_MARKER_END)}", re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(new_toc_content, content)
    else:
        new_content = new_toc_content + "\n\n" + content
        
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == "__main__":
    update_readme()
