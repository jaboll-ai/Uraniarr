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