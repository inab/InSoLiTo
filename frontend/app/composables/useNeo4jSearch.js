import { buildSearchQuery } from '../utils/cypherQueries'
import { parseNeo4jGraph } from '../utils/parseNeo4jGraph'
import { postCypher } from '../utils/neo4jClient'

export function useNeo4jSearch () {
    const loading = ref(false)
    const error = ref('')

    async function search ({ name, kind, occurrenceMin, yearMin, yearMax }) {
        loading.value = true
        error.value = ''
        try {
            const { statement, parameters } = buildSearchQuery({ name, kind, occurrenceMin, yearMin, yearMax })
            const response = await postCypher(statement, parameters, ['graph'])
            const { nodes, edges } = parseNeo4jGraph(response)
            // Topic searches match a whole set of tools via the EDAM hierarchy, not one
            // specific node — there's no single "entry point" to highlight for those.
            const entryPointId = kind === 'Topic' ? null : nodes.find((node) => node.properties?.name === name)?.id ?? null
            return { nodes, edges, entryPointId }
        } catch (e) {
            error.value = e.message || 'Search failed'
            throw e
        } finally {
            loading.value = false
        }
    }

    return { search, loading, error }
}
