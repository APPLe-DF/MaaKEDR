import { defineThemeConfig } from 'vuepress-theme-plume'
import { genThemeLocales } from './navigation/genLocales.ts'
import { HOSTNAME } from './config/site.ts'

/**
 * 固定的 Open Graph 分享图。
 *
 * Plume 的 seo 插件只在页面自带 cover、或正文里出现图片时才写 og:image
 * （顺便一提，它也从不写 twitter 卡片）。首页没有 cover，所以分享到
 * QQ 群或 Bilibili 时没有任何预览图。这里统一给全站套一张站标图：
 * 虽然不如专门排版的 1200×630 好看，但至少链接展开时有图可看。
 */
const OG_IMAGE = `${HOSTNAME}/MaaKEDR/images/maakedr-logo_512x512.png`

export default defineThemeConfig({
  logo: '/images/maakedr-logo_512x512.png',

  appearance: true,

  social: [
    { icon: 'qq', link: 'https://qm.qq.com/q/clvWu1RoWI' },
    { icon: 'github', link: 'https://github.com/APPLe-DF/MaaKEDR' },
  ],
  navbarSocialInclude: ['qq', 'github'],

  footer: {
    message: 'AGPL-3.0 License',
    copyright: 'Copyright © 2025 APPLe-DF',
  },

  locales: genThemeLocales(),
})
