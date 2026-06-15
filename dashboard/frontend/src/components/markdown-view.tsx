/**
 * @header {
 *   "module": "markdown-view",
 *   "layer": "component",
 *   "domain": "shared",
 *   "description": "공통 마크다운 렌더러 — react-markdown + remark-gfm + rehype-slug + prose(typography) 클래스. 문서 시작의 @header frontmatter를 추출해 접힘 아코디언으로 표시하고 본문에서 제거. 헤딩 2개 이상이면 TOC(목차) 박스를 본문 앞에 렌더, 클릭 시 scrollIntoView로 스크롤. 색은 토큰 경유(C-12).",
 *   "exports": ["MarkdownView"],
 *   "depends": ["react-markdown", "remark-gfm", "rehype-slug", "github-slugger", "accordion"]
 * }
 */

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import GithubSlugger from "github-slugger";
import { cn } from "@/lib/utils";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface MarkdownViewProps {
  content: string;
  className?: string;
}

interface HeaderMeta {
  module?: string;
  layer?: string;
  domain?: string;
  description?: string;
  exports?: string[];
  depends?: string[];
  note?: string;
  [key: string]: unknown;
}

interface TocItem {
  level: number;
  text: string;
  slug: string;
}

/**
 * 문서 상단 frontmatter에서 @header JSON을 추출한다.
 * 반환: { meta: HeaderMeta | null, body: string }
 */
function extractHeader(content: string): {
  meta: HeaderMeta | null;
  body: string;
} {
  // frontmatter 블록 추출 (문서 시작의 --- ... ---)
  const fmMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n?/);
  if (!fmMatch) {
    return { meta: null, body: content };
  }

  const frontmatter = fmMatch[1];
  const body = content.slice(fmMatch[0].length);

  // @header JSON 추출 — balanced brace 방식
  const headerKeyIdx = frontmatter.indexOf("@header");
  if (headerKeyIdx === -1) {
    return { meta: null, body: content };
  }

  const braceStart = frontmatter.indexOf("{", headerKeyIdx);
  if (braceStart === -1) {
    return { meta: null, body };
  }

  // balanced brace 탐색
  let depth = 0;
  let braceEnd = -1;
  for (let i = braceStart; i < frontmatter.length; i++) {
    if (frontmatter[i] === "{") depth++;
    else if (frontmatter[i] === "}") {
      depth--;
      if (depth === 0) {
        braceEnd = i;
        break;
      }
    }
  }

  if (braceEnd === -1) {
    return { meta: null, body };
  }

  const jsonStr = frontmatter.slice(braceStart, braceEnd + 1);

  try {
    const meta = JSON.parse(jsonStr) as HeaderMeta;
    return { meta, body };
  } catch {
    return { meta: null, body };
  }
}

/**
 * 본문에서 h1~h3 헤딩을 추출하고 github-slugger로 slug를 생성한다.
 * rehype-slug와 동일한 slug 규칙을 사용해 id와 일치시킨다.
 */
function extractToc(body: string): TocItem[] {
  const slugger = new GithubSlugger();
  const headingRegex = /^(#{1,3})\s+(.+)$/gm;
  const items: TocItem[] = [];
  let match: RegExpExecArray | null;

  while ((match = headingRegex.exec(body)) !== null) {
    const level = match[1].length;
    // 인라인 마크다운 제거 (강조, 코드, 링크 등)
    const text = match[2]
      .replace(/\*\*(.+?)\*\*/g, "$1")
      .replace(/\*(.+?)\*/g, "$1")
      .replace(/_(.+?)_/g, "$1")
      .replace(/`(.+?)`/g, "$1")
      .replace(/\[(.+?)\]\(.+?\)/g, "$1")
      .trim();
    const slug = slugger.slug(text);
    items.push({ level, text, slug });
  }

  return items;
}

function HeaderMetaAccordion({ meta }: { meta: HeaderMeta }) {
  return (
    <Accordion type="single" collapsible className="mb-4">
      <AccordionItem
        value="header-meta"
        className="border border-border rounded-md overflow-hidden"
      >
        <AccordionTrigger className="px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:no-underline bg-muted/50 hover:bg-muted transition-colors">
          <span className="flex items-center gap-1.5">
            <span>📋</span>
            <span>문서 메타 (@header)</span>
            {meta.module && (
              <span className="ml-1 font-mono text-[10px] bg-background border border-border rounded px-1.5 py-0.5 text-foreground/70">
                {meta.module}
              </span>
            )}
          </span>
        </AccordionTrigger>
        <AccordionContent className="px-3 pt-2 pb-3">
          <div className="space-y-2 text-xs">
            {/* module / layer / domain — badge row */}
            {(meta.module || meta.layer || meta.domain) && (
              <div className="flex flex-wrap gap-1.5">
                {meta.module && (
                  <span className="inline-flex items-center gap-1">
                    <span className="font-mono text-muted-foreground">module</span>
                    <span className="bg-primary/10 text-primary border border-primary/20 rounded px-1.5 py-0.5 font-mono text-[10px]">
                      {meta.module}
                    </span>
                  </span>
                )}
                {meta.layer && (
                  <span className="inline-flex items-center gap-1">
                    <span className="font-mono text-muted-foreground">layer</span>
                    <span className="bg-secondary text-secondary-foreground border border-border rounded px-1.5 py-0.5 font-mono text-[10px]">
                      {meta.layer}
                    </span>
                  </span>
                )}
                {meta.domain && (
                  <span className="inline-flex items-center gap-1">
                    <span className="font-mono text-muted-foreground">domain</span>
                    <span className="bg-accent text-accent-foreground border border-border rounded px-1.5 py-0.5 font-mono text-[10px]">
                      {meta.domain}
                    </span>
                  </span>
                )}
              </div>
            )}

            {/* description */}
            {meta.description && (
              <div>
                <span className="font-mono text-muted-foreground mr-1.5">description</span>
                <span className="text-foreground/80">{meta.description}</span>
              </div>
            )}

            {/* exports */}
            {meta.exports && meta.exports.length > 0 && (
              <div>
                <div className="font-mono text-muted-foreground mb-1">exports</div>
                <div className="flex flex-wrap gap-1">
                  {meta.exports.map((exp, i) => (
                    <span
                      key={i}
                      className="bg-muted border border-border rounded px-1.5 py-0.5 font-mono text-[10px] text-foreground/70"
                    >
                      {exp}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* depends */}
            {meta.depends && meta.depends.length > 0 && (
              <div>
                <div className="font-mono text-muted-foreground mb-1">depends</div>
                <div className="flex flex-wrap gap-1">
                  {meta.depends.map((dep, i) => (
                    <span
                      key={i}
                      className="bg-muted border border-border rounded px-1.5 py-0.5 font-mono text-[10px] text-foreground/70"
                    >
                      {dep}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* note */}
            {meta.note && (
              <div>
                <span className="font-mono text-muted-foreground mr-1.5">note</span>
                <span className="text-foreground/70 italic">{meta.note}</span>
              </div>
            )}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

/**
 * TOC(목차) 박스 — 헤딩 2개 이상일 때만 렌더.
 * TOC 항목 클릭 시 scrollIntoView로 컨테이너 내부 스크롤.
 */
function TableOfContents({ items }: { items: TocItem[] }) {
  if (items.length < 2) return null;

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>, slug: string) => {
    e.preventDefault();
    const target = document.getElementById(slug);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <Accordion type="single" collapsible defaultValue="toc" className="mb-4">
      <AccordionItem
        value="toc"
        className="border border-border rounded-md overflow-hidden"
      >
        <AccordionTrigger className="px-3 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:no-underline bg-muted/30 hover:bg-muted/50 transition-colors">
          <span className="flex items-center gap-1.5">
            <span>📑</span>
            <span>목차</span>
            <span className="ml-1 font-mono text-[10px] bg-background border border-border rounded px-1.5 py-0.5 text-foreground/60">
              {items.length}
            </span>
          </span>
        </AccordionTrigger>
        <AccordionContent className="px-3 pt-2 pb-3">
          <nav>
            <ul className="space-y-0.5">
              {items.map((item, i) => (
                <li
                  key={i}
                  style={{
                    paddingLeft: item.level === 1 ? 0 : item.level === 2 ? "0.75rem" : "1.5rem",
                  }}
                >
                  <a
                    href={`#${item.slug}`}
                    onClick={(e) => handleClick(e, item.slug)}
                    className={cn(
                      "text-xs text-muted-foreground hover:text-foreground transition-colors",
                      "flex items-center gap-1 py-0.5 leading-relaxed",
                      item.level === 1 && "font-medium text-foreground/80",
                      item.level === 2 && "before:content-['–'] before:text-border before:mr-1",
                      item.level === 3 && "before:content-['·'] before:text-border before:mr-1 text-foreground/60",
                    )}
                  >
                    {item.text}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

export function MarkdownView({ content, className }: MarkdownViewProps) {
  const { meta, body } = extractHeader(content);
  const tocItems = extractToc(body);

  return (
    <div className={cn("flex flex-col", className)}>
      {meta && <HeaderMetaAccordion meta={meta} />}
      <TableOfContents items={tocItems} />
      <div
        className={cn(
          "prose prose-sm dark:prose-invert max-w-none",
          // 표 스타일 — GFM table
          "prose-table:w-full prose-table:border-collapse",
          "prose-th:border prose-th:border-border prose-th:bg-muted prose-th:px-3 prose-th:py-1.5 prose-th:text-left prose-th:text-xs prose-th:font-semibold",
          "prose-td:border prose-td:border-border prose-td:px-3 prose-td:py-1.5 prose-td:text-xs prose-td:align-top",
          // 코드 블록 — mono + muted background + 텍스트 색 명시(라이트/다크 대비 확보)
          "prose-code:font-mono prose-code:text-xs prose-code:bg-muted prose-code:text-foreground prose-code:px-1 prose-code:py-0.5 prose-code:rounded",
          "prose-pre:bg-muted prose-pre:text-foreground prose-pre:border prose-pre:border-border prose-pre:rounded-md prose-pre:overflow-x-auto",
          // pre 내부 code는 배경 제거(이중 배경 방지)·색 상속
          "[&_pre_code]:bg-transparent [&_pre_code]:text-foreground [&_pre_code]:p-0",
          // 헤딩 크기 조정 (prose-sm 기준)
          "prose-headings:font-semibold prose-headings:text-foreground",
          // 링크 색 — 토큰 경유
          "prose-a:text-primary prose-a:no-underline hover:prose-a:underline",
          // 인용 스타일
          "prose-blockquote:border-l-border prose-blockquote:text-muted-foreground",
        )}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeSlug]}
        >
          {body}
        </ReactMarkdown>
      </div>
    </div>
  );
}
