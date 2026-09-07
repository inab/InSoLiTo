import CommunityData from '../../../DB/CommunityData.json'

// community id -> its full CommunityData.json record (dominant Topic/Language/OS
// across that community's tools, plus totalNodes — its size). Topic was the only
// field ever read here before the 2026-09 field audit (see CLAUDE.md); Language/OS/
// totalNodes were already bundled in the exact same JSON, just discarded.
export const communityMetaById = Object.fromEntries(
    CommunityData
        .filter((community) => community && community.id !== undefined)
        .map((community) => [community.id, community])
)

// Dominant EDAM topic across that community's tools (see CLAUDE.md, "Data
// Integration Pipeline" — Louvain groups purely by co-citation density, EDAM is
// only used afterwards to label the result). Shared by Legend.vue and SelectionInfoPanel.vue
// so both show the exact same label for a given community.
export const communityTopicById = Object.fromEntries(
    Object.entries(communityMetaById).map(([id, community]) => [id, community.Topic || 'Unknown'])
)
