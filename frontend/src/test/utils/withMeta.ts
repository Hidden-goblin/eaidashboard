type TestMeta = {
    testKey?: string;
    repoPath?: string;
    description?: string;
    steps?: string[];    // or richer objects
    tags?: string[];
    [k: string]: any;
}

import { test as baseTest } from 'vitest'

export function testWithMeta(name: string, meta: TestMeta, fn: any) {
    baseTest(name, async (ctx) => {
        // attach metadata to the task so the reporter will receive it
        // (Vitest serializes task.meta to the runner process)
        ctx.task.meta = { ...(ctx.task.meta || {}), ...meta }
        // run the original test fn (pass ctx so user may use it)
        return fn(ctx)
    })
}