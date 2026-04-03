#!/usr/bin/env python3
"""
playwright-tool — OPAL 웹 페이지 수집 CLI 도구

Usage:
  main.py <url> [--mode {full,clean}] [--output <path>] [--timeout <seconds>]

출력 (stdout, JSON):
  성공: {"ok": true, "url": "...", "mode": "...", "path": "...", "content": "..."}
  실패: {"ok": false, "url": "...", "error": "..."}
"""

import argparse
import json
import re
import sys
from pathlib import Path


def err_out(url, message):
    print(json.dumps({"ok": False, "url": url, "error": message}, ensure_ascii=False))
    sys.exit(1)


def remove_tags(soup, tags):
    """지정된 태그들을 soup에서 제거한다."""
    for tag in tags:
        for el in soup.find_all(tag):
            el.decompose()


def html_to_markdown(soup):
    """BeautifulSoup 객체를 간단한 Markdown으로 변환한다."""
    # markdownify 우선 사용
    try:
        import markdownify
        return markdownify.markdownify(str(soup), heading_style="ATX", strip=["script", "style"])
    except ImportError:
        pass

    # 직접 변환 구현
    text = _convert_node(soup)
    # 빈 줄 정리 (3개 이상 → 2개)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _convert_node(node):
    """재귀적으로 노드를 Markdown으로 변환한다."""
    from bs4 import NavigableString, Tag

    if isinstance(node, NavigableString):
        return str(node)

    if not isinstance(node, Tag):
        return ""

    tag = node.name.lower() if node.name else ""

    # 헤딩
    heading_map = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
    if tag in heading_map:
        inner = _children_text(node).strip()
        if inner:
            return f"\n\n{heading_map[tag]} {inner}\n\n"
        return ""

    # 단락
    if tag == "p":
        inner = _children_text(node).strip()
        if inner:
            return f"\n\n{inner}\n\n"
        return ""

    # 링크
    if tag == "a":
        href = node.get("href", "")
        inner = _children_text(node).strip()
        if inner and href:
            return f"[{inner}]({href})"
        return inner

    # 이미지
    if tag == "img":
        src = node.get("src", "")
        alt = node.get("alt", "")
        if src:
            return f"![{alt}]({src})"
        return ""

    # 리스트
    if tag == "ul":
        items = []
        for li in node.find_all("li", recursive=False):
            item_text = _children_text(li).strip()
            if item_text:
                items.append(f"- {item_text}")
        return "\n\n" + "\n".join(items) + "\n\n" if items else ""

    if tag == "ol":
        items = []
        for i, li in enumerate(node.find_all("li", recursive=False), 1):
            item_text = _children_text(li).strip()
            if item_text:
                items.append(f"{i}. {item_text}")
        return "\n\n" + "\n".join(items) + "\n\n" if items else ""

    # 코드
    if tag == "code":
        inner = _children_text(node)
        if "\n" in inner:
            return f"\n\n```\n{inner}\n```\n\n"
        return f"`{inner}`"

    if tag == "pre":
        inner = _children_text(node)
        return f"\n\n```\n{inner}\n```\n\n"

    # 강조
    if tag in ("strong", "b"):
        inner = _children_text(node).strip()
        return f"**{inner}**" if inner else ""

    if tag in ("em", "i"):
        inner = _children_text(node).strip()
        return f"*{inner}*" if inner else ""

    # 줄바꿈
    if tag == "br":
        return "\n"

    # 블록 요소
    if tag in ("div", "section", "article", "main", "blockquote"):
        inner = _children_text(node)
        return f"\n{inner}\n"

    # 테이블 (기본 처리)
    if tag == "table":
        return _convert_table(node)

    # 제목/레이아웃 컨테이너
    if tag in ("body", "html", "span", "li"):
        return _children_text(node)

    # 나머지 태그: 자식 내용만 반환
    return _children_text(node)


def _children_text(node):
    parts = []
    for child in node.children:
        parts.append(_convert_node(child))
    return "".join(parts)


def _convert_table(table_node):
    """테이블을 Markdown 테이블로 변환한다."""
    rows = table_node.find_all("tr")
    if not rows:
        return ""

    md_rows = []
    for i, row in enumerate(rows):
        cells = row.find_all(["td", "th"])
        cell_texts = [_children_text(c).strip().replace("\n", " ") for c in cells]
        md_rows.append("| " + " | ".join(cell_texts) + " |")
        if i == 0:
            md_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")

    return "\n\n" + "\n".join(md_rows) + "\n\n"


def extract_content(html, mode):
    """HTML에서 모드에 따라 콘텐츠를 추출하고 Markdown으로 변환한다."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        # BeautifulSoup 없을 때 정규식 폴백
        return _regex_extract(html, mode)

    soup = BeautifulSoup(html, "html.parser")

    # 공통 제거: script, style, noscript, iframe
    remove_tags(soup, ["script", "style", "noscript", "iframe"])

    # clean 모드 추가 제거: nav, header, footer, aside
    if mode == "clean":
        remove_tags(soup, ["nav", "header", "footer", "aside"])
        # role 속성 기반 제거
        for role in ("navigation", "banner", "contentinfo"):
            for el in soup.find_all(attrs={"role": role}):
                el.decompose()

    # body 또는 전체 변환
    body = soup.find("body") or soup
    title = soup.find("title")
    title_text = title.get_text().strip() if title else ""

    content = html_to_markdown(body)

    # 빈 줄 정리
    content = re.sub(r'\n{3,}', '\n\n', content).strip()

    return title_text, content


def _regex_extract(html, mode):
    """BeautifulSoup 없을 때 정규식으로 기본 처리한다."""
    # title 추출
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title_text = title_match.group(1).strip() if title_match else ""

    # 제거할 태그들
    tags_to_remove = ["script", "style", "noscript", "iframe"]
    if mode == "clean":
        tags_to_remove += ["nav", "header", "footer", "aside"]

    text = html
    for tag in tags_to_remove:
        text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # 모든 HTML 태그 제거
    text = re.sub(r'<[^>]+>', ' ', text)
    # 공백 정리
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return title_text, text.strip()


def main():
    parser = argparse.ArgumentParser(
        prog="playwright-tool",
        description="웹 페이지를 Playwright로 수집하여 Markdown으로 변환한다."
    )
    parser.add_argument("url", help="수집할 URL")
    parser.add_argument("--mode", choices=["full", "clean"], default="full",
                        help="추출 모드: full(기본) 또는 clean(본문만)")
    parser.add_argument("--output", metavar="PATH",
                        help="지정 시 파일로 저장 (미지정 시 stdout JSON)")
    parser.add_argument("--timeout", type=int, default=30,
                        help="페이지 로딩 타임아웃 (초, 기본: 30)")

    args = parser.parse_args()
    url = args.url

    # playwright import 확인
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        err_out(url, "playwright module not found. Run: ~/.opal/.venv/bin/pip install playwright")

    # 페이지 수집
    html = None
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "playwright install" in msg.lower():
                    err_out(url, "browser not installed. Run: ~/.opal/.venv/bin/playwright install chromium")
                err_out(url, f"browser launch failed: {msg}")

            try:
                page = browser.new_page()
                page.goto(url, timeout=args.timeout * 1000, wait_until="networkidle")
                html = page.content()
            except PlaywrightTimeoutError:
                err_out(url, f"timeout: page load exceeded {args.timeout}s")
            except Exception as e:
                msg = str(e)
                if "net::ERR_NAME_NOT_RESOLVED" in msg or "ERR_NAME_NOT_RESOLVED" in msg:
                    err_out(url, f"DNS resolution failed: {url}")
                err_out(url, str(e))
            finally:
                browser.close()

    except SystemExit:
        raise
    except Exception as e:
        err_out(url, str(e))

    # 콘텐츠 추출
    try:
        title_text, content = extract_content(html, args.mode)
    except Exception as e:
        err_out(url, f"content extraction failed: {e}")

    # 산출물 형식: 헤더 메타 + 콘텐츠
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"# {title_text}\n\n> 소스: {url}\n> 캡처일: {now}\n> 추출 방식: playwright-tool CLI\n> 추출 모드: {args.mode}\n\n---\n\n"
    full_content = header + content

    # 파일 저장 (--output 지정 시)
    output_path = None
    if args.output:
        try:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(full_content, encoding="utf-8")
            output_path = str(out_path.resolve())
        except Exception as e:
            err_out(url, f"file write failed: {e}")

    result = {
        "ok": True,
        "url": url,
        "mode": args.mode,
        "path": output_path,
        "content": full_content,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
