/* ==========================================================================
   DayDayDream —— 前端交互
   主题切换 / 搜索 / 公告关闭 / 回到顶部 / 代码复制 / 目录高亮
   ========================================================================== */
(function () {
  "use strict";

  var doc = document;
  var root = doc.documentElement;

  /* ---------- 主题 ---------- */
  function applyTheme(mode) {
    root.dataset.theme = mode;
    var dark =
      mode === "dark" ||
      (mode === "auto" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    root.classList.toggle("dark", dark);
    try { localStorage.setItem("dsh-theme", mode); } catch (e) {}
  }

  var themeToggle = doc.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      applyTheme(root.classList.contains("dark") ? "light" : "dark");
    });
  }

  /* ---------- 公告关闭 ---------- */
  var noticeClose = doc.querySelector(".notice-close");
  if (noticeClose) {
    noticeClose.addEventListener("click", function () {
      root.classList.add("notice-off");
      try { localStorage.setItem("dsh-notice", "off"); } catch (e) {}
    });
  }

  /* ---------- 回到顶部 ---------- */
  var toTop = doc.getElementById("back-to-top");
  if (toTop) {
    var onScroll = function () {
      toTop.classList.toggle("show", window.scrollY > 480);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    toTop.addEventListener("click", function (event) {
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ---------- 进入视口时的入场动画 ---------- */
  /* 给需要错峰入场的元素打上 anim-item（由 build.py 输出的 data-reveal 属性决定），
     再用 IntersectionObserver 在进入视口时加 .is-in 并设逐项递增的延迟，
     模仿 Firefly onload-animation 的渐进延迟。observer 不可用时直接全部显示。 */
  var revealTargets = doc.querySelectorAll("[data-reveal]");
  if (revealTargets.length && "IntersectionObserver" in window) {
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduceMotion) {
      root.classList.add("anim-reveal");
      var revealObserver = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            var node = entry.target;
            node.style.animationDelay = Math.min(node.dataset.reveal, 12) * 45 + "ms";
            node.classList.add("is-in");
            revealObserver.unobserve(node);
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
      );
      Array.prototype.forEach.call(revealTargets, function (node) {
        node.classList.add("anim-item");
        revealObserver.observe(node);
      });
      /* 兜底：1.4s 后还没进场的（observer 在某些环境可能漏触发）直接显示，
         保证内容绝不会因为动画系统故障而隐藏 */
      window.setTimeout(function () {
        Array.prototype.forEach.call(revealTargets, function (node) {
          if (!node.classList.contains("is-in")) {
            node.classList.remove("anim-item");
            node.style.opacity = "";
            node.style.animationDelay = "";
          }
        });
      }, 1400);
    }
  }

  /* ---------- 顶部阅读进度条 + 导航栏滚动收缩 ---------- */
  var pageProgress = doc.getElementById("page-progress");
  var topbarEl = doc.querySelector(".topbar");
  if (pageProgress || topbarEl) {
    var progressTicking = false;
    var onProgress = function () {
      var scrollTop = window.scrollY || root.scrollTop;
      var max = root.scrollHeight - window.innerHeight;
      var ratio = max > 0 ? Math.min(1, scrollTop / max) : 0;
      if (pageProgress) {
        pageProgress.style.transform = "scaleX(" + ratio + ")";
        pageProgress.style.opacity = ratio > 0.004 ? "1" : "0";
      }
      if (topbarEl) {
        topbarEl.classList.toggle("is-scrolled", scrollTop > 24);
      }
      progressTicking = false;
    };
    var requestProgress = function () {
      if (!progressTicking) {
        progressTicking = true;
        window.requestAnimationFrame(onProgress);
      }
    };
    window.addEventListener("scroll", requestProgress, { passive: true });
    window.addEventListener("resize", requestProgress);
    onProgress();
  }

  /* ---------- 代码复制 ---------- */
  doc.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var block = button.closest(".code-block");
      var code = block && block.querySelector("code");
      if (!code) return;
      var text = code.innerText;
      var done = function () {
        var old = button.textContent;
        button.textContent = "已复制";
        window.setTimeout(function () { button.textContent = old; }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
      function fallback() {
        var area = doc.createElement("textarea");
        area.value = text;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.opacity = "0";
        doc.body.appendChild(area);
        area.select();
        try { doc.execCommand("copy"); done(); } catch (e) {}
        doc.body.removeChild(area);
      }
    });
  });

  /* ---------- 目录高亮 ---------- */
  var tocLinks = Array.prototype.slice.call(doc.querySelectorAll(".toc-list a[href^='#']"));
  if (tocLinks.length) {
    var heads = tocLinks
      .map(function (link) {
        return doc.getElementById(decodeURIComponent(link.hash.slice(1)));
      })
      .filter(Boolean);
    if (heads.length && "IntersectionObserver" in window) {
      var visible = new Set();
      var observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) visible.add(entry.target.id);
            else visible.delete(entry.target.id);
          });
          var current = heads.find(function (head) { return visible.has(head.id); });
          tocLinks.forEach(function (link) {
            link.classList.toggle("active", !!current && link.hash === "#" + current.id);
          });
        },
        { rootMargin: "-88px 0px -70% 0px", threshold: 0 }
      );
      heads.forEach(function (head) { observer.observe(head); });
    }
  }

  /* ---------- 搜索 ---------- */
  var overlay = doc.getElementById("search-overlay");
  var input = doc.getElementById("search-input");
  var results = doc.getElementById("search-results");
  var index = null;
  var items = [];
  var active = -1;

  function escapeHtml(text) {
    return String(text).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch];
    });
  }

  function highlight(text, query) {
    var safe = escapeHtml(text);
    if (!query) return safe;
    var pattern = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return safe.replace(new RegExp("(" + pattern + ")", "gi"), '<mark class="search-hit">$1</mark>');
  }

  function render(list, query) {
    items = list;
    active = -1;
    if (!list.length) {
      results.innerHTML = '<p class="search-empty">没有匹配的文章</p>';
      return;
    }
    results.innerHTML = list
      .map(function (item, i) {
        return (
          '<a class="search-item" href="' + root.dataset.root + item.url + '" data-i="' + i + '">' +
          '<span class="search-item-title">' + highlight(item.title, query) + "</span>" +
          '<span class="search-item-meta">' + item.date + (item.tags.length ? " · " + escapeHtml(item.tags.join(" / ")) : "") + "</span>" +
          '<span class="search-item-summary">' + highlight(item.summary || "", query) + "</span>" +
          "</a>"
        );
      })
      .join("");
  }

  function search(query) {
    var q = query.trim().toLowerCase();
    if (!q) {
      render(index.slice(0, 8), "");
      return;
    }
    var scored = [];
    index.forEach(function (item) {
      var title = item.title.toLowerCase();
      var tags = item.tags.join(" ").toLowerCase();
      var body = (item.summary + " " + item.content).toLowerCase();
      var score = 0;
      if (title.indexOf(q) >= 0) score += 60;
      if (tags.indexOf(q) >= 0) score += 30;
      if (body.indexOf(q) >= 0) score += 10;
      if (score) {
        if (title.indexOf(q) === 0) score += 20;
        scored.push([score, item]);
      }
    });
    scored.sort(function (a, b) { return b[0] - a[0]; });
    render(scored.slice(0, 20).map(function (pair) { return pair[1]; }), query);
  }

  function openSearch() {
    if (!overlay || !index) return;
    overlay.hidden = false;
    doc.body.style.overflow = "hidden";
    input.value = "";
    render(index.slice(0, 8), "");
    window.setTimeout(function () { input.focus(); }, 30);
  }

  function closeSearch() {
    if (!overlay) return;
    overlay.hidden = true;
    doc.body.style.overflow = "";
    if (input) input.blur();
  }

  function ensureIndex(done) {
    if (index) { done(); return; }
    if (window.SEARCH_INDEX) {
      index = window.SEARCH_INDEX;
      done();
      return;
    }
    var script = doc.querySelector("script[src$='search-index.js']");
    if (script) {
      index = [];
      script.addEventListener("load", function () {
        index = window.SEARCH_INDEX || [];
        done();
      });
      script.addEventListener("error", function () { index = []; done(); });
      return;
    }
    index = [];
    done();
  }

  var toggle = doc.getElementById("search-toggle");
  if (overlay && input && results) {
    if (toggle) {
      toggle.addEventListener("click", function () {
        ensureIndex(openSearch);
      });
    }
    var timer = null;
    input.addEventListener("input", function () {
      var value = input.value;
      window.clearTimeout(timer);
      timer = window.setTimeout(function () { search(value); }, 90);
    });
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) closeSearch();
    });
    doc.addEventListener("keydown", function (event) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test((event.target || {}).tagName || "");
      if (event.key === "Escape" && !overlay.hidden) {
        closeSearch();
        return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        ensureIndex(openSearch);
        return;
      }
      if (event.key === "/" && !typing && overlay.hidden) {
        event.preventDefault();
        ensureIndex(openSearch);
        return;
      }
      if (overlay.hidden) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        if (!items.length) return;
        active = (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        Array.prototype.forEach.call(results.children, function (node, i) {
          node.classList.toggle("active", i === active);
        });
        var current = results.children[active];
        if (current) current.scrollIntoView({ block: "nearest" });
      }
      if (event.key === "Enter" && active >= 0) {
        var picked = results.children[active];
        if (picked) {
          event.preventDefault();
          window.location.href = picked.getAttribute("href");
        }
      }
    });
  }

  /* ---------- 分类栏：溢出时横向滚动 + 两侧渐隐 ---------- */
  var tagBar = doc.querySelector(".tag-bar");
  if (tagBar) {
    var tagScroll = tagBar.querySelector(".tag-scroll");
    var tagFadeLeft = tagBar.querySelector(".tag-fade-left");
    var tagFadeRight = tagBar.querySelector(".tag-fade-right");
    var tagMoreDivider = tagBar.querySelector(".tag-divider-more");

    if (tagScroll) {
      var syncTagBar = function () {
        var max = tagScroll.scrollWidth - tagScroll.clientWidth;
        var hasOverflow = max > 1;
        var atStart = tagScroll.scrollLeft <= 1;
        var atEnd = tagScroll.scrollLeft >= max - 1;
        if (tagFadeLeft) tagFadeLeft.toggleAttribute("data-visible", hasOverflow && !atStart);
        if (tagFadeRight) tagFadeRight.toggleAttribute("data-visible", hasOverflow && !atEnd);
        if (tagMoreDivider) tagMoreDivider.toggleAttribute("data-visible", hasOverflow);
      };

      tagScroll.addEventListener("scroll", syncTagBar, { passive: true });
      window.addEventListener("resize", syncTagBar);

      /* 竖滚轮推到两端后放行页面滚动，中间区段则把列表横向推动 */
      tagScroll.addEventListener(
        "wheel",
        function (event) {
          if (tagScroll.scrollWidth <= tagScroll.clientWidth || event.ctrlKey) return;
          if (Math.abs(event.deltaX) >= Math.abs(event.deltaY)) return;
          var delta =
            event.deltaMode === 1
              ? event.deltaY * 16
              : event.deltaMode === 2
                ? event.deltaY * tagScroll.clientWidth
                : event.deltaY;
          var max = tagScroll.scrollWidth - tagScroll.clientWidth;
          var atStart = tagScroll.scrollLeft <= 1;
          var atEnd = tagScroll.scrollLeft >= max - 1;
          if ((delta < 0 && atStart) || (delta > 0 && atEnd)) return;
          event.preventDefault();
          tagScroll.scrollLeft = Math.min(max, Math.max(0, tagScroll.scrollLeft + delta));
          syncTagBar();
        },
        { passive: false }
      );

      syncTagBar();
      window.addEventListener("load", syncTagBar);
    }
  }
})();
