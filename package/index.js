import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const binding = require('./index.cjs');

export const hash = binding.hashSync;
export const hashAsync = binding.hashAsync;
export const Blake3Hasher = binding.Blake3Hasher;
export const initLogger = binding.initLogger;

export default {
    hash,
    hashAsync,
    Blake3Hasher,
    initLogger
};