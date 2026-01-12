import os
import re
import json
import urllib.parse

# 설정
README_PATH = "README.md"
TARGET_EXTENSIONS = (".md", ".ipynb", ".py")
TOC_HEADER = "## 목차 (Table of Contents)"
TOC_MARKER_START = ""
TOC_MARKER_END = ""


def get_files_with_numbering(root_dir="."):
    files = []
    # 정규식: 숫자로 시작하는 파일명 (예: 01_intro.md, 01file.py)
    pattern = re.compile(r"^(\d+).*\.(md|ipynb|py)$")

    for f in os.listdir(root_dir):
        match = pattern.match(f)
        if match:
            # (숫자값, 파일명, 확장자) 튜플 저장
            files.append((int(match.group(1)), f, match.group(2)))

    # 숫자 순서대로 정렬
    return sorted(files, key=lambda x: x[0])


def generate_anchor(text):
    # GitHub 스타일 앵커 생성 (소문자, 특수문자 제거, 공백은 -로)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def parse_md_headings(filepath):
    headings = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # # 으로 시작하는 라인 감지
            match = re.match(r"^(#{1,6})\s+(.*)", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append({"level": level, "title": title})
    return headings


def parse_ipynb_headings(filepath):
    headings = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            notebook = json.load(f)
            for cell in notebook.get("cells", []):
                if cell.get("cell_type") == "markdown":
                    for line in cell.get("source", []):
                        match = re.match(r"^(#{1,6})\s+(.*)", line)
                        if match:
                            level = len(match.group(1))
                            title = match.group(2).strip()
                            headings.append({"level": level, "title": title})
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return headings


def parse_py_headings(filepath):
    headings = []
    # .py 파일은 '# ## 제목' 또는 '# 제목' 등의 관례를 따름
    # 여기서는 '# ## ' 처럼 주석 안에 마크다운 헤더가 있는 경우를 가정
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*#\s+(#{1,6})\s+(.*)", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append({"level": level, "title": title})
    return headings


def generate_toc_content():
    files = get_files_with_numbering()
    lines = [TOC_MARKER_START, TOC_HEADER]

    for num, filename, ext in files:
        # 파일 링크 생성 (URL 인코딩 필요)
        file_link = urllib.parse.quote(filename)
        lines.append(f"\n### [{filename}]({file_link})")

        headings = []
        if ext == ".md":
            headings = parse_md_headings(filename)
        elif ext == ".ipynb":
            headings = parse_ipynb_headings(filename)
        elif ext == ".py":
            headings = parse_py_headings(filename)

        for h in headings:
            indent = "  " * (h["level"] - 1)  # 들여쓰기 조정
            # .py는 내부 앵커 동작 불가하므로 파일 링크로 대체하거나 링크 제거
            if ext == ".py":
                lines.append(f"{indent}- {h['title']}")
            else:
                anchor = generate_anchor(h["title"])
                lines.append(f"{indent}- [{h['title']}]({file_link}#{anchor})")

    lines.append("\n" + TOC_MARKER_END)
    return "\n".join(lines)


def update_readme():
    toc_content = generate_toc_content()

    if not os.path.exists(README_PATH):
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(toc_content)
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 기존 TOC 마커가 있으면 교체, 없으면 상단에 추가
    pattern = re.compile(
        f"{re.escape(TOC_MARKER_START)}.*{re.escape(TOC_MARKER_END)}", re.DOTALL
    )

    if pattern.search(content):
        new_content = pattern.sub(toc_content, content)
    else:
        new_content = toc_content + "\n\n" + content

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    update_readme()
