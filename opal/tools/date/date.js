#!/usr/bin/env node
// date.js — KST 날짜/시각 취득 유틸리티
//
// 사용법: node date.js [format]
//   format:
//     yymmdd    → KST 기준 YYMMDD (예: 260409)
//     date      → KST 기준 YYYY-MM-DD (예: 2026-04-09)
//     datetime  → KST 기준 YYYY-MM-DD HH:mm (예: 2026-04-09 10:29)
//
// 인자 없거나 미지원 포맷: 사용법 출력 후 정상 종료

const format = process.argv[2];

function getKST() {
  const now = new Date();
  const fmt = new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  const parts = fmt.formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type)?.value ?? '';

  const year = get('year');   // 4자리
  const month = get('month'); // 2자리
  const day = get('day');     // 2자리
  const hour = get('hour');   // 2자리 (00-23)
  const minute = get('minute'); // 2자리

  return { year, month, day, hour, minute };
}

function printUsage() {
  console.log('사용법: node date.js [format]');
  console.log('');
  console.log('format:');
  console.log('  yymmdd    — KST 기준 YYMMDD         (예: 260409)');
  console.log('  date      — KST 기준 YYYY-MM-DD      (예: 2026-04-09)');
  console.log('  datetime  — KST 기준 YYYY-MM-DD HH:mm (예: 2026-04-09 10:29)');
}

if (!format) {
  printUsage();
  process.exit(0);
}

const { year, month, day, hour, minute } = getKST();

switch (format) {
  case 'yymmdd': {
    const yy = year.slice(-2);
    console.log(`${yy}${month}${day}`);
    break;
  }
  case 'date': {
    console.log(`${year}-${month}-${day}`);
    break;
  }
  case 'datetime': {
    console.log(`${year}-${month}-${day} ${hour}:${minute}`);
    break;
  }
  default: {
    console.log(`미지원 포맷: ${format}`);
    console.log('');
    printUsage();
    process.exit(0);
  }
}
