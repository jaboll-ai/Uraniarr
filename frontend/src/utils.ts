export function getInitials(name: string) {
  const names = name.split(' ')
  let initials = ''
  for (let i = 0; i < names.length; i++) {
    initials += names[i].charAt(0).toLocaleUpperCase()
  }
  return initials
}