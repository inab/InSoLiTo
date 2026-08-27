import { buildEdgeYearBreakdownQuery } from '../utils/cypherQueries'
import { postCypher } from '../utils/neo4jClient'

export function useEdgeYearBreakdown () {
    const loading = ref(false)
    const error = ref('')

    async function fetchBreakdown ({ sourceId, targetId }) {
        loading.value = true
        error.value = ''
        try {
            const { statement, parameters } = buildEdgeYearBreakdownQuery({ sourceId, targetId })
            const response = await postCypher(statement, parameters, ['row'])
            return response.results[0].data.map((row) => ({ year: row.row[0], times: row.row[1] }))
        } catch (e) {
            error.value = e.message || 'Failed to load year breakdown'
            throw e
        } finally {
            loading.value = false
        }
    }

    return { fetchBreakdown, loading, error }
}
