import { viteBundler } from '@vuepress/bundler-vite'
import { defineUserConfig } from 'vuepress'
import { plumeTheme } from 'vuepress-theme-plume'

import {
  genSiteLocales,
  HOSTNAME,
  BASE_URL,
  locales,
  SITE_TITLE,
  SITE_TITLE_EN,
  SITE_DESCRIPTION_ZH,
} from './config/site.ts'

/** 全站统一的 Open Graph 分享图（站标）。 */
const OG_IMAGE = `${HOSTNAME}${BASE_URL}images/maakedr-logo_512x512.png`

export default defineUserConfig({
  base: BASE_URL,
  lang: 'zh-CN',
  // 站点名/描述统一从 config/site.ts 取，避免两处各写一份后忘了同步。
  title: SITE_TITLE,
  description: SITE_DESCRIPTION_ZH,

  locales: genSiteLocales(),

  plugins: [],

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: `${BASE_URL}images/maakedr-logo_512x512.png` }],
    ['meta', { name: 'baidu-site-verification', content: 'codeva-GnOwnwiCSA' }],
    ['meta', { name: 'msvalidate.01', content: '6A49AB032E4ED1D8DC8BD5B30324C3ED' }],
    ['meta', { name: 'google-site-verification', content: 'bLO4xMnM1-AK3Gw_hBpnuPxb3ztH4QW0HCHK_1_M7Tg' }],
  ],

  bundler: viteBundler(),

  shouldPrefetch: false,

  theme: plumeTheme({
    hostname: HOSTNAME,

    docsRepo: 'APPLe-DF/MaaKEDR',
    docsDir: 'docs',
    docsBranch: 'main',

    editLink: true,
    lastUpdated: false,
    contributors: false,
    changelog: false,

    cache: 'filesystem',

    autoFrontmatter: {
      permalink: false,
      createTime: false,
      title: false,
    },

    search: {
      provider: 'local',
    },

    markdown: {
      image: {
        figure: true,
        lazyload: true,
        mark: true,
        size: true,
      },
      fileTree: {
        icon: 'colored',
      },
    },

    watermark: false,

    /**
     * 内置插件配置。
     *
     * 注意这些都必须是 `plumeTheme({...})` 的参数 —— 放在 `plume.config.ts` 的顶层
     * 不会被读到：主题侧是用 `getThemeConfig().xxx ?? plugins.xxx` 取值的，
     * `getThemeConfig()` 只返回传给 plumeTheme 的对象。
     */
    plugins: {
      seo: {
        // 首页没有 cover 时用它兜底，避免 JSON-LD 的 image 出现空字符串。
        fallBackImage: OG_IMAGE,

        /**
         * 给每页写 canonical。
         *
         * tools/fix-docs-urls.mjs 会把每个 `xxx.html` 再复制一份到 `xxx/index.html`，
         * 于是每篇文档都有两个内容完全相同的 URL（构建产物 107 个 HTML 对应 57 个页面）。
         * 不声明首选地址的话，搜索引擎会把它当成两份重复内容，权重被摊薄。
         *
         * 统一指向目录形式（`/xxx/`）：它既是 GitHub Pages 深链接最自然的形式，
         * 也是 sitemap 之外那份副本能通过 canonical 收敛到的目标。
         * 首页本身就是 `/`、`/zh/`、`/en/`，去掉末尾的 index.html 即可。
         */
        canonical: (page) => `${HOSTNAME}${BASE_URL.replace(/\/$/, '')}${page.path.replace(/index\.html$/, '')}`,

        /**
         * 给全站补分享图。
         *
         * 插件只在页面有 cover、或正文出现图片时才写 og:image，首页两样都没有，
         * 分享到 QQ 群 / Bilibili 时链接展开是一片空白。这里统一套站标图。
         */
        ogp: (ogp, page) => {
          // 首页没有 frontmatter title，插件也就不会产出 og:title——分享卡片会没标题。
          // 用站点名兜底，保证任何页面都有可用的 og:title。
          const fallbackTitle = page.path.startsWith('/en/') ? SITE_TITLE_EN : SITE_TITLE
          const title = ogp['og:title'] || String(page.title || '') || fallbackTitle
          // 先剔除所有 twitter:* 再重写：页面若自带 cover，插件会同时写
          // twitter:image 与 twitter:image:src 两条，留着会重复。
          const content: Record<string, unknown> = {}
          for (const [key, value] of Object.entries(ogp)) {
            if (!key.startsWith('twitter:')) content[key] = value
          }
          return {
            ...content,
            'og:title': title,
            'og:image': OG_IMAGE,
            'og:image:alt': title,
            'twitter:card': 'summary',
            'twitter:title': title,
            'twitter:image': OG_IMAGE,
            'twitter:image:alt': title,
          } as never
        },

        /**
         * 首页的 JSON-LD headline 默认是空字符串（它来自页面标题，而首页没有
         * frontmatter title）。结构化数据里出现空 headline 会让搜索结果拿不到标题，
         * 所以补成站点名；首页本身不是文章，类型也一并改成 WebPage。
         */
        jsonLd: (jsonLD, page) => {
          // 首页的 page.title 是空的（frontmatter 里没有 title），
          // 所以 headline 用站点名兜底，而不是留一个空字符串给搜索引擎。
          const fallbackTitle = page.path.startsWith('/en/') ? SITE_TITLE_EN : SITE_TITLE
          const headline = jsonLD.headline || String(page.title || '') || fallbackTitle
          // 首页的 home 标记不在 page.frontmatter 里（插件读到的是 undefined），
          // 只能靠路径判断：中文首页是 /zh/，英文是 /en/，语言选择页是 /。
          const isHome = ['/', '/zh/', '/en/'].includes(page.path)
          if (isHome) {
            return {
              '@context': 'https://schema.org',
              '@type': 'WebPage',
              name: headline,
              description: String(page.frontmatter.description || ''),
              headline,
              image: [OG_IMAGE],
              author: jsonLD.author ?? [],
            } as never
          }
          return { ...jsonLD, headline } as never
        },
      },
    },
  }),
})
