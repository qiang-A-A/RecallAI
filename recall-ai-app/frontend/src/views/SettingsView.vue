<script setup lang="ts">
/** 设置页:AI 模型供应商 / API Key 管理(运行时生效,无需重启)。 */
import { onMounted, ref } from 'vue'
import { settingsApi } from '@/api/client'
import AppButton from '@/components/ui/AppButton.vue'

const status = ref<{ provider: string; model: string; base_url: string; api_key_configured: boolean } | null>(null)
const loading = ref(true)
const apiKey = ref('')
const showKey = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref<{ ok: boolean; msg: string } | null>(null)

async function loadStatus() {
  loading.value = true
  try {
    status.value = await settingsApi.getStatus()
  } catch (e) {
    testResult.value = { ok: false, msg: `获取状态失败:${(e as Error).message}` }
  } finally {
    loading.value = false
  }
}

async function saveKey() {
  const key = apiKey.value.trim()
  if (!key) { testResult.value = { ok: false, msg: '请先输入 API Key' }; return }
  saving.value = true
  testResult.value = null
  try {
    status.value = await settingsApi.setKey(key)
    apiKey.value = ''
    testResult.value = { ok: true, msg: '已保存(内存中,重启后需重新配置)' }
  } catch (e) {
    testResult.value = { ok: false, msg: `保存失败:${(e as Error).message}` }
  } finally {
    saving.value = false
  }
}

async function clearKey() {
  saving.value = true
  try {
    status.value = await settingsApi.clearKey()
    testResult.value = { ok: true, msg: '已清除,回落到 .env 配置' }
  } catch (e) {
    testResult.value = { ok: false, msg: `清除失败:${(e as Error).message}` }
  } finally {
    saving.value = false
  }
}

async function testKey() {
  testing.value = true
  testResult.value = null
  try {
    const r = await settingsApi.test()
    testResult.value = { ok: true, msg: r.message }
  } catch (e) {
    testResult.value = { ok: false, msg: (e as Error).message }
  } finally {
    testing.value = false
  }
}

onMounted(loadStatus)
</script>

<template>
  <div class="max-w-[720px] mx-auto space-y-4">
    <!-- AI 模型设置 -->
    <div class="bg-white border border-[#e5e3df] rounded-[16px] shadow-xs overflow-hidden">
      <div class="px-5 py-4 border-b border-[#e5e3df]">
        <b class="text-sm text-charcoal">AI 模型设置</b>
        <p class="text-xs text-stone mt-0.5">配置 DeepSeek API Key 后,AI 诊断 / 答疑 / 变式生成即可真实调用(静态版 Key 保存在本机浏览器,直连 DeepSeek)</p>
      </div>

      <div class="p-5 space-y-4">
        <div v-if="loading" class="text-center text-xs text-stone py-6">加载中…</div>

        <template v-else-if="status">
          <!-- 当前状态 -->
          <div class="grid grid-cols-3 gap-3">
            <div class="bg-[#fafaf9] border border-[#e5e3df] rounded-[12px] p-3">
              <div class="text-[11px] text-stone mb-1">供应商</div>
              <b class="text-[13px] text-charcoal">{{ status.provider }}</b>
            </div>
            <div class="bg-[#fafaf9] border border-[#e5e3df] rounded-[12px] p-3">
              <div class="text-[11px] text-stone mb-1">模型</div>
              <b class="text-[13px] text-charcoal">{{ status.model }}</b>
            </div>
            <div class="bg-[#fafaf9] border border-[#e5e3df] rounded-[12px] p-3">
              <div class="text-[11px] text-stone mb-1">API Key 状态</div>
              <b class="text-[13px]" :class="status.api_key_configured ? 'text-success' : 'text-error'">
                {{ status.api_key_configured ? '已配置' : '未配置' }}
              </b>
            </div>
          </div>

          <!-- API Key 输入 -->
          <div class="border border-[#e5e3df] rounded-[12px] p-3.5">
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-semibold text-charcoal">API Key</span>
              <button class="text-[11px] text-slate hover:text-charcoal" @click="showKey = !showKey">
                {{ showKey ? '隐藏' : '显示' }}
              </button>
            </div>
            <div class="flex gap-2">
              <input
                v-model="apiKey"
                :type="showKey ? 'text' : 'password'"
                placeholder="sk-… (静态版保存在本机浏览器 localStorage)"
                class="flex-1 border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary"
                @keyup.enter="saveKey"
              />
              <AppButton variant="primary" size="sm" :disabled="saving" @click="saveKey">
                {{ saving ? '保存中…' : '保存' }}
              </AppButton>
              <AppButton variant="secondary" size="sm" :disabled="saving" @click="clearKey">清除</AppButton>
            </div>
          </div>

          <!-- 测试与提示 -->
          <div class="flex items-center gap-3">
            <AppButton variant="secondary" size="sm" :disabled="testing || !status.api_key_configured" @click="testKey">
              {{ testing ? '测试中…' : '测试连接' }}
            </AppButton>
            <span class="text-[11px] text-stone">测试会调用 DeepSeek 发送一条简短消息验证 Key 有效性</span>
          </div>

          <div v-if="testResult"
               class="text-xs px-3 py-2 rounded-lg"
               :class="testResult.ok ? 'bg-success/10 text-[#0a6b1f]' : 'bg-error/10 text-error'">
            {{ testResult.msg }}
          </div>
        </template>
      </div>
    </div>

    <!-- 说明 -->
    <div class="bg-white border border-[#e5e3df] rounded-[16px] p-5 text-xs text-stone space-y-1.5 shadow-xs">
      <b class="text-[13px] text-charcoal block">说明</b>
      <p>· 静态版:API Key 仅保存在本机浏览器(localStorage),浏览器直连 DeepSeek,不经过任何服务器。</p>
      <p>· 运行版:Key 保存在后端内存中,不写入数据库,不会返回明文。</p>
      <p>· 服务重启后需重新配置;也可在 <code class="bg-[#f6f5f4] px-1.5 py-0.5 rounded text-[11px]">backend/.env</code> 中配置 DEEPSEEK_API_KEY 实现持久化。</p>
      <p>· 未配置 Key 时,AI 诊断/答疑/变式会优雅降级,不影响错题录入等基础功能。</p>
    </div>
  </div>
</template>
