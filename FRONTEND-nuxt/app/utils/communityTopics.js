import CommunityData from '../../../DB/CommunityData.json'

// community id -> dominant EDAM topic across that community's tools (see CLAUDE.md,
// "Data Integration Pipeline" — Louvain groups purely by co-citation density, EDAM is
// only used afterwards to label the result). Shared by Legend.vue and NodeInfoPanel.vue
// so both show the exact same label for a given community.
export const communityTopicById = Object.fromEntries(
    CommunityData
        .filter((community) => community && community.id !== undefined)
        .map((community) => [community.id, community.Topic || 'Unknown'])
)
