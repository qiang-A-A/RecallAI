/* Recall AI 前端渲染验证:Playwright 截图 + 关键元素断言 */
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(String(err)));

  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle' });

  // 等待错题数据加载
  await page.waitForTimeout(1500);

  // 截图
  await page.screenshot({ path: 'shot-questions.png', fullPage: true });

  // 断言关键元素
  const checks = [];
  const hasNav = await page.locator('nav').first().isVisible().catch(() => false);
  checks.push(['顶部导航可见', hasNav]);
  const hasBrand = await page.getByText('Recall', { exact: true }).first().isVisible().catch(() => false);
  checks.push(['Recall 品牌', hasBrand]);
  const hasQ = await page.getByText('单调递减区间').first().isVisible().catch(() => false);
  checks.push(['错题卡片渲染(从后端 API)', hasQ]);

  // 切换 AI 答疑页
  await page.getByRole('button', { name: 'AI 答疑' }).click().catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'shot-ai.png', fullPage: true });
  const hasChat = await page.getByText('AI 答疑助手').isVisible().catch(() => false);
  checks.push(['AI 答疑页', hasChat]);

  // 切换数据看板
  await page.getByRole('button', { name: '数据看板' }).click().catch(() => {});
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'shot-analytics.png', fullPage: true });
  const hasKpi = await page.getByText('题目总数').isVisible().catch(() => false);
  checks.push(['数据看板 KPI', hasKpi]);

  console.log('=== 渲染检查 ===');
  let pass = true;
  for (const [name, ok] of checks) {
    console.log(`${ok ? '✓' : '✗'} ${name}`);
    if (!ok) pass = false;
  }
  console.log(`\nJS 错误数: ${errors.length}`);
  errors.slice(0, 5).forEach((e) => console.log('  ERR:', e.slice(0, 120)));
  console.log(pass && errors.length === 0 ? '\n=== 全部通过 ===' : '\n=== 存在问题 ===');

  await browser.close();
})();
