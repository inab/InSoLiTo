function triggerDownload (href, filename) {
    const link = document.createElement('a')
    link.href = href
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
}

export function downloadDataUri (dataUri, filename) {
    triggerDownload(dataUri, filename)
}

export function downloadGraphAsJson (nodes, edges) {
    const blob = new Blob([JSON.stringify({ nodes, edges }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    triggerDownload(url, 'InSoLiTo-graph.json')
    URL.revokeObjectURL(url)
}
