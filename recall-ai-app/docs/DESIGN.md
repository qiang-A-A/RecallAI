# DESIGN.md — Recall AI 智能错题本 · 设计系统规范

> **版本**: v1.0 | **设计者**: Diana (Design System Architect)
> **品牌参考**: Notion(色彩/知识管理语言) × Linear(排版/克制阴影) × Claude(温暖 AI 氛围)
> **配套文档**: 《Recall AI 业务流程设计 v2.0》《Recall AI MVP 技术文档 v1.0》《Recall AI 竞品分析报告 v1.0》
> **可用平台**: Web (桌面端优先) / 微信小程序(同源 Token 缩放)

---

## 1. Visual Theme & Atmosphere(视觉主题与氛围)

**设计哲学** — "学习不是惩罚,是成长"。Recall AI 希望呈现:像 Notion 一样清晰可信的知识管理底座,像 Linear 一样克制高效的工具感,叠加一层 AI 陪伴的温暖。产品要让学生感到"这是我自己的学习空间",而不是"又一个教辅 App"。

**视觉基调**: 明亮 · 轻盈 · 专注。浅色为主(学生长时间使用),大面积留白,信息密度按"复习场景低 / 看板场景中"分档。

**核心视觉特征关键词**:
- `清晰` (Clear) — 层级分明,一眼找到"今天该做什么"
- `轻盈` (Light) — 柔和卡片色、细边框、弱阴影,不压迫
- `成长` (Growth) — 掌握度用薄荷绿渐进,错误用暖橙而非刺目红
- `AI 感` (AI-native) — 紫色系用于 AI 能力,与用户操作(蓝)严格分离

**光影与质感**: 纯扁平 + 微阴影(Linear 式克制阴影),不用毛玻璃大面积铺陈;仅全局 AI 对话浮层可用 8% 透明度毛玻璃提升层级感。

---

## 2. Color Palette & Roles(调色板与角色)

### 2.1 Primary Colors(主色)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--primary` | `#5645d4` | 品牌主色 / 主要 CTA / AI 焦点 / 选中态 |
| `--primary-pressed` | `#4534b3` | 主色按下态 |
| `--primary-deep` | `#3a2a99` | 主色深变体(渐变收尾/强调文字) |
| `--on-primary` | `#ffffff` | 主色上的文字/图标 |

### 2.2 Brand & Dark(品牌色与深色变体)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--brand-navy` | `#0a1530` | 品牌深藏青:Hero 底、登录页、空状态底色 |
| `--brand-navy-deep` | `#070f24` | 深藏青极深变体(渐变端点) |
| `--brand-navy-mid` | `#1a2a52` | 导航栏悬浮态 |
| `--brand-purple` | `#7b3ff2` | AI 能力强调(AI 对话/诊断标签) |
| `--brand-purple-300` | `#d6b6f6` | 浅紫(图标底/徽章底) |

### 2.3 Accent / Interactive(强调与交互色)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--link-blue` | `#0075de` | 用户操作入口 / 文本链接 / 蓝 = 用户行为 |
| `--link-blue-pressed` | `#005bab` | 链接按下态 |
| `--warning` | `#dd5b00` | 判断分支 / "模糊"状态 / 复习提醒 |
| `--info` | `#0075de` | 信息提示 / 系统通知 |

### 2.4 Neutral / Gray Scale(中性灰阶)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--ink` | `#1a1a1a` | 正文主文字 |
| `--charcoal` | `#37352f` | 标题文字(暖黑,Notion 风) |
| `--slate` | `#5d5b54` | 次级文字 |
| `--steel` | `#787671` | 辅助说明文字 |
| `--stone` | `#a4a097` | 禁用态 / 占位 |
| `--muted` | `#bbb8b1` | 最弱层级(表格表头) |

### 2.5 Surface & Borders(表面与边框)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--canvas` | `#ffffff` | 页面主画布 |
| `--surface` | `#f6f5f4` | 次级表面(侧栏/卡片内底) |
| `--surface-soft` | `#fafaf9` | 页面背景(默认) |
| `--hairline` | `#e5e3df` | 常规边框/分隔线 |
| `--hairline-strong` | `#c8c4be` | 强调边框(卡片描边) |

### 2.6 Semantic Colors(语义色)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--success` | `#1aae39` | 已掌握 / 成功 / 系统处理 |
| `--success-tint` | `#d9f3e1` | 成功浅底(标签/节点) |
| `--warning` | `#dd5b00` | 模糊 / 待复习 / 提醒 |
| `--warning-tint` | `#ffe8d4` | 警告浅底 |
| `--error` | `#e03131` | 不会 / 严重异常 / 删除 |
| `--error-tint` | `#fde0ec` | 错误浅底 |

### 2.7 Soft Card Tints(柔和卡片色 — Notion card-tint)

| CSS 变量 | HEX | 用途 |
|---|---|---|
| `--tint-lavender` | `#e6e0f5` | AI 诊断卡片 / 知识点标签底 |
| `--tint-sky` | `#dcecfa` | 用户操作入口底 |
| `--tint-mint` | `#d9f3e1` | 掌握度/已完成底 |
| `--tint-peach` | `#ffe8d4` | 复习提醒/待办底 |
| `--tint-yellow` | `#fef7d6` | 变式训练/强化底 |
| `--tint-cream` | `#f8f5e8` | 中性提示底 |

### 2.8 Shadow Colors(阴影色)

| CSS 变量 | rgba | 用途 |
|---|---|---|
| `--shadow-color-sm` | `rgba(10, 21, 48, 0.05)` | 微阴影(卡片默认) |
| `--shadow-color-md` | `rgba(10, 21, 48, 0.08)` | 悬浮卡片 |
| `--shadow-color-lg` | `rgba(10, 21, 48, 0.10)` | 弹窗/抽屉 |

---

## 3. Typography Rules(排版规则)

### 3.1 Font Family(字体族)

```css
--font-sans: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
             "Noto Sans SC", "Inter", -apple-system, sans-serif;
--font-mono: ui-monospace, SFMono-Regular, Consolas, "JetBrains Mono", monospace;
```

> 中文场景以 PingFang/雅黑为主;数字与公式使用 Inter 的 tabular-nums;数学公式用 `--font-mono`。

### 3.2 Type Scale(完整层级表)

| 层级 | Font Size | Weight | Line Height | Letter Spacing | 用途 |
|---|---|---|---|---|---|
| Display | 32px / 2rem | 700 | 1.20 | -0.02em | 品牌 Hero 标题 |
| H1 | 26px / 1.625rem | 650 | 1.25 | -0.01em | 页面主标题 |
| H2 | 20px / 1.25rem | 650 | 1.30 | -0.01em | 区块标题 |
| H3 | 16px / 1rem | 600 | 1.40 | 0 | 卡片标题 |
| Body-LG | 15px / 0.9375rem | 400 | 1.60 | 0 | 正文(阅读场景) |
| Body | 14px / 0.875rem | 400 | 1.65 | 0 | 默认正文 |
| Body-Medium | 14px / 0.875rem | 500 | 1.55 | 0 | 列表项/表格 |
| Caption | 12px / 0.75rem | 400 | 1.50 | 0 | 辅助说明 |
| Caption-Bold | 12px / 0.75rem | 600 | 1.40 | 0.04em | 表头/按钮文字 |
| Micro | 11px / 0.6875rem | 500 | 1.40 | 0.06em | 标签/徽章/时间戳 |

### 3.3 设计哲学

- **标题用 600-700 半粗,不追求超黑**:中文字重过大易糊,650 是 Recall 的标志性字重
- **正文行高 1.6-1.65**:学生长时间阅读,行高偏大缓解疲劳
- **数字用等宽对齐**:复习计数、进度百分比用 `font-variant-numeric: tabular-nums`,避免跳动
- **字母间距克制**:仅 Micro 级(标签)允许 0.04-0.06em 加宽,标题一律负字距贴近现代感

---

## 4. Component Stylings(组件样式)

### 4.1 Buttons(按钮)

```css
/* Primary 主按钮 — 品牌紫 */
.btn-primary {
  background: var(--primary); color: #fff;
  border: none; border-radius: 8px;
  padding: 10px 20px; font-size: 14px; font-weight: 600;
  box-shadow: var(--shadow-sm);
  transition: background .15s, transform .1s;
}
.btn-primary:hover { background: var(--primary-pressed); }
.btn-primary:active { transform: scale(.98); }
.btn-primary:disabled { background: var(--stone); cursor: not-allowed; }

/* Secondary 次按钮 — 白底描边 */
.btn-secondary {
  background: #fff; color: var(--charcoal);
  border: 1px solid var(--hairline-strong);
  border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 500;
}
.btn-secondary:hover { border-color: var(--primary); color: var(--primary); }

/* Ghost 幽灵按钮 — 无底 */
.btn-ghost {
  background: transparent; color: var(--slate);
  border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px;
}
.btn-ghost:hover { background: var(--surface); color: var(--charcoal); }

/* Danger 危险按钮 — 删除 */
.btn-danger {
  background: var(--error); color: #fff;
  border: none; border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 600;
}
.btn-danger:hover { background: #b3272b; }
```

**按钮圆角统一 `8px`;最小点击区域 44×44px(移动端)。**

### 4.2 Cards(卡片)

```css
.card {
  background: #fff;
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow .15s, transform .15s;
}
.card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.card--interactive { cursor: pointer; border-color: var(--hairline-strong); }
```

### 4.3 Inputs(输入框)

```css
.input {
  background: #fff;
  border: 1px solid var(--hairline-strong);
  border-radius: 8px;
  padding: 10px 14px; font-size: 14px;
  transition: border-color .15s, box-shadow .15s;
}
.input::placeholder { color: var(--stone); }
.input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(86, 69, 212, 0.12);
}
```

### 4.4 Navigation(导航)

```css
.nav {
  height: 56px;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(8px);           /* 仅导航允许毛玻璃 */
  border-bottom: 1px solid var(--hairline);
  position: sticky; top: 0; z-index: 100;
}
.nav-item {
  color: var(--slate); font-size: 14px; font-weight: 500;
  padding: 6px 14px; border-radius: 8px;
}
.nav-item:hover { background: var(--surface); color: var(--charcoal); }
.nav-item.active { color: var(--primary); background: var(--tint-lavender); font-weight: 600; }
```

### 4.5 Badges / Tags(徽章与标签)

```css
.badge { display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 600; }
.badge--ai    { background: var(--tint-lavender); color: var(--primary-deep); }
.badge--user  { background: var(--tint-sky); color: #005bab; }
.badge--sys   { background: var(--success-tint); color: #0a7a23; }
.badge--warn  { background: var(--warning-tint); color: #9c3f00; }
.badge--done  { background: var(--tint-mint); color: #0a6b1f; }
```

### 4.6 Modals / Dialogs(弹窗)

```css
.modal-mask {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(10, 21, 48, 0.40);   /* 深藏青遮罩 */
  display: flex; align-items: center; justify-content: center;
  animation: fadeIn .18s ease;
}
.modal {
  background: #fff; border-radius: 16px;
  padding: 24px; width: min(480px, 92vw);
  box-shadow: var(--shadow-lg);
  animation: slideUp .22s cubic-bezier(.16,1,.3,1);
}
@keyframes fadeIn  { from { opacity: 0 } to { opacity: 1 } }
@keyframes slideUp { from { opacity: 0; transform: translateY(12px) } to { opacity: 1; transform: none } }
```

### 4.7 Model Provider Settings(模型供应商设置)

> Recall AI 支持切换/配置多个 AI 模型供应商(DeepSeek / OpenAI / GLM / 通义千问等),用于知识诊断、复习讲解、变式生成三类任务。该组件位于「设置与帮助 → AI 模型设置」页,遵循"密钥最小可见、状态一目了然、降级透明"原则。

```css
/* Provider Card — 供应商卡片 */
.provider-card {
  display: flex; align-items: center; gap: 14px;
  background: #fff;
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: var(--shadow-xs);
  transition: border-color .15s, box-shadow .15s;
}
.provider-card:hover { border-color: var(--hairline-strong); }
.provider-card.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(86, 69, 212, 0.10);
}
.provider-logo {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface); font-size: 20px;
}
.provider-meta { flex: 1; min-width: 0; }
.provider-name { font-size: 14px; font-weight: 600; color: var(--charcoal); }
.provider-desc { font-size: 12px; color: var(--steel); }

/* API Key Input — 密钥输入(掩码 + 切换可见) */
.api-key-field {
  display: flex; align-items: center; gap: 8px;
  background: var(--surface-soft);
  border: 1px solid var(--hairline-strong);
  border-radius: 8px;
  padding: 8px 12px;
}
.api-key-field .key-value {
  flex: 1; font-family: var(--font-mono); font-size: 12.5px;
  color: var(--slate); letter-spacing: .02em;
}
.api-key-field input[type="password"] { border: none; background: transparent; width: 100%; }
.api-key-field .toggle-key { color: var(--steel); cursor: pointer; padding: 4px; }
.api-key-field .toggle-key:hover { color: var(--primary); }

/* Connection Status — 连接状态指示 */
.conn-status { display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 600; padding: 3px 10px; border-radius: 999px; }
.conn-status .dot { width: 8px; height: 8px; border-radius: 50%; }
.conn-ok    { background: var(--success-tint); color: #0a7a23; }
.conn-ok .dot    { background: var(--success); }
.conn-fail  { background: var(--error-tint); color: #a0233c; }
.conn-fail .dot  { background: var(--error); }
.conn-empty { background: var(--surface); color: var(--steel); border: 1px solid var(--hairline); }
.conn-empty .dot { background: var(--stone); }

/* Model Select — 模型选择(按用途分组) */
.model-group { margin-bottom: 16px; }
.model-group-title { font-size: 12px; font-weight: 600; color: var(--slate); margin-bottom: 8px; }
.model-option {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px; cursor: pointer;
}
.model-option:hover { background: var(--surface); }
.model-option.selected { background: var(--tint-lavender); }
.model-option.selected .model-name { color: var(--primary-deep); font-weight: 600; }
.model-name { font-size: 13px; color: var(--charcoal); }
.model-tag { font-size: 10.5px; color: var(--steel); background: var(--surface);
  padding: 1px 6px; border-radius: 4px; }

/* Usage Quota — 用量配额条 */
.quota-bar { height: 6px; border-radius: 3px; background: var(--surface); overflow: hidden; }
.quota-bar .fill { height: 100%; border-radius: 3px; background: var(--primary);
  transition: width .3s ease; }
.quota-bar .fill.warn { background: var(--warning); }
.quota-meta { display: flex; justify-content: space-between; font-size: 11.5px;
  color: var(--steel); margin-top: 6px; }
```

**模型供应商设置交互要点**:

| 状态 | 视觉 | 交互规则 |
|---|---|---|
| 未配置 | `conn-empty` 灰点 + "未配置" | 卡片可点,展开 API Key 输入;显示密钥加密存储提示 |
| 已连接 | `conn-ok` 绿点 + "已连接 · 延迟 xx ms" | 支持"测试连接"按钮;可切换为默认供应商 |
| 连接失败 | `conn-fail` 红点 + "连接失败" | 展示错误原因 + "重试";自动降级到备选供应商并提示 |
| 默认供应商 | 卡片 `active` 态(紫描边 + 3px 光圈) | 全站 AI 任务优先使用;标注"默认"徽章 |

- **任务分流**:诊断 / 复习讲解 / 变式生成三类任务可分别指定不同供应商与模型(成本优化:高精度任务用旗舰,批量任务用轻量)
- **密钥安全**:API Key 默认 `type="password"` 掩码显示,可切换可见;仅存服务端加密(前端不回显完整 Key),日志脱敏
- **降级透明**:默认供应商异常时,系统自动切换备选并在 AI 对话流顶部显示"当前由 xx 提供 AI 服务"轻提示(不阻断使用)

---

## 5. Layout Principles(布局原则)

### 5.1 Spacing System(间距系统)

**基数 4px**: `4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`。卡片内边距默认 20px,区块间距 48px,页面左右留白 32px。

### 5.2 Grid System(栅格系统)

- **12 列栅格**,列间距 16px(桌面)/ 8px(移动)
- 最大内容宽度 `1180px`
- 复习清单用两列卡片流(桌面);看板用 3-4 列小卡片

### 5.3 Container(容器)

```css
.container { max-width: 1180px; margin: 0 auto; padding: 0 32px; }
.page-padding { padding: 32px 0 96px; }
.section-gap { margin-bottom: 48px; }
```

### 5.4 留白哲学

- **复习页大留白**:单题复习是"专注场景",卡片四周留 64px+,消除干扰
- **错题列表中等密度**:列表是"扫读场景",行距 12px,信息密度高
- **看板克制堆叠**:最多 4 列,超过即分页或折叠,不搞"数据墙"

---

## 6. Depth & Elevation(深度与层级)

### 6.1 Shadow System(阴影系统)

```css
--shadow-xs: 0 1px 2px rgba(10,21,48,.05);
--shadow-sm: 0 1px 3px rgba(10,21,48,.06), 0 1px 2px rgba(10,21,48,.04);
--shadow-md: 0 4px 12px rgba(10,21,48,.08), 0 2px 4px rgba(10,21,48,.04);
--shadow-lg: 0 12px 32px rgba(10,21,48,.10), 0 4px 8px rgba(10,21,48,.05);
--shadow-xl: 0 24px 60px rgba(10,21,48,.14), 0 8px 16px rgba(10,21,48,.06);
```

### 6.2 Surface Layers(表面层级)

| 层级 | 变量 | 用途 |
|---|---|---|
| background | `--surface-soft` | 页面底 |
| surface | `--surface` | 侧栏/分组底 |
| elevated | `#ffffff + shadow-sm/md` | 卡片 |
| overlay | `#ffffff + shadow-lg` | 弹窗/抽屉 |
| modal | `#ffffff + shadow-xl` | 全屏确认/编辑 |

### 6.3 Z-index Scale

```
10    sticky 导航
100   悬浮按钮 / 快捷入口
200   下拉 / 浮层
300   弹窗遮罩与弹窗
400   全局 AI 对话浮层(最高)
```

### 6.4 Backdrop Effects

```css
/* 仅两处允许毛玻璃:导航栏 + AI 对话浮层 */
--blur-nav:  blur(8px);
--blur-ai:   blur(12px); background: rgba(255,255,255,.82);
```

---

## 7. Do's and Don'ts(设计规范与禁忌)

### Do's(应遵循)

1. **用户操作 = 蓝,AI 处理 = 紫,系统状态 = 绿** —— 三色语义贯穿全站,见 `<span class="badge">` 体系
2. **复习/录入入口全局可达** —— 任何页面右下角有悬浮"+"(录入)与"⚡"(一键复习)
3. **掌握度用薄荷绿渐进表达** —— 从灰(未学)→ 浅绿 → 深绿,避免用红色表达"差"
4. **空状态要有引导** —— 错题本为空时展示"录入第一道错题"大按钮 + 示例
5. **数字等宽对齐** —— 计数、进度、时长用 tabular-nums
6. **错误提示可操作** —— 报错旁带"重试/修正"按钮,不裸抛错误码
7. **点击反馈即时** —— 按钮 active 态 scale(.98),卡片 hover 微抬升

### Don'ts(应避免)

1. **禁用大面积纯红表达"错误"** —— 学生产品心理负担重,用暖橙 `#dd5b00` 替代
2. **禁止超过 3 级信息层级** —— 页面深度一律 ≤ 导航 → 模块页 → 详情/弹窗
3. **禁止广告与诱导按钮** —— 核心闭环无商业化元素(品牌承诺)
4. **禁止 AI 输出无来源** —— 诊断/讲解必须带知识点来源或"AI 生成"标识
5. **禁止字体小于 11px** —— 正文不低于 14px,注释不低于 12px
6. **禁止纯黑 `#000` 文字** —— 用 `--charcoal` 暖黑,阅读更柔和
7. **禁止弹窗套弹窗** —— 需要二次确认时用行内展开而非叠加弹层
8. **禁止所有页面同样密度** —— 复习页必须比看板页留白多

---

## 8. Responsive Behavior(响应式行为)

### 8.1 Breakpoints

| 断点 | 宽度 | 策略 |
|---|---|---|
| mobile | `< 640px` | 底部 Tab 导航(首页/错题本/复习/我的),悬浮按钮缩小为 48px |
| tablet | `640-1024px` | 左侧栏收为图标栏,卡片 2 列 |
| desktop | `1024-1440px` | 完整侧栏,12 列栅格 |
| wide | `> 1440px` | 内容居中 1180px,两侧留白 |

### 8.2 Touch Targets(触摸目标)

- 最小点击区域 **44×44px**(移动端)、**32×32px**(桌面)
- 底部 Tab 高度 ≥ 56px,悬浮按钮 ≥ 56px

### 8.3 折叠策略

- 侧栏(收藏夹/筛选器)→ tablet 以下收起为抽屉
- 错题详情(题干/解答/AI 诊断)→ 移动端用标签页 Tab 折叠,不用堆叠
- 数据看板 4 列卡片 → mobile 折叠为单列手风琴

### 8.4 Font Scaling

- 桌面固定 14-16px 正文;移动端正文下限保持 14px(不随设备缩小)
- 标题用 `clamp(22px, 4vw, 26px)` 弹性缩放
- 中文不启用文字缩放导致的换行错乱,容器保留 `overflow-wrap: break-word`

---

## 9. Agent Prompt Guide(AI 代理提示指南)

### 9.1 Quick Reference(快速参考摘要)

```
品牌: Recall AI 智能错题本(学生错题学习工具)
主色: #5645d4 (紫, AI)  蓝 #0075de (用户操作)  绿 #1aae39 (系统/掌握)
中性: 文字 #37352f / 次级 #5d5b54 / 边框 #e5e3df / 页面底 #fafaf9
圆角: 按钮 8px · 卡片 14px · 弹窗 16px
间距: 4px 基数, 卡片内 20px, 区块 48px
阴影: Linear 式克制阴影, 5 级 (xs/sm/md/lg/xl)
字体: PingFang SC / 微软雅黑 / Inter; 正文 14px 行高 1.65
核心规范: 层级 ≤3 级 · 三色语义(蓝/紫/绿) · 复习页大留白 · 无广告
模型供应商: 支持多供应商配置(BYOK), 诊断/讲解/变式可分模型, 密钥加密存储
```

### 9.2 Component Prompts(组件生成 Prompt 示例)

```text
1. 生成 Recall AI 的"今日复习卡片"组件:显示题目数、预计用时、
   掌握度环形进度(薄荷绿渐变),右下角带"开始复习"主按钮(品牌紫)。
   遵循 DESIGN.md 的 card/button/typography 规范。

2. 生成错题列表页:左侧学科筛选(徽章样式)、列表行含题干缩略、
   AI 诊断标签(紫色)、掌握度徽章(绿/橙)、时间戳;支持按错误次数筛选。

3. 生成"AI 知识点诊断"结果面板:候选知识点卡片(薰衣草底)、
   置信度进度条(紫)、"确认/重新诊断"按钮、AI 生成标识。

4. 生成数据看板页:掌握度矩阵(热力图用薄荷绿渐变)、错因 TOP5
   横向条形图(暖橙)、学习趋势折线;数字用 tabular-nums。

5. 生成复习页空状态:深藏青渐变底、"还没有到期复习"标题、
   "去录一道错题"主按钮 + 示例题卡片,引导而非惩罚。

6. 生成 AI 对话浮层:右下角悬浮(最高 z-index)、毛玻璃背景、
   紫色 AI 标识、消息气泡(用户蓝/AI 白)、快捷提问 chip。

7. 生成"AI 模型设置"页:供应商卡片列表(DeepSeek/OpenAI/GLM/通义,
   含 logo、连接状态徽章、默认标记)、API Key 掩码输入(可切换可见)、
   按用途分组的模型选择(诊断/讲解/变式)、用量配额进度条。
   遵循 DESIGN.md §4.7 的 provider-card / api-key-field / conn-status 规范。
```

### 9.3 Iteration Guide(AI 生成 UI 迭代建议)

1. 首版先建 **color token 表**,所有颜色只引用 CSS 变量,禁止硬编码
2. 每次生成后自查:文字颜色是否用了 `--charcoal` 而非 `#000`
3. 卡片默认 `--shadow-sm`,hover 升 `--shadow-md`,不跳级
4. 复习类页面主动减少元素:单屏信息 ≤ 3 个区块
5. 所有"掌握/模糊/不会"状态必须映射到语义色,不新增色值
6. 数字展示统一加 `font-variant-numeric: tabular-nums`
7. 空状态必须带"下一步动作"按钮,否则视为未完成
8. 移动端每个可点元素检查是否 ≥ 44px,不足则补 padding
9. 弹窗场景优先考虑"行内展开"替代,弹窗套弹窗为反模式
10. 交付前跑一遍对比:紫色 = AI 能力、蓝色 = 用户操作、绿色 = 系统/掌握

---

*End of DESIGN.md v1.0 — 与 Recall AI 全部产品文档保持一致的设计语言。*
