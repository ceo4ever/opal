# 배포·복구

승인 범위에 배포가 있으면 init --delivery release, 기본 build는 ready_for_merge에서 끝난다.
REVIEW에서 독립 판정과 코드 소유자/릴리스 승인 후 RELEASE로 이동한다.
실제 승인 환경의 배포 명령만 collect-evidence role=deployment로 실행한다.
배포 exit만으로 건강 상태를 보장하지 않는다. health check와 RELEASE 확인이 필요하다.

OBSERVE에서는 합의한 관찰 구간·지표로 실제 조회 명령을 실행한다.
운영 담당자가 결과를 확인해 OBSERVE 승인 후 DONE과 함께 닫는다.
이상은 block하고 새 change_id의 intent에 증거·영향·제안·미결 질문을 담는다.
사전 승인된 롤백 런북만 실행한다. plan에 복구 절차·판단·담당자를 기록한다.
자격증명과 실제 배포 도구는 프로젝트가 제공하며 미연결 상태를 성공으로 보고하지 않는다.
