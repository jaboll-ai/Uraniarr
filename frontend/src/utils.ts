import { ref } from "vue"
import { notify } from "@kyvg/vue3-notification";

export function getInitials(name: string) {
  const names = name.split(' ')
  let initials = ''
  for (let i = 0; i < names.length; i++) {
    initials += names[i].charAt(0).toLocaleUpperCase()
  }
  return initials
}

export function formatSize(size: string | number) {
  const num = Number(size)
  if (isNaN(num)) return size
  if (num < 1024) return `${num} B`
  if (num < 1024 ** 2) return `${(num / 1024).toFixed(1)} KB`
  if (num < 1024 ** 3) return `${(num / 1024 ** 2).toFixed(1)} MB`
  return `${(num / 1024 ** 3).toFixed(1)} GB`
}

export function diffDisplay(oldPath: string, newPath: string): string {
    if (oldPath === newPath)
        return `<div class="diffLine"><span class="noop">${escapeHtml(oldPath)}</span> <span class="same">(no changes)</span></div>`

    let start = 0, endOld = oldPath.length, endNew = newPath.length

    while (start < endOld && start < endNew && oldPath[start] === newPath[start]) start++
    while (endOld > start && endNew > start && oldPath[endOld - 1] === newPath[endNew - 1]) { endOld--; endNew-- }

    const esc = escapeHtml
    const prefix = esc(oldPath.slice(0, start))
    const suffix = esc(oldPath.slice(endOld))
    const removed = esc(oldPath.slice(start, endOld))
    const added = esc(newPath.slice(start, endNew))

    return `
    <div class="diffLine">${prefix}<span class="removedDiff">${removed}</span>${suffix}</div>
    <div class="diffLine">${prefix}<span class="addedDiff">${added}</span>${suffix}</div>
  `
}

function escapeHtml(s: string) {
    return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]!))
}

export const loadingBooks = ref<{ [bookKey: string]: { [action: string]: string } }>({})

export async function runBatch(keys: string[], requestFn:(key: string) => Promise<any>, field: string, timeoutMs: number) {
  const promises = []
  for (const key of keys) {
    loadingBooks.value[key] = { ...loadingBooks.value[key], [field]: 'loading' }
    const p = requestFn(key)
      .then(res => ({ ...res, _bookKey: key }))
      .catch(err => { err._bookKey = key; throw err })
    promises.push(p)
  }

  const resets = []
  for (const r of await Promise.allSettled(promises)) {
    var key = null
    if (r.status === 'fulfilled') {
      key = r.value._bookKey
      loadingBooks.value[key] = { ...loadingBooks.value[key], [field]: 'check' }
    } else {
      key = r.reason._bookKey
      loadingBooks.value[key] = { ...loadingBooks.value[key], [field]: 'error' }
      try {
        notify({
          title: 'Error',
          text: r.reason.response.data.detail,
          type: 'error'
        })
      } catch {}
    }
    resets.push((async () => {
      await new Promise(res => setTimeout(res, timeoutMs))
      loadingBooks.value[key] = { ...loadingBooks.value[key], [field]: field }
    })())
  }
  Promise.all(resets)
}