export const BASE_URL = '/MaaKEDR/'

export const SITE_TITLE = 'MaaKEDR'
export const SITE_DESCRIPTION_ZH = '《雪松》小助手 — 基于 MaaFramework 的自动化工具'
export const SITE_DESCRIPTION_EN = 'KEDR Automation Assistant — Powered by MaaFramework'

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
    htmlLang: 'en-US',
    siteTitle: SITE_TITLE,
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