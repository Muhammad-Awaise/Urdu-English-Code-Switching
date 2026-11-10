export function labelClass(label: string) {
  switch (label) {
    case 'URDU_ROMAN':
      return 'badge-urdu'
    case 'ENGLISH':
      return 'badge-english'
    case 'AMBIGUOUS':
      return 'badge-ambiguous'
    case 'UNKNOWN':
      return 'badge-unknown'
    default:
      return 'badge-other'
  }
}
