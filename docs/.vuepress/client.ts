import { defineClientConfig } from 'vuepress/client'

import HomeDownload from './components/HomeDownload.vue'
import HomePointerField from './components/HomePointerField.vue'
import HomeStats from './components/HomeStats.vue'
import './styles/palette.css'
import './styles/home-hero.css'

export default defineClientConfig({
  enhance({ app, router }) {
    // Plume 的 home config 会把未知 type 当作全局组件解析，注册后即可作为一个首页块使用。
    app.component('HomeDownload', HomeDownload)
    app.component('HomePointerField', HomePointerField)
    app.component('HomeStats', HomeStats)

    if (router) {
      router.afterEach(() => {
        fixBreadcrumbRDFa()
      })
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('load', fixBreadcrumbRDFa)
    }
  },
})

function fixBreadcrumbRDFa() {
  if (typeof document === 'undefined') return

  const breadcrumbItems = document.querySelectorAll('.vp-breadcrumb li[typeof="ListItem"]')

  breadcrumbItems.forEach((li, index) => {
    const webPageElement = li.querySelector('[typeof="WebPage"]')
    if (webPageElement && !webPageElement.hasAttribute('resource')) {
      const position = index + 1
      let url = 'https://apple-df.github.io/MaaKEDR'

      if (position === 1) {
        url += '/'
      } else {
        const currentPath = window.location.pathname
        const pathSegments = currentPath.split('/').filter(Boolean)
        if (pathSegments.length >= position - 1) {
          url += '/' + pathSegments.slice(0, position - 1).join('/') + '/'
        }
      }

      webPageElement.setAttribute('resource', url)
    }
  })
}
