/**
 * @header {
 *   "module": "trailing-brace-demo",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "정상 헤더 뒤에 무관한 { 블록이 오는 경우 대조군 (태스크 077 결함 C)",
 *   "exports": ["trailingBraceDemo"]
 * }
 */

// 아래는 헤더와 무관한 예시 설정 객체 — 헤더 인식에 영향을 주면 안 됨
const exampleConfig = {
  scopes: { be: 'workspace/backend/' },
  extensions: ['.py', '.js'],
  exclude: ['node_modules'],
};

function trailingBraceDemo() {
  return exampleConfig;
}

module.exports = { trailingBraceDemo, exampleConfig };
