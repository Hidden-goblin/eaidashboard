// src/utils/logger.js
const levels = ['debug', 'info', 'warn', 'error']
const maxLevelPerBuildTpe = {'development': 'debug', 'production': 'warn'};

const buildType = import.meta.env.RUN_TYPE || 'production'
console.warn('Running build type', buildType)
const levelIndex = levels.indexOf(maxLevelPerBuildTpe[buildType])

function shouldLog(level) {
    return levels.indexOf(level) >= levelIndex
}

export const logger = {
    debug(...args) {
        if (shouldLog('debug')) console.debug(...args)
    },
    info(...args) {
        if (shouldLog('info')) console.info(...args)
    },
    warn(...args) {
        if (shouldLog('warn')) console.warn(...args)
    },
    error(...args) {
        if (shouldLog('error')) console.error(...args)
    }
}
