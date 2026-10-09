# DayDayDream

> 醒着做梦，落笔成诗——记所思，存所学。

个人博客站点：<https://daydaydream000.github.io/>

整站是**纯静态 HTML**，没有数据库、没有服务器，也不依赖任何博客模板或第三方库。
内容用 Markdown 写，由仓库自带的 `build.py` 生成到 `docs/`，GitHub Pages 直接发布这个目录。

```text
Markdown（posts/ · pages/）  →  python build.py  →  docs/  →  git push  →  GitHub Pages
```

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `posts/` | 文章源文件（Markdown + front matter），进入首页列表、标签页和 RSS |
| `pages/` | 独立页面（如「关于」），只出现在导航里 |
| `images/` | 文章中引用的本地图片，构建时自动复制到 `docs/assets/images/` |
| `assets/` | 手写的 `style.css`、`app.js`、`favicon.svg`，原样复制到 `docs/assets/` |
| `templates/` | HTML / XML 模板（`{{变量}}` 占位符） |
| `tools/check_site.py` | 生成结果自检：内部链接、锚点、资源、RSS / sitemap |
| `build.py` | 静态站点生成器（只用 Python 标准库） |
| `docs/` | **构建产物**，也是 GitHub Pages 的发布目录，不要手改 |

## 写一篇文章

在 `posts/` 下新建 `.md` 文件即可，文件名决定 URL（`posts/hello.md` → `/post/hello.html`）：

```markdown
---
title: 文章标题
date: 2026-10-08 21:47:00
tags: [随笔, 建站]
summary: 显示在首页卡片上的摘要，不写就自动截取正文开头。
cover: images/cover.png
pinned: false
draft: false
---

正文从这里开始，标题由模板渲染，不用再写一遍 `# 标题`。
```

支持的 front matter 字段：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `title` | 否 | 不写则取正文第一个 `#` 标题；再没有就用文件名 |
| `date` | 否 | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`；不写则用文件修改时间并给出警告 |
| `updated` | 否 | 有值时文章页额外显示「更新于 …」 |
| `tags` | 否 | 数组或逗号分隔字符串，例如 `[随笔, 建站]` |
| `summary` | 否 | 首页卡片摘要，也用于 RSS 与搜索 |
| `cover` | 否 | 封面图，出现在文章顶部与首页卡片 |
| `slug` | 否 | 自定义 URL 文件名（默认取源文件名的英文/数字部分） |
| `pinned` | 否 | `true` 时置顶 |
| `draft` | 否 | `true` 时不参与构建 |
| `author` | 否 | 覆盖默认作者 |

独立页面放到 `pages/`，写法相同，通常加一个 `slug` 让 URL 更好看（`slug: about` → `/about.html`）。
新建页面后记得在 `build.py` 顶部的 `CONFIG["nav"]` 里加上导航项。

## 支持的 Markdown 语法

标题、段落、**粗体**、*斜体*、`行内代码`、~~删除线~~、==高亮==、链接、有序 / 无序 / 嵌套列表、
任务列表、引用、围栏代码块（带语言标签和复制按钮）、表格（支持 `:---:` 对齐）、分隔线、
以及直接书写 HTML 块。

图片写 `![图注](images/x.png)`；**独占一段**时会渲染成带图注的 `<figure>`，否则作为行内图片。
本地图片会被自动复制到 `docs/assets/images/`，外链图片（`http(s)://`、`data:`）原样保留。

引用块支持 GitHub 风格的提示框：

```markdown
> [!NOTE]
> 支持 NOTE / TIP / IMPORTANT / WARNING / CAUTION 五种。
```

## 本地构建与预览

需要 Python 3.9+，无第三方依赖：

```bash
python build.py            # 生成整站到 docs/
python tools/check_site.py # 自检：链接、锚点、资源、RSS、sitemap
```

直接双击 `docs/index.html` 也能预览（站内链接全部用相对路径，不依赖服务器）。
若要模拟真实环境，可在 `docs/` 下起一个静态服务器，例如 `python -m http.server -d docs 8000`。

## 部署到 GitHub Pages

发布源是 **`main` 分支的 `/docs` 目录**，按官方文档
[Configuring a publishing source for your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
配置：

1. 在 GitHub 打开仓库，进入 **Settings**；
2. 左侧边栏 **Code, planning, and automation** → **Pages**；
3. **Build and deployment** → **Source** 选 **Deploy from a branch**；
4. 分支选 **`main`**，文件夹选 **`/docs`**，点击 **Save**。

之后每次把改动推到 `main`，GitHub Pages 就会重新发布 `docs/` 里的内容：

```bash
git add -A
git commit -m "post: 新文章"
git push
```

仓库里没有 `.github/workflows/`，构建完全在本地完成——推上去的 `docs/` 是什么，线上就是什么。

## 自定义

- **站名、副标题、作者、域名、每页篇数、导航项**：改 `build.py` 顶部的 `CONFIG`；
- **头像**：换成 `assets/avatar.png`（默认，站点不依赖任何第三方域名），也可以填外链 `https://…`；
- **配色、字体、版式**：改 `assets/style.css` 顶部的 CSS 变量（`--accent`、`--content-width`、`--bg`…），深浅色主题各有独立变量；
- **页面结构**：改 `templates/` 下的模板，`{{key}}` 是 `build.py` 传入的变量；
- **社交分享图**：文章页优先用 front matter 里的 `cover`，其余页面回退到 `CONFIG["avatar"]`。

> 修改 `docs/` 里的任何文件都会在下次 `python build.py` 时被覆盖，请改源文件。

## 许可

除特别注明外，本站内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh) 许可协议，转载请注明出处。
`build.py`、`templates/`、`assets/` 等站点代码可自由取用。
