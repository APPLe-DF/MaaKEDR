import { ThemeCollectionItem, ThemeNavItem } from 'vuepress-theme-plume'

export interface NavigationConfig {
  navbar: ThemeNavItem[]
  collections: ThemeCollectionItem[]
}

const zh: NavigationConfig = {
  navbar: [
    { text: '用户手册', icon: 'mdi:user', link: '/zh/manual/' },
    { text: '开发文档', icon: 'ph:code-bold', link: '/zh/develop/' },
    { text: '协议文档', icon: 'basil:document-solid', link: '/zh/protocol/' },
  ],
  collections: [
    {
      type: 'doc',
      title: '用户手册',
      dir: 'manual',
      sidebar: ['newbie.md', 'faq.md', 'connection.md', 'introduction.md', 'choose-ui.md'],
    },
    {
      type: 'doc',
      title: '开发文档',
      dir: 'develop',
      sidebar: [
        'setup.md',
        'pipeline.md',
        'custom.md',
        'vibe-coding.md',
        'fix.md',
        'formatting.md',
        'structure.md',
        'doc.md',
      ],
    },
    {
      type: 'doc',
      title: '协议文档',
      dir: 'protocol',
      sidebar: [
        'overview.md',
        'startup.md',
        'claim-rewards.md',
        'farm-resources.md',
        'pvp.md',
      ],
    },
  ],
}

const en: NavigationConfig = {
  navbar: [
    { text: 'User Manual', icon: 'mdi:user', link: '/en/manual/' },
    { text: 'Development Docs', icon: 'ph:code-bold', link: '/en/develop/' },
    { text: 'Protocol', icon: 'basil:document-solid', link: '/en/protocol/' },
  ],
  collections: [
    {
      type: 'doc',
      title: 'User Manual',
      dir: 'manual',
      sidebar: ['newbie.md', 'faq.md', 'connection.md', 'introduction.md', 'choose-ui.md'],
    },
    {
      type: 'doc',
      title: 'Development Docs',
      dir: 'develop',
      sidebar: [
        'setup.md',
        'pipeline.md',
        'custom.md',
        'vibe-coding.md',
        'fix.md',
        'formatting.md',
        'structure.md',
        'doc.md',
      ],
    },
    {
      type: 'doc',
      title: 'Protocol',
      dir: 'protocol',
      sidebar: [
        'overview.md',
        'startup.md',
        'claim-rewards.md',
        'farm-resources.md',
        'pvp.md',
      ],
    },
  ],
}

export const navigation: Record<string, NavigationConfig> = { zh, en }
