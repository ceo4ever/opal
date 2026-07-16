# Skill Commands (스킬 커맨드)

> 출처: opal/core/AGENT.md §스킬 레지스트리 + §쌍슬래시 커맨드
> 로드 시점: 사용자가 `//`로 시작하는 입력을 보낼 때
> 역할: skill-registry 호출 절차 / 스킬명 추출·매칭 / 폴백(skills.md) / 커맨드 형식

---

## 스킬 레지스트리

- `node ~/.opal/tools/skill-registry/skill-registry.js` 실행 가능 여부를 확인한다
- 사용자가 `//` 커맨드 또는 스킬 관련 요청 시: `match "{입력}"` 으로 매칭
- 스킬 정보 필요 시: `get {스킬명}` 으로 조회
- 상세 사용법 및 기술 스택별 추천: `~/.opal/references/skills.md` 참조
- Node.js 미설치 시 폴백: `~/.opal/references/skills.md`를 Read

## 쌍슬래시 커맨드 (`//`)

소유자가 `//`로 시작하는 입력을 보내면 OPAL 스킬 호출로 인식한다.

- `//` 뒤의 문자열에서 스킬명(정식 또는 약식)을 추출한다
- `~/.opal/references/skills.md` 레지스트리에서 해당 스킬을 찾는다
- 스킬의 SKILL.md를 Read하고 프로세스를 따른다
- 단, `match` 응답이 `installed: false`(미설치 community 스킬)이면 — SKILL.md Read 전에 **`opal-skill-manager/SKILL.md §6`(미설치 매칭 시 자동 설치·실행) 절차를 먼저 따른다**. 라이선스 확인된 스킬은 동의 대기 없이 자동 설치·실행하고, 미확인(Unknown) 라이선스만 확인 게이트를 거친다.
- `//` 뒤에 이어지는 텍스트는 작업 설명(arguments)으로 전달한다

```
형식: //{스킬명 또는 약식} [--interactive|--semi-agentic|--agentic] {작업 설명}
예시: //opds 로그인 버그 수정해줘                  (기본 — semi-agentic)
      //opd --interactive 회원가입 기능 전체 개발해줘
      //opp --agentic 자율 진행
      //api-analyzer https://api.example.com
```

매칭됐으나 미설치(`installed: false`)인 community 스킬: `opal-skill-manager/SKILL.md §6` 자동 설치·실행 절차로 라우팅한다 (위 참조).

매칭 실패 시: "해당 스킬을 찾을 수 없습니다. `//` 없이 자연어로 요청해주세요." 안내.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — AGENT.md §스킬레지스트리·§쌍슬래시커맨드 분리 (128) |
| v1.1 | 2026-05-09 11:22 | 쌍슬래시 커맨드 예시에 모드 플래그 3-way 추가 (140) |
| v1.2 | 2026-07-16 14:59 KST | 미설치(`installed:false`) community 스킬 매칭 시 skill-manager §6 자동 설치·실행 라우팅 추가 — `//` 흐름 라우팅 공백 봉합 (064) |
