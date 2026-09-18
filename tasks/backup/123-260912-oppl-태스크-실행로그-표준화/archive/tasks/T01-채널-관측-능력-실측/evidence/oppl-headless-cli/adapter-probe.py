#!/usr/bin/env python3
"""oppl-headless-cli 축 관측 프로브 (Phase 0 실측용, 읽기·계측 전용).

opal-agent 헤드리스 CLI 호출을 서브프로세스로 감싸 아래 4항목을 모델 협조 없이 기계 수집한다.
  1) 시작 식별자   : os.fork/exec 결과 PID + 프로세스 시작 monotonic 기준점
  2) 중간 사건     : --stream stdout JSONL 각 줄을 수신 시점 monotonic 오프셋과 함께 기록
  3) 종료 봉투     : 프로세스 종료 코드(returncode)
  4) 단조 시계 구간: time.monotonic() 차분 (벽시계 차분 아님)
증거는 stdout 원본(.events.jsonl) + 계측 메타(.probe.json)로 분리 저장한다.
"""
import hashlib, json, os, subprocess, sys, time, datetime

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def main():
    out_prefix = sys.argv[1]
    cmd = sys.argv[2:]
    raw_path = out_prefix + '.events.jsonl'
    meta_path = out_prefix + '.probe.json'
    lines = []
    t0 = time.monotonic()
    started_wall = utc()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    pid = p.pid
    with open(raw_path, 'w') as raw:
        for line in p.stdout:
            off = time.monotonic() - t0
            raw.write(line)
            raw.flush()
            h = hashlib.sha256(line.encode()).hexdigest()
            try:
                typ = json.loads(line).get('type')
            except Exception:
                typ = None
            lines.append({'monotonic_offset_ms': round(off * 1000, 3),
                          'observed_at': utc(), 'type': typ,
                          'bytes': len(line), 'line_sha256': h})
    stderr = p.stderr.read()
    rc = p.wait()
    t1 = time.monotonic()
    meta = {
        'probe_version': '1.0',
        'channel_id': 'oppl-headless-cli',
        'command': cmd,
        'start': {'pid': pid, 'started_at_wall': started_wall, 'monotonic_origin': True},
        'stream_lines': lines,
        'terminal': {'exitcode': rc, 'source_kind': 'process_exit',
                     'ended_at_wall': utc(),
                     'stderr_sha256': hashlib.sha256(stderr.encode()).hexdigest(),
                     'stderr_bytes': len(stderr)},
        'monotonic_span': {'duration_ms': round((t1 - t0) * 1000, 3),
                           'duration_source': 'adapter_monotonic',
                           'clock': 'time.monotonic'},
        'counts': {'total_lines': len(lines),
                   'lines_before_result': sum(1 for x in lines if x['type'] != 'result'),
                   'result_lines': sum(1 for x in lines if x['type'] == 'result')},
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(out_prefix + '.err.log', 'w') as f:
        f.write(stderr)
    with open(out_prefix + '.exitcode', 'w') as f:
        f.write(str(rc) + '\n')
    print(json.dumps({'exitcode': rc, 'lines': len(lines),
                      'duration_ms': meta['monotonic_span']['duration_ms']}))
    return 0

if __name__ == '__main__':
    sys.exit(main())
