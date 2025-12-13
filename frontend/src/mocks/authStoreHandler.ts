import {http, HttpResponse} from "msw";
import {logger} from "@/composables/logger"

import jwt from 'jsonwebtoken';

const JWT_SECRET = 'your_jwt_secret';



const API_BASE = "http://mock-api";

export const authStoreHandler = [
    http.post(API_BASE + '/api/v1/token', async({request}) => {
        const info = await request.formData();
        logger.debug(info);
        if (info.get('username') == "john@jon.son") {
            logger.debug("Create token for john@jon.son");
            const tempToken = jwt.sign({
                username: 'john',
                scopes: {
                    '*': 'admin',
                    project42: 'admin',
                    project1: 'user'
                }
            }, JWT_SECRET, { expiresIn: '1h' });

            return HttpResponse.json({access_token: tempToken, token_type: "Bearer"}, {status: 200})
        }
        else if (info.get('username') == "user@jon.son"){
            logger.debug("Create token for user@jon.son");
            const tempToken = jwt.sign({
                username: 'user',
                scopes:{
                    '*': 'user',
                    project42: 'user',
                    project1: 'admin'
                }
            }, JWT_SECRET, { expiresIn: '1h' });
            return HttpResponse.json({access_token:tempToken, token_type: "Bearer"}, {status: 200})
        }
        else if (info.get('username') == "noscope@jon.son"){
            logger.debug("Create token for noscope@jon.son");
            const tempToken = jwt.sign({
                username: 'user',
                scopes:{
                    '*': 'user',
                }
            }, JWT_SECRET, { expiresIn: '1h' });
            return HttpResponse.json({access_token:tempToken, token_type: "Bearer"}, {status: 200})
        }
        else if (info.get('username') == "badjwt@jon.son"){
            return HttpResponse.json({access_token: 'badToken', token_type:'Bearer'}, {status: 200})
        }
    }),
    http.get(API_BASE + '/api/v1/settings/projects', () => {
        logger.debug('return projects')
        return HttpResponse.json(['project42', 'project1', 'project10'])
    })
]