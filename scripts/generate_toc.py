import os
import re
import json
import urllib.parse

README_PATH = "README.md"
TOC_HEADER = "## 목차 (Table of Contents)"
TOC_MARKER_START = ""
TOC_MARKER_END = ""


def get_files_with_numbering(root_dir="."):
    files = []
    pattern = re.compile(r"^(\d+).*\.(md|ipynb|py)$")
    for f in os.listdir(root_dir):
        match = pattern.match(f)
        if match:
            files.append((int(match.group(1)), f, match.group(2)))
    return sorted(files, key=lambda x: x[0])


def generate_anchor(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text


def parse_md_headings(filepath):
    headings = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^(#{1,6})\s+(.*)", line)
                if match:
                    headings.append(
                        {"level": len(match.group(1)), "title": match.group(2).strip()}
                    )
    except:
        pass
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
                            headings.append(
                                {
                                    "level": len(match.group(1)),
                                    "title": match.group(2).strip(),
                                }
                            )
    except:
        pass
    return headings


def parse_py_headings(filepath):
    headings = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                match = re.match(r"^\s*#\s+(#{1,6})\s+(.*)", line)
                if match:
                    headings.append(
                        {"level": len(match.group(1)), "title": match.group(2).strip()}
                    )
    except:
        pass
    return headings


def generate_toc_string():
    files = get_files_with_numbering()
    lines = [TOC_MARKER_START, TOC_HEADER]

    if not files:
        lines.append("\n_목차에 표시할 파일이 없습니다._")

    for num, filename, ext in files:
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
            indent = "  " * (h["level"] - 1)
            if ext == ".py":
                lines.append(f"{indent}- {h['title']}")
            else:
                anchor = generate_anchor(h["title"])
                lines.append(f"{indent}- [{h['title']}]({file_link}#{anchor})")

    lines.append("\n" + TOC_MARKER_END)
    return "\n".join(lines)


def update_readme():
    new_toc_content = generate_toc_string()

    if not os.path.exists(README_PATH):
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_toc_content)
        return

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 마커가 존재하는지 확인
    pattern = re.compile(
        f"{re.escape(TOC_MARKER_START)}.*?{re.escape(TOC_MARKER_END)}", re.DOTALL
    )

    if pattern.search(content):
        # 마커가 있으면 그 부분만 교체
        new_content = pattern.sub(new_toc_content, content)
    else:
        # 마커가 없으면 (즉, 깨끗한 상태이거나 정리된 상태면) 맨 위에 추가
        new_content = new_toc_content + "\n\n" + content

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


if __name__ == "__main__":
    update_readme()
