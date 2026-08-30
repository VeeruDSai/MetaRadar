'use client'

import { useEffect, useRef } from 'react'

const REVEAL_SELECTOR = '[data-scroll-reveal="signal"]'

/** Applies the scale/opacity reveal to present and subsequently streamed UI elements. */
export function ScrollReveal() {
  const scrollDirection = useRef<'up' | 'down' | 'idle'>('idle')

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    let lastScrollY = window.scrollY
    const handleScroll = () => {
      const currentScrollY = window.scrollY
      scrollDirection.current = currentScrollY > lastScrollY ? 'down' : currentScrollY < lastScrollY ? 'up' : 'idle'
      lastScrollY = currentScrollY
    }
    window.addEventListener('scroll', handleScroll, { passive: true })

    const observe = (element: Element) => {
      if (!(element instanceof HTMLElement) || element.dataset.scrollObserved === 'true') return
      element.dataset.scrollObserved = 'true'
      element.classList.add('scroll-reveal')
      observer.observe(element)
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return

          if (scrollDirection.current === 'up') {
            // Never hide content while moving upward; reveal unseen cards instantly.
            entry.target.classList.add('scroll-reveal-no-animation', 'scroll-reveal-visible')
          } else {
            entry.target.classList.remove('scroll-reveal-no-animation')
            entry.target.classList.add('scroll-reveal-visible')
          }
        })
      },
      { threshold: 0.02, rootMargin: '0px 0px 60px 0px' },
    )

    document.querySelectorAll(REVEAL_SELECTOR).forEach(observe)
    const mutationObserver = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (!(node instanceof Element)) return
          if (node.matches(REVEAL_SELECTOR)) observe(node)
          node.querySelectorAll(REVEAL_SELECTOR).forEach(observe)
        })
      })
    })
    mutationObserver.observe(document.body, { childList: true, subtree: true })

    return () => {
      mutationObserver.disconnect()
      observer.disconnect()
      window.removeEventListener('scroll', handleScroll)
    }
  }, [])

  return null
}
