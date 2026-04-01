# PLAN: 제미나이 플랫폼 전용 OPAL 규율 강화 (Hardening)

## 1. 분석 및 설계 방향

제미나이(Gemini 1.5 Pro)가 컨텍스트를 '유연하게' 해석하려는 경향을 차단하고, OPAL 하네스를 '절대적 명령'으로 인식하게 만드는 것이 목표임.

### ① 제미나이 전용 Hardened 부트스트랩
- **명칭**: `gemini-bootstrap-hardened.md`
- **핵심**: "Read" 지시만 하는 것이 아니라, "Read 후 준수 여부를 스스로 증명하라"는 요구 포함.
- **네거티브 가드**: "프로세스 생략 = 지능적 실패"임을 명문화.

### ② 플랫폼 특화 정체성(Identity) 주입
- `identity.md` 내에 제미나이 감지 시 발동되는 **"Process-Oriented Guard"**를 설계.
- 제미나이의 기본 페르소나를 억제하고 OPAL PM으로서의 자아를 고정함.

---

## 2. 상세 구현 계획

### Step 1: gemini-bootstrap-hardened.md 설계 및 생성
- **파일**: `opal/bootstrapper/gemini-bootstrap-hardened.md`
- **추가 섹션**:
  - `[HARDENING RULES]`: 5대 절대 금지 사항 명시 (QA 생략, 체크리스트 미갱신, 요약 보고 등)
  - `[PROCESS PROOF]`: 답변 시작 시 현재 단계와 하네스 준수 여부를 짧게 보고하도록 유도.

### Step 2: identity.md 보강
- **파일**: `~/.opal/identity.md` (워크스페이스 소스: `opal/core/identity-template.md`)
- **내용**: 제미나이 플랫폼 전용 `traits`와 `behavioral_guards` 섹션 추가.

### Step 3: GEMINI.md 교체
- 워크스페이스 루트의 `GEMINI.md`를 신규 Hardened 버전으로 교체하여 즉시 효력 발생 유도.

---

## 3. QA 체크리스트

- [ ] `gemini-bootstrap-hardened.md`의 문구가 제미나이에게 충분히 강압적인가?
- [ ] 네거티브 가드가 구체적인 실패 사례(068 태스크 등)를 타겟팅하고 있는가?
- [ ] 부트스트랩 절차(AGENT.md, identity.md 로드)가 여전히 최우선으로 실행되는가?
- [ ] **[Self-Check]** 본 태스크(069) 종료 보고 전 `PLAN.md` 체크리스트를 갱신했는가? (068 실수 재발 방지)

---

## 4. 워커 디스패치 계획

이 태스크는 에이전트의 '자아'와 '규율'을 다루는 매우 민감한 작업이므로 PM(알투)이 직접 수행함. 
필요 시 제미나이의 반응성을 테스트하기 위한 간단한 문답 검토 에이전트를 활용할 수 있음.
