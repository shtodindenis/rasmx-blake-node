import { hash, hashAsync, initLogger } from './index.js';
import crypto from 'crypto';

initLogger();

const MEGABYTE = 1024 * 1024;

function formatSpeed(bytes, ms) {
    const seconds = ms / 1000;
    const mb = bytes / MEGABYTE;
    return `${(mb / seconds).toFixed(2)} MB/s`;
}

async function benchmark() {
    console.log('\n🚀 STARTING HIGH-LOAD BENCHMARK (@rasmx/node/blake3)\n');

    // 1. Throughput Benchmark (Large Buffer)
    const BUFFER_SIZE = 100 * MEGABYTE; // 100 MB
    console.log(`[Setup] Generating ${BUFFER_SIZE / MEGABYTE} MB random buffer...`);
    const largeBuffer = crypto.randomBytes(BUFFER_SIZE);
    
    console.log('\n--- Throughput Test (Sync) ---');
    const startSync = performance.now();
    hash(largeBuffer);
    const endSync = performance.now();
    console.log(`✅ Result: ${formatSpeed(BUFFER_SIZE, endSync - startSync)}`);

    console.log('\n--- Throughput Test (Async) ---');
    const startAsync = performance.now();
    await hashAsync(largeBuffer);
    const endAsync = performance.now();
    console.log(`✅ Result: ${formatSpeed(BUFFER_SIZE, endAsync - startAsync)}`);

    // 2. Operations Per Second (Small Inputs)
    const OPS_ITERATIONS = 100000;
    const smallBuffer = Buffer.from("Rasmx fast hash");
    console.log(`\n--- OPS Test (Sync, ${OPS_ITERATIONS} iterations, 32B input) ---`);
    
    const startOps = performance.now();
    for (let i = 0; i < OPS_ITERATIONS; i++) {
        hash(smallBuffer);
    }
    const endOps = performance.now();
    const durationSec = (endOps - startOps) / 1000;
    const ops = Math.floor(OPS_ITERATIONS / durationSec);
    
    console.log(`✅ Result: ${ops.toLocaleString()} ops/sec`);
    console.log(`⏱ Total time: ${(endOps - startOps).toFixed(2)}ms`);

    // 3. String vs Buffer overhead
    console.log('\n--- String Input Comparison ---');
    const strInput = "A".repeat(1024 * 1024); // 1MB String
    const bufInput = Buffer.from(strInput); // 1MB Buffer

    console.time('String Input');
    hash(Buffer.from(strInput)); // Simulate converting in JS
    console.timeEnd('String Input');

    console.time('Buffer Input');
    hash(bufInput);
    console.timeEnd('Buffer Input');

    console.log('\n🏁 Benchmark Complete');
}

benchmark().catch(console.error);