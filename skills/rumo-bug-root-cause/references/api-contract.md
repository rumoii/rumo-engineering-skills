# API Contract Investigation

For each suspect request, record method, normalized path, headers, authentication context, query and path parameters, request body, validation, response status, response body, and error mapping.

Map every visible field to its serialized key and backend representation. Trace redirects, reverse proxies, development rewrites, gateways, generated clients, and multipart or streaming behavior when present. Do not assume that a frontend path equals the backend route.

Compare the real request captured from the browser or client with source types, controller inputs, service expectations, persistence fields, and the assembled runtime configuration. Test missing, null, empty, boundary, unknown enum, duplicate, pagination, upload, download, and partial-success behavior when relevant.
