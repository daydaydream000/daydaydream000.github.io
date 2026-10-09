/* ==========================================================================
   DayDayDream —— 站点交互脚本（无依赖）
   主题切换 / 站内搜索 / 目录高亮 / 代码复制 / 回到顶部
   ========================================================================== */
(function () {
  'use strict';

  var html = document.documentElement;
  var THEME_KEY = 'theme';

  /* ---------------- 主题切换 ---------------- */
  function applyTheme(theme) {
    var dark = theme === 'dark' || (theme === 'auto' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);
    html.dataset.theme = theme;
    html.classList.toggle('dark', dark);
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* ignore */ }
  }

  var themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', function () {
      var current = html.classList.contains('dark') ? 'dark' : 'light';
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
    // 双击图标恢复“跟随系统”
    themeToggle.addEventListener('dblclick', function () { applyTheme('auto'); });
  }

  var media = window.matchMedia('(prefers-color-scheme: dark)');
  var onSystemChange = function () {
    if (html.dataset.theme === 'auto' || !html.dataset.theme) { applyTheme('auto'); }
  };
  if (media.addEventListener) { media.addEventListener('change', onSystemChange); }
  else if (media.addListener) { media.addListener(onSystemChange); }

  /* ---------------- 代码复制 ---------------- */
  document.querySelectorAll('[data-copy]').forEach(function (button) {
    button.addEventListener('click', function () {
      var block = button.closest('.code-block');
      var code = block && block.querySelector('code');
      if (!code) { return; }
      var text = code.innerText;
      var done = function () {
        button.textContent = '已复制';
        button.classList.add('done');
        window.setTimeout(function () {
          button.textContent = '复制';
          button.classList.remove('done');
        }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.appendChild(area);
        area.select();
        try { document.execCommand('copy'); done(); } catch (e) { /* ignore */ }
        document.body.removeChild(area);
      }
    });
  });

  /* ---------------- 回到顶部 ---------------- */
  var toTop = document.getElementById('back-to-top');
  if (toTop) {
    var onScroll = function () {
      toTop.hidden = window.scrollY < 480;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------------- 目录高亮 ---------------- */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll('.toc-list a'));
  if (tocLinks.length) {
    var targets = tocLinks
      .map(function (link) { return document.getElementById(decodeURIComponent(link.hash.slice(1))); })
      .filter(Boolean);
    if ('IntersectionObserver' in window && targets.length) {
      var visible = new Map();
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) { visible.set(entry.target.id, entry.isIntersecting); });
        var activeId = null;
        targets.forEach(function (target) { if (activeId === null && visible.get(target.id)) { activeId = target.id; } });
        tocLinks.forEach(function (link) {
          var id = decodeURIComponent(link.hash.slice(1));
          link.classList.toggle('current', id === activeId);
        });
      }, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });
      targets.forEach(function (target) { observer.observe(target); });
    }
  }

  /* ---------------- 站内搜索 ---------------- */
  var index = window.SEARCH_INDEX || [];
  var overlay = document.getElementById('search-overlay');
  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var openBtn = document.getElementById('search-toggle');
  var closeBtn = document.getElementById('search-close');
  var lastFocus = null;

  function normalize(text) {
    return (text || '').toLowerCase();
  }

  function escapeHtml(text) {
    return (text || '').replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  function highlight(text, query) {
    var safe = escapeHtml(text);
    if (!query) { return safe; }
    var pattern = escapeHtml(query).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
      return safe.replace(new RegExp('(' + pattern + ')', 'ig'), '<mark>$1</mark>');
    } catch (e) {
      return safe;
    }
  }

  function search(query) {
    var q = normalize(query).trim();
    if (!q) {
      results.innerHTML = '<p class="search-hint">输入关键词开始搜索，支持标题、标签和正文。按 Esc 关闭。</p>';
      return;
    }
    var terms = q.split(/\s+/).filter(Boolean);
    var hits = [];
    index.forEach(function (item) {
      var haystack = normalize([item.title, (item.tags || []).join(' '), item.summary, item.content].join('\n'));
      var score = 0;
      var ok = terms.every(function (term) {
        var at = haystack.indexOf(term);
        if (at === -1) { return false; }
        if (normalize(item.title).indexOf(term) !== -1) { score += 10; }
        if ((item.tags || []).join(' ').toLowerCase().indexOf(term) !== -1) { score += 5; }
        score += 1;
        return true;
      });
      if (ok) { hits.push({ item: item, score: score }); }
    });
    hits.sort(function (a, b) { return b.score - a.score; });

    if (!hits.length) {
      results.innerHTML = '<p class="search-hint">没有找到匹配「' + escapeHtml(query) + '」的内容。</p>';
      return;
    }
    var root = document.body.getAttribute('data-root') || '';
    results.innerHTML = hits.slice(0, 20).map(function (hit) {
      var item = hit.item;
      return '<a class="search-item" href="' + root + item.url + '">' +
        '<h3>' + highlight(item.title, query) + '</h3>' +
        '<p>' + highlight(item.summary || '', query) + '</p>' +
        '<p class="search-meta">' + escapeHtml(item.date || '') +
        ((item.tags || []).length ? ' · ' + escapeHtml(item.tags.join(' / ')) : '') + '</p>' +
        '</a>';
    }).join('');
  }

  function openSearch() {
    if (!overlay) { return; }
    lastFocus = document.activeElement;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
    if (input) {
      input.value = '';
      input.focus();
      search('');
    }
  }

  function closeSearch() {
    if (!overlay || overlay.hidden) { return; }
    overlay.hidden = true;
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
  }

  if (openBtn) { openBtn.addEventListener('click', openSearch); }
  if (closeBtn) { closeBtn.addEventListener('click', closeSearch); }
  if (input) {
    var timer = null;
    input.addEventListener('input', function () {
      window.clearTimeout(timer);
      var value = input.value;
      timer = window.setTimeout(function () { search(value); }, 120);
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter') {
        var first = results.querySelector('.search-item');
        if (first) { window.location.href = first.getAttribute('href'); }
      }
    });
  }
  if (overlay) {
    overlay.addEventListener('click', function (event) {
      if (event.target === overlay) { closeSearch(); }
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') { closeSearch(); }
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((event.target.tagName || '')) || event.target.isContentEditable;
    if (!typing && (event.key === '/' || (event.key === 'k' && (event.metaKey || event.ctrlKey)))) {
      event.preventDefault();
      openSearch();
    }
  });
})();
