import { http, HttpResponse } from 'msw'
import {logger} from "@/composables/logger";

function parseFormBody(body: string): Record<string, string> {
    const result: Record<string, string> = {}

    body.split('&').forEach((pair) => {
        const [key, value] = pair.split('=')
        if (key) {
            result[decodeURIComponent(key)] = decodeURIComponent(value || '')
        }
    })

    return result
}

export const handlers = [
    http.get('http://mock-api/api/v1/settings/projects', ({request}) => {
        const authHeader = request.headers.get('authorization')
        if (authHeader === 'Bearer valid.token') {
            return HttpResponse.json(['project1', 'project2'], { status: 200 })
        } else if (authHeader === 'Bearer not.allowed.token') {
            return HttpResponse.json({ detail: 'Access denied' }, { status: 403 })
        } else {
            logger.debug("Returning 401")
            return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
        }
    }),
    http.post('http://mock-api/api/v1/token', async ({ request }) => {
        const rawbody = await request.text()
        const body = parseFormBody(rawbody)

        logger.debug('POST /api-old/v1/token', body)
        if (body.username === 'valid@example.com' && body.password === 'password123') {
            return HttpResponse.json({ access_token: 'mocked.jwt.token' })
        } else {
            return HttpResponse.json(
                { detail: 'Invalid credentials' },
                { status: 401 }
            )
        }
    }),
    http.post('http://mock-api/api/v1/projects/demo/versions/v1/tickets/', async ({request}) => {
        const authHeader = request.headers.get('authorization')
        const body = await request.json()
        logger.debug("mock POST http://mock-api/api/v1/projects/demo/versions/v1/tickets/ ", authHeader, body);
        if (authHeader !== 'Bearer valid.token') {
            return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
        } else if (body.reference == 'EXISTING_REF') {
            logger.debug('Return existing ticket');
            return HttpResponse.json({ detail: 'Ticket reference already exits for the project' }, { status: 400 })
        } else if (body.reference == ''|| body.description == '') {
            return HttpResponse.json({ detail: 'Wrong input'}, {status: 422})
        } else {
            return HttpResponse.json({ inserted_id: '12', acknowledged: true, message:''}, {status: 200})
        }
    }),
    http.post('http://mock-api/api/v1/projects/demo/versions', async ({request}) => {
        logger.debug('handler POST /api/v1/projects/demo/versions/')
        const authHeader = request.headers.get('authorization')
        const body = await request.json()
        if (authHeader !== 'Bearer valid.token') {
            return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
        } else if (body.version == "1.1"){
            logger.debug("Success creation")
            return HttpResponse.json({ inserted_id: '12', acknowledged: true, message:'' }, { status: 200 })
        }
        else if (body.version === "v1"){
            return HttpResponse.json({detail: "Existing version"}, {status: 409})
        }
        else {
            logger.debug("Server error");
            return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        }
    }),
    http.get<{versionName: string}>('http://mock-api/api/v1/projects/demo/versions/:versionName', async ({params, request}) => {
        logger.debug(`handler GET /api/v1/projects/demo/versions/${params.versionName}`)
        try {
        const authHeader = request.headers.get('authorization')
            logger.debug("After get authentication header")
        if (authHeader !== 'Bearer valid.token') {
            return HttpResponse.json({detail: 'Unauthorized'}, {status: 401})
        } else if (params.versionName !== "1.1" && params.versionName !== "v1"){
            return HttpResponse.json({ detail: `Could not find ${params.versionName}` }, { status: 404 })
        } else {
            logger.debug('Return default success response')
            return HttpResponse.json({
                "version": "string",
                "created": "2025-08-19T12:52:46.359Z",
                "updated": "2025-08-19T12:52:46.359Z",
                "started": "2025-08-19T12:52:46.359Z",
                "end_forecast": "2025-08-19T12:52:46.360Z",
                "status": "in progress",
                "statistics": {
                    "open": 0,
                    "cancelled": 0,
                    "blocked": 0,
                    "in_progress": 0,
                    "done": 0
                },
                "bugs": {
                    "open_blocking": 0,
                    "open_major": 0,
                    "open_minor": 0,
                    "closed_blocking": 0,
                    "closed_major": 0,
                    "closed_minor": 0
                }
            }, {status: 200})
        }
    } catch (error) {logger.error('handler', error)}})
]