// Shared shape between the JSON export's metadata and the "Share" link's URL
// param — both are the same underlying payload (searchTerms + filters), just
// carried by a different medium (a downloaded file vs a query string). Importing
// either one replays the same searches through the normal search pipeline
// (Sidebar.vue's restoreFromMetadata -> addSearchTerm + rebuildGraph), rather than
// injecting nodes/edges directly, so the result is a live graph, not a snapshot.

// Bumped only if the {searchTerms, filters} shape itself changes in a way that
// would break re-importing an older file — not on every unrelated app change.
// Not enforced anywhere yet (nothing to be incompatible with at version 1), but
// costs nothing to have on file now instead of retrofitting it once it's needed.
const STATE_VERSION = 1

export function buildStateMetadata ({ searchTerms, filters, layers }) {
    return {
        version: STATE_VERSION,
        searchTerms,
        filters,
        layers,
        exportedAt: new Date().toISOString()
    }
}

const VALID_KINDS = ['Tool', 'Database', 'Topic']
const VALID_NODE_TYPES = ['Tool', 'Database', 'Publication']

function isValidSearchTerms (value) {
    return Array.isArray(value) && value.length > 0 &&
        value.every((term) => term && typeof term.name === 'string' && VALID_KINDS.includes(term.kind))
}

function isValidFilters (value) {
    return value && typeof value === 'object' &&
        (value.yearMin === null || typeof value.yearMin === 'number') &&
        (value.yearMax === null || typeof value.yearMax === 'number') &&
        typeof value.occurrenceMin === 'number'
}

// Legend/Filters visibility (uiStore's hiddenTypes/hiddenCommunities/hiddenToolTypes)
// — added after v1's initial searchTerms+filters shape, so `undefined` (a file
// saved before this field existed, or a share link built from one) is valid too,
// not just a well-formed object; normalizeLayers below is what actually fills in
// the "nothing hidden" default for that case.
function isValidLayers (value) {
    if (value === undefined) return true
    return value && typeof value === 'object' &&
        Array.isArray(value.hiddenTypes) && value.hiddenTypes.every((type) => VALID_NODE_TYPES.includes(type)) &&
        Array.isArray(value.hiddenCommunities) && value.hiddenCommunities.every((id) => typeof id === 'number') &&
        Array.isArray(value.hiddenToolTypes) && value.hiddenToolTypes.every((type) => typeof type === 'string')
}

function normalizeLayers (value) {
    return {
        hiddenTypes: value?.hiddenTypes ?? [],
        hiddenCommunities: value?.hiddenCommunities ?? [],
        hiddenToolTypes: value?.hiddenToolTypes ?? []
    }
}

// Used by both JSON import and the share link — same validation either way, since
// a malformed share link (hand-edited URL) is no different a risk than a malformed
// uploaded file. Returns { data, error }: error is a specific, human-readable
// reason (missing field vs wrong shape) instead of one generic "doesn't look
// right" message — the share-link path (parseShareState below) only needs data,
// so it discards error and treats any failure as "not a share link" the same way.
export function parseStateMetadata (raw) {
    if (!raw || typeof raw !== 'object') {
        return { data: null, error: "The file doesn't contain any graph data." }
    }
    if (!isValidSearchTerms(raw.searchTerms)) {
        return { data: null, error: 'The file has no valid search terms (missing, empty, or wrong format).' }
    }
    if (!isValidFilters(raw.filters)) {
        return { data: null, error: 'The file is missing valid filter settings (year range, minimum co-citations).' }
    }
    if (!isValidLayers(raw.layers)) {
        return { data: null, error: 'The file has invalid layer visibility settings.' }
    }
    return { data: { searchTerms: raw.searchTerms, filters: raw.filters, layers: normalizeLayers(raw.layers) }, error: null }
}

const SHARE_PARAM = 'state'

export function buildShareUrl ({ searchTerms, filters, layers }) {
    const encoded = btoa(encodeURIComponent(JSON.stringify({ searchTerms, filters, layers })))
    const url = new URL(window.location.href)
    url.search = ''
    url.searchParams.set(SHARE_PARAM, encoded)
    return url.toString()
}

// Reads location.search directly (not passed in) — the one caller is app.vue on
// initial load, before there's any Vue Router state to read it from instead.
export function parseShareState () {
    const encoded = new URLSearchParams(window.location.search).get(SHARE_PARAM)
    if (!encoded) return null
    try {
        return parseStateMetadata(JSON.parse(decodeURIComponent(atob(encoded)))).data
    } catch {
        return null
    }
}
