// html-mockup shared scripts — 모든 화면 공통 동작

// 1) Lucide 아이콘 초기화 — DOM 로드 후 자동 치환
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
});

// 2) Alpine.js 전역 store — 단일 파일 모드 활성 탭 추적 (§(f) 단일 파일 모드용)
document.addEventListener('alpine:init', () => {
  if (window.Alpine) {
    Alpine.store('ui', {
      activeTab: '',
      setTab(slug) { this.activeTab = slug; }
    });
  }
});

// 3) 해시 변경 시 활성 탭 동기화 (단일 파일 모드)
window.addEventListener('hashchange', () => {
  const slug = location.hash.replace(/^#screen-/, '');
  if (window.Alpine && Alpine.store('ui')) Alpine.store('ui').setTab(slug);
});
