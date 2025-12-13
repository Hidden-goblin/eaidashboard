import { http, HttpResponse } from "msw";
import { logger} from "@/composables/logger";
import type {components} from "@/api/openapi";

const API_BASE = "http://mock-api";

type RegisterVersion = components['schemas']['RegisterVersion'];

export const versionHandler = [
    http.post<{}, RegisterVersion, {}>(`${API_BASE}/api/v1/projects/demo/versions`, async ({request}) => {
        logger.debug('handler POST /api/v1/projects/demo/versions/')
        const body: RegisterVersion =  await request.json();
         if (body?.version == "1.1"){
            logger.debug("Success creation")
            return HttpResponse.json({ inserted_id: '12', acknowledged: true, message:'' }, { status: 200 })
        }
        else if (body?.version === "v1"){
            return HttpResponse.json({detail: "Existing version"}, {status: 409})
        }
        else {
            logger.debug("Server error");
            return HttpResponse.json({ detail: 'Server error' }, { status: 500 })
        }
    }),
    http.get<{versionName: string}>(`${API_BASE}/api/v1/projects/demo/versions/:versionName`, async ({params, request}) => {
        logger.debug(`handler GET /api/v1/projects/demo/versions/${params.versionName}`)
        try {
            if (params.versionName !== "1.1" && params.versionName !== "v1"){
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