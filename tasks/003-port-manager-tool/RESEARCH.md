# RESEARCH: 프로젝트별 포트 매니저 CLI 도구 (r2-port)

> 작성일: 2026-03-09 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `scripts/install-mac.sh` | 프레임워크 설치 스크립트 | 수정 (r2-port 설치 메뉴 추가) |
| `scripts/r2-port.sh` | 포트 매니저 CLI (신규) | 신규 |

### 현재 구현 패턴

- `scripts/install-mac.sh`는 메뉴 기반 설치 구조로 `show_menu()` → `main()` 루프 패턴을 사용
- 설치 함수는 `install_{platform}()` 네이밍 컨벤션
- 헬퍼 함수(`install_dir`, `install_r2_section`)는 재사용 가능한 단위로 분리
- 컬러 출력(`info`, `success`, `warn`, `error`)은 공통 로깅 함수로 정의

## 2. 기술 조사 결과

### macOS 환경

| 항목 | 결과 |
|------|------|
| python3 | `/usr/bin/python3` (3.9.6) — macOS 기본 포함, JSON 파싱에 활용 가능 |
| lsof | 포트 사용 여부 확인: `lsof -i :PORT -sTCP:LISTEN -t` |
| /etc/hosts | 탭 구분 형식 `127.0.0.1\tdomain`, 수정 시 `sudo` 필요 |

### /etc/hosts 관리

- **형식**: `127.0.0.1	my-api.local` (IP + 탭 + 도메인)
- **추가**: `echo "127.0.0.1	$domain" | sudo tee -a /etc/hosts`
- **존재 확인**: `grep -qF "$domain" /etc/hosts`
- **삭제**: `sudo sed -i '' "/ $domain$/d" /etc/hosts`
- **DNS 캐시 반영**: `sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder`
- **제약**: 포트 매핑은 불가 — IP 매핑만 지원. URL에 포트를 포함해야 함 (`http://my-api.local:8201`)

### 포트 사용 여부 확인

```bash
# 포트가 사용 중이면 PID 반환, 아니면 빈 문자열
lsof -i :$port -sTCP:LISTEN -t 2>/dev/null
```

### JSON 파싱 (python3)

외부 의존성(jq) 없이 macOS 기본 python3으로 JSON 읽기/쓰기 가능:

```bash
# 읽기: 특정 키의 port 조회
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2],{}).get('port',''))" "$REGISTRY" "$domain"

# 쓰기: 새 엔트리 추가
python3 -c "
import json,sys
f=sys.argv[1]; d=json.load(open(f)) if __import__('os').path.exists(f) else {}
d[sys.argv[2]]={'port':int(sys.argv[3]),'type':sys.argv[4],'project':sys.argv[5],'created':sys.argv[6]}
json.dump(d,open(f,'w'),indent=2,ensure_ascii=False)
" "$REGISTRY" "$domain" "$port" "$type" "$project" "$date"
```

## 3. 영향 범위

| 영향 대상 | 내용 |
|----------|------|
| `install-mac.sh` | 메뉴 항목 추가 ([6] r2-port), `show_menu()` 범위 변경, `install_r2port()` 함수 추가 |
| `~/ports.json` | 중앙 포트 레지스트리 (신규) |
| `~/.r2/bin/` | r2-port CLI 설치 경로 (신규) |
| `/etc/hosts` | 도메인 엔트리 추가/삭제 (sudo 필요) |
| 사용자 셸 프로파일 | `~/.r2/bin`을 PATH에 추가해야 함 |

## 4. 핵심 발견 사항

1. **python3이 macOS 기본 포함** — jq 없이 JSON 처리 가능, 외부 의존성 0
2. **lsof로 포트 확인이 신뢰적** — `lsof -i :PORT -sTCP:LISTEN -t` 패턴이 간결하고 정확
3. **/etc/hosts는 포트 매핑 불가** — URL에 포트 포함 필수 (`http://domain:port`). 하지만 도메인으로 의미 부여 + `.env` 주입으로 코드에서는 포트를 직접 알 필요 없음
4. **DNS 캐시 플러시 필요** — /etc/hosts 변경 후 `dscacheutil -flushcache` 실행해야 즉시 반영
5. **install-mac.sh 루프 구조 활용 가능** — 기존 while 루프 메뉴에 [6] 항목 추가

## 5. 제약/리스크

| 리스크 | 대응 |
|--------|------|
| sudo 거부 시 /etc/hosts 등록 실패 | warn 출력 후 계속 진행 (포트 할당은 정상 동작, hosts만 수동 안내) |
| 포트 범위 고갈 (900개) | 현실적으로 발생 가능성 극히 낮음. 발생 시 에러 메시지 출력 |
| python3 미설치 macOS (극히 드묾) | 스크립트 시작 시 python3 존재 확인, 없으면 안내 후 종료 |
| PATH 설정 누락 | 설치 시 셸 프로파일에 자동 추가 또는 안내 메시지 출력 |
