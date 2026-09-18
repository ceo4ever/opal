---
name: opal-pilot-project-build
description: 프로젝트 빌드 오케스트레이터 fixture
---

# opal-pilot-project-build (fixture)

## Usage

```bash
opal-pilot-project-build --intent INTENT.md
```

## When to use

프로젝트 빌드가 필요한 fixture 시나리오.

## Arguments

- `--intent` (string, required): INTENT.md 경로

## Options

- `--dry-run` (boolean, optional, default: false): 실행 없이 계획만 출력

## Examples

```bash
opal-pilot-project-build --intent tasks/x/INTENT.md
```
