import {http, HttpResponse} from "msw";
import { logger} from "@/composables/logger.ts"

const API_BASE = "http://mock-api";

export const updateVersionHandlers = [
        // GET version data
        http.get<{ projectName: string, versionId: string}>(`http://mock-api/api/v1/projects/:projectName/versions/:versionId`, async ({params, request}) => {
            const authHeader = request.headers.get('authorization')
            if (authHeader == 'Bearer not.allowed.token') {
                return HttpResponse.json({detail: 'Access denied'}, {status: 403})
            } else if (authHeader === 'Bearer invalid.token') {
                return HttpResponse.json({detail: 'Unauthorized'}, {status: 401})
            } else if (params.versionId === '00') {
                return HttpResponse.json({detail: 'Version not found'}, {status: 404})
            } else if (params.versionId === "v2") {
                return HttpResponse.json({
                    status: "Incorrect",
                    started: "2024-01-01T00:00:00Z",
                    end_forecast: "2024-02-01T00:00:00Z"
                });
            } else {
                return HttpResponse.json({
                    status: "Planned",
                    started: "2024-01-01T00:00:00Z",
                    end_forecast: "2024-02-01T00:00:00Z"
                });
            }
        }),

        // GET possible statuses
        http.get<{ projectName: string, status: string}>(`http://mock-api/api/v1/settings/projects/:projectName/workflow/:status`, async ({params, request}) => {
            logger.debug("In handler get status", params.projectName, params.status);
            const authHeader = request.headers.get('authorization')
            if (params.status === "Incorrect"){
                return HttpResponse.json({detail: 'No starting status'}, {status: 404})
            } else {
            return HttpResponse.json({
                data: ["In Progress", "Done"]
            });
        }}),

        // PUT update version
        http.put<{ projectName: string, versionId: string}>(`http://mock-api/api/v1/projects/:projectName/versions/:versionId`, async ({request}) => {
            const authHeader = request.headers.get('authorization')
            const body = await request.json();
            if (body.status === "Invalid") {
                return HttpResponse.json({detail: "Invalid status"}, {status: 400});
            }
            return HttpResponse.json({ok: true});
        })
    ]