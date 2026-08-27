import neo4jConfig from '../config.json'

// Shared POST to Neo4j's HTTP transactional endpoint. Fixes a bug carried over from
// the webpack app: `(user + ':' + pass).toString('base64')` is a no-op on String (that
// method only exists on Node's Buffer), so the old Authorization header was sent
// unencoded — harmless only because production Neo4j runs with NEO4J_AUTH=none.
// btoa() here produces real HTTP Basic auth.
export async function postCypher (statement, parameters, resultDataContents) {
    const response = await $fetch(neo4jConfig.serverUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json;charset=UTF-8',
            'Access-Mode': 'READ',
            Authorization: `Basic ${btoa(`${neo4jConfig.serverUser}:${neo4jConfig.serverPassword}`)}`
        },
        body: {
            statements: [{ statement, parameters, resultDataContents }]
        }
    })
    if (response.errors?.length) {
        // Tagged so callers can tell "Neo4j ran the query and reported a problem"
        // apart from a network/server failure (no response body to read at all).
        const dbError = new Error(response.errors[0].message)
        dbError.cause = 'database'
        throw dbError
    }
    return response
}
