// reporters/custom-json-reporter.ts
import { DefaultReporter } from 'vitest/reporters'
import type { Reporter, TestCase, TestModule } from 'vitest/node'
import { writeFileSync, mkdirSync } from 'fs'
import { dirname } from 'path'

type Options = { output?: string }

export default class CustomJsonReporter extends DefaultReporter implements Reporter {
    results: any[] = []
    options: Options

    constructor(options?: Options) {
        super()
        this.options = options || { output: 'vitest-test-report.json' }
    }

    // called for each finished test
    onTestCaseResult(testCase: TestCase) {
        const meta = (testCase.meta && typeof testCase.meta === 'function')
            ? testCase.meta()
            : {} // defensive

        const result = (testCase.result && typeof testCase.result === 'function')
            ? testCase.result()
            : {}

        this.results.push({
            id: testCase.id,
            name: testCase.name,
            file: testCase.file?.file ?? null,
            suitePath: testCase.suitePath ?? null,
            status: result.state ?? 'unknown',
            duration: result.duration ?? null,
            error: result.errors && result.errors.length ? result.errors.map(e => e.message || String(e)) : [],
            meta,
        })
    }

    // called when all runs finished
    onFinished(testModule: TestModule) {
        const out = this.options.output ?? 'vitest-test-report.json'
        // ensure directory exists
        mkdirSync(dirname(out), { recursive: true })
        writeFileSync(out, JSON.stringify({ finishedAt: new Date().toISOString(), results: this.results }, null, 2))
        // optional: call super so default console output still works
        super.onFinished?.(testModule)
    }
}
