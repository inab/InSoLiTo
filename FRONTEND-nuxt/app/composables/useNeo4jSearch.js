import neo4jConfig from '../config.json'
import { buildSearchQuery } from '../utils/cypherQueries'
import { parseNeo4jGraph } from '../utils/parseNeo4jGraph'

// POSTs a Cypher query to Neo4j's HTTP transactional endpoint. Fixes a bug carried
// over from the webpack app: `(user + ':' + pass).toString('base64')` is a no-op on
// String (that method only exists on Node's Buffer), so the old Authorization header
// was sent unencoded — harmless only because production Neo4j runs with
// NEO4J_AUTH=none. btoa() here produces real HTTP Basic auth.
export function useNeo4jSearch () {
    const loading = ref(false)
    const error = ref('')

    async function search ({ name, kind, occurrenceMin, yearMin, yearMax }) {
        loading.value = true
        error.value = ''
        try {
            const { statement, parameters } = buildSearchQuery({ name, kind, occurrenceMin, yearMin, yearMax })
            const response = await $fetch(neo4jConfig.serverUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json;charset=UTF-8',
                    'Access-Mode': 'READ',
                    Authorization: `Basic ${btoa(`${neo4jConfig.serverUser}:${neo4jConfig.serverPassword}`)}`
                },
                body: {
                    statements: [{ statement, parameters, resultDataContents: ['graph'] }]
                }
            })
            if (response.errors?.length) {
                // Tagged so callers can tell "Neo4j ran the query and reported a problem"
                // apart from a network/server failure (no response body to read at all).
                const dbError = new Error(response.errors[0].message)
                dbError.cause = 'database'
                throw dbError
            }
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
