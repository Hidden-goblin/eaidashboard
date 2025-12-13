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

]