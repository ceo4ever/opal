# CLI 계약

| 명령 | 설명 | 종료 코드 |
|---|---|---|
| `stockctl [--store PATH] add SKU --qty N [--name NAME] [--location LOC]` | 수량 추가 | 0 |
| `stockctl remove SKU --qty N` | 수량 차감 | 0 성공, 1 미등록 SKU, 2 수량 부족 |
| `stockctl list` | `SKU\tNAME\tLOCATION\tQTY` 줄 출력 | 0 |

저장소 경로: `--store` > 환경변수 `STOCKCTL_STORE` > `stock.json`.
