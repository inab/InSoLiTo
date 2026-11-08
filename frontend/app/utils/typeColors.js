// Node fill/border color by type ('Tool' | 'Database' | 'Publication') — the same
// colors Network.vue paints on the canvas in 'type' mode, pulled from the same CSS
// custom properties so a change to main.scss can't silently desync the two.
export function getTypeColor (type) {
    const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()
    const bg = {
        Tool: cssVar('--insolito-node-primary'),
        Database: cssVar('--insolito-node-tertiary'),
        Publication: cssVar('--insolito-node-secondary')
    }
    const border = {
        Tool: cssVar('--insolito-primary'),
        Database: cssVar('--insolito-node-tertiary-dark'),
        Publication: cssVar('--insolito-secondary-hover')
    }
    return { bg: bg[type] || '#999999', border: border[type] || '#666666' }
}
