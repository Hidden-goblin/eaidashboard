import { http, HttpResponse } from 'msw'

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
        console.log('GET /api/v1/settings/projects')
        console.log(request.headers.get('authorization'))
        const authHeader = request.headers.get('authorization')
        if (authHeader === 'Bearer valid.token') {
            return HttpResponse.json(['project1', 'project2'], { status: 200 })
        } else if (authHeader === 'Bearer bad.token') {
            return HttpResponse.json({ detail: 'Access denied' }, { status: 403 })
        } else {
            return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
        }
    }),
    http.post('http://mock-api/api/v1/token', async ({ request }) => {
        console.log('POST /api/v1/token - Mocked Handler')
        const rawbody = await request.text()
        console.log('body:', rawbody)
        const body = parseFormBody(rawbody)

        console.log('POST /api/v1/token', body)
        if (body.username === 'valid@example.com' && body.password === 'password123') {
            return HttpResponse.json({ access_token: 'mocked.jwt.token' })
        } else {
            return HttpResponse.json(
                { detail: 'Invalid credentials' },
                { status: 401 }
            )
        }
    }),
]