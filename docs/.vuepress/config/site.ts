export const BASE_URL = '/MaaKEDR/'

/**
 * 站点名要带上用户真正会搜的词。
 *
 * 用户不会搜 "MaaKEDR" 这个项目代号——他们搜的是游戏名加用途：「雪松小助手」
 * 「雪松自动化」「雪松脚本」。原先把 title 写成纯 "MaaKEDR"，渲染出来是
 * "<title>MaaKEDR | MaaKEDR</title>"，搜索引擎能匹配到的关键词只有项目名，
 * 结果就是搜游戏名根本找不到这个站。
 *
 * 所以标题采用「游戏名 + 用途 + 项目名」的排列：前两段负责被搜到，
 * 项目名放在最后维持品牌一致性。竖线是搜索引擎结果里最常见的分隔符，
 * Plume 自己也会用 " | " 拼「页面标题 | 站点标题」。
 */
export const SITE_TITLE = '雪松小助手 MaaKEDR · 雪松自动化脚本'
export const SITE_TITLE_EN = 'MaaKEDR · KEDR Automation Assistant'
export const SITE_DESCRIPTION_ZH =
    '雪松小助手（MaaKEDR）是《雪松》游戏的自动化工具，基于 MaaFramework 实现图像识别与模拟控制，支持启动游戏、领取奖励、资源刷取、PvP 对战等任务的自动完成，解放双手。'
export const SITE_DESCRIPTION_EN =
    'MaaKEDR (Cedar Assistant) is an automation tool for the game Cedar, built on MaaFramework with image recognition and simulated input. It automates game launch, reward claiming, resource farming and PvP battles.'

// 站点根域名（不含 base）。base 为 /MaaKEDR/ 时若再写进 HOSTNAME，会生成双重 /MaaKEDR/MaaKEDR/ 链接。
export const HOSTNAME = 'https://apple-df.github.io'

export interface Locale {
  name: string
  htmlLang: string
  siteTitle: string
  siteDescription: string
}

export const locales: Locale[] = [
  {
    name: 'zh',
    htmlLang: 'zh-CN',
    siteTitle: SITE_TITLE,
    siteDescription: SITE_DESCRIPTION_ZH,
  },
  {
    name: 'en',
    // 英文站不复用中文标题：中文关键词出现在 en 页面里对英文搜索结果毫无帮助，
    // 反而会让标题看着像混排。英文侧用 KEDR Automation Assistant 这个既定叫法。
    htmlLang: 'en-US',
    siteTitle: SITE_TITLE_EN,
    siteDescription: SITE_DESCRIPTION_EN,
  },
]

export function normalizeBaseUrl(baseUrl: string): string {
  return baseUrl.replace(/\/+$/, '')
}

export function buildHomePaths(baseUrl: string, locales: Locale[]): string[] {
  const normalized = normalizeBaseUrl(baseUrl)
  const paths = [normalized, `${normalized}/index.html`]
  for (const locale of locales) {
    paths.push(`${normalized}/${locale.name}/`, `${normalized}/${locale.name}/index.html`)
  }
  return paths
}

export function genSiteLocales(): Record<string, { lang: string; title: string; description: string }> {
  const siteLocales: Record<string, { lang: string; title: string; description: string }> = {}
  for (const locale of locales) {
    siteLocales[`/${locale.name}/`] = {
      lang: locale.htmlLang,
      title: locale.siteTitle,
      description: locale.siteDescription,
    }
  }
  return siteLocales
}