---
template: sdlc-v2
---
# 추가 작업: 최초 실행 온보딩

## 목표

저장된 WorkStudio 상태가 없는 최초 실행에서 샘플 Workspace를 바로 노출하지 않고, `OPAL WorkStudio에 오신 것을 환영합니다`를 중심으로 한 진입 화면을 제공한다.

## 계약

- AW-FR-1: 최초 실행 화면에 `기존 프로젝트 열기`, `새 프로젝트 만들기`, `데모 둘러보기`를 서로 구분된 행위로 보여준다.
- AW-FR-2: 저장된 최근 Project가 없으면 `최근 프로젝트가 없습니다`를 보여준다.
- AW-FR-3: 기존/새 Project 행위는 Electron typed preload의 directory selection을 사용하고, 등록 성공 시 Workspace로 진입한다. 취소/실패 시 온보딩을 유지한다.
- AW-FR-4: `데모 둘러보기`는 기존 seed Workspace로 진입하고 상태를 저장해 다음 실행에서 온보딩을 반복하지 않는다.
- AW-FR-5: 기존 38개 WorkStudio 테스트와 Dashboard 123개 테스트를 회귀시키지 않는다.

## 구현 경계

- 이 단계의 최근 Project 목록은 빈 상태 표현까지만 구현한다. 실제 최근 목록과 Registry 영속화는 다음 Project Registry 태스크가 소유한다.
- 샘플 seed는 삭제하지 않고 명시적 `데모 둘러보기`로만 진입한다.
- 실제 PTY·PM Runtime 연동은 기존 범위 밖 계약을 유지한다.

## 검증

- 구현 전 RED: 저장 상태가 없을 때 Welcome 문구·3개 진입 행위·최근 Project empty state가 노출되는지 검증한다.
- GREEN: 데모 진입 후 Welcome이 닫히고 Workspace가 사용 가능한지, Project 선택 취소 시 Welcome이 유지되는지 검증한다.
- 회귀: WorkStudio lint/typecheck/test/build/Electron syntax와 Dashboard lint/typecheck/test/build를 재실행한다.
