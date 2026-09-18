# system-architecture-html (html-sa)

시스템·인프라 레이어 구조를 자기완결형 단일 HTML 다이어그램으로 만드는 스킬.

## 개요

레이어드 시스템 아키텍처, 기술 스택, 인프라 구성을 "엔지니어의 화이트보드를 코드로 옮긴 듯한" 다크 IDE 톤의 단일 HTML 파일로 생성합니다. 헤더, 범례, 레이어별 노드 카드, 빌드 우선순위 배지, 선택적 로드맵 섹션까지 포함된 출력물은 외부 의존성이 Google Fonts 정도뿐이라 그대로 공유하거나 인쇄할 수 있습니다.

## 언제 쓰나

- "시스템 아키텍처를 HTML로 만들어줘", "아키텍처 다이어그램 HTML" 요청을 받았을 때
- 이미 채팅에서 SVG로 아키텍처를 그렸는데, 공유 가능한 단일 파일로 만들고 싶을 때

다음 경우에는 이 스킬을 쓰지 않습니다: 인라인 SVG 다이어그램(비주얼라이저 사용), 레이어 없는 시퀀스/플로우 다이어그램(mermaid 사용), ER 다이어그램(`erd-modeler` 또는 mermaid `erDiagram` 사용), 화면 목업(`html-mockup` 사용).

## 사용법

호출: `//html-sa` 또는 `//system-architecture-html`

| 항목 | 내용 |
|------|------|
| 필수 입력 | 시스템명, 레이어 구성 |
| 보장 출력 | `outputs/<system_name>_architecture.html` 단일 파일 |

정보가 부족하면 다음을 인터뷰로 확인합니다.

- 시스템명과 한 줄 목적
- 대상 사용자/고객
- 레이어 수 (보통 4~7개, 불명확하면 6개 기본)
- 레이어별로 들어갈 노드명·설명·기술 스택
- 노드별 빌드 우선순위 (MVP/LATER 등)
- 컬러 테마(기본 코랄, 브랜드 컬러가 있으면 확인)

정보가 최소한만 주어지면 아래 6레이어 기본 골격을 제안하고 확인을 받습니다: ① Channel/Entry ② Orchestration/Routing ③ Core Logic/Agents ④ Data/Brain ⑤ External Services ⑥ Operator/Monitoring.

## 동작 흐름

1. **환경 감지**: `.opal/AGENT.md`, `tasks/{NNN}-*/TASK.md`, `STATE.md`/`MEMORY.json` 존재 여부로 OPAL 프로젝트·태스크 폴더 여부를 판별합니다.
2. **컨텍스트 흡수**: `TASK.md`, `ANALYSIS.md`, `PLAN.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md` 등에서 시스템명·레이어 후보·노드 후보·MVP 분류 힌트를 추출합니다. 추가로 `.opal/code-scan.json`(있으면), `package.json` 등 의존성 매니페스트, 디렉토리 트리를 보강 자료로 사용합니다. 추론 가능한 항목은 "{항목}은 컨텍스트에서 {추론값}으로 자동 결정. 변경하시려면 알려주세요." 1줄 통지로 대체합니다.
3. **인터뷰**: 채팅에 이미 충분한 정보가 있으면 생략하고, 아니면 위 항목을 확인합니다.
4. **HTML 초안 작성**: `references/template.html`을 복사해 메타 패널, 제목, 레이어별 `.layer-num`/`.layer-name`/`.layer-tag`와 노드 카드를 채웁니다. 이때 `references/design-system.md`(레이어 컬러 팔레트, 타이포그래피, 컴포넌트 패턴)와 `references/copywriting.md`(노드 설명·기술 칩 작성법)를 반드시 참조합니다.
5. **저장**: 환경에 따라 저장 경로를 결정합니다.

| 환경 | 저장 경로 |
|------|---------|
| OPAL 태스크 폴더 | `tasks/{NNN}-*/outputs/<system_name>_architecture.html` |
| OPAL 프로젝트(태스크 외) | `<cwd>/outputs/<system_name>_architecture.html` 또는 `docs/architecture/<system_name>.html` |
| 비-OPAL/사용자 지정 | 인터뷰로 확인하거나 `<cwd>/<system_name>_architecture.html` |

파일명은 snake_case 규칙을 유지합니다.

## 산출물

단일 `.html` 파일이며 다음 구성을 포함합니다.

| 구성 요소 | 내용 |
|----------|------|
| 헤더 | 제목, eyebrow 태그, 프로젝트 메타 패널(target/BM/stack/timeline) |
| 범례 | 레이어 컬러 코드, 상태 배지(MVP/LATER/DONE 등) |
| 아키텍처 그리드 | 레이어별 좌측 레일(번호·이름·설명)과 우측 노드 카드(제목·상태 배지·설명·기술 칩) |
| 로드맵 섹션(기본 포함) | Now/Next/Later 3트랙 빌드 계획 |
| 푸터 | 버전, 작성자, 한줄 요약 |

브라우저에서 바로 열리고, 인쇄 시 흰 배경/검은 텍스트로 전환되며, 900px 미만에서는 그리드가 1열로 접히는 반응형입니다.

## FAQ

### ER 다이어그램도 이 스킬로 만들 수 있나요?
아니요. ER 다이어그램은 `erd-modeler` 스킬이나 mermaid `erDiagram`을 사용합니다.

### 화면 목업도 이 스킬로 만드나요?
아니요. 화면 목업은 `html-mockup` 스킬을 사용합니다.
