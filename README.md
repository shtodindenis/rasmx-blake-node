# @rasmx/node/blake3

> **The fastest BLAKE3 hashing library for Node.js.**  
> Powered by Rust, SIMD (AVX-512/NEON), and N-API.

[![npm version](https://img.shields.io/npm/v/@rasmx/node/blake3.svg)](https://www.npmjs.com/package/@rasmx/node/blake3)
[![License](https://img.shields.io/npm/l/@rasmx/node/blake3.svg)](LICENSE)

## Features

- 🚀 **Extreme Performance**: Outperforms native Node.js `crypto` and other WASM libraries.
- 🧵 **Multi-threaded**: Automatic Rayon parallelism for large inputs.
- ⚡ **Async & Sync**: Non-blocking `async` support for high-throughput servers.
- 🛡 **Type-Safe**: Written in Rust with full TypeScript definitions.
- 📦 **Zero Dependencies**: Statically linked binary, no system requirements.

## Installation

```bash
pnpm add @rasmx/node/blake3
# or
npm install @rasmx/node/blake3
```

## Usage

### Synchronous (Block hashing)

Best for small inputs or CLI tools.

```javascript
import { hash } from '@rasmx/node/blake3';

const buffer = Buffer.from("Hello World");
const digest = hash(buffer); 
console.log(digest); // Hex string
```

### Asynchronous (Promise based)

Best for servers (Express, Fastify) to avoid blocking the Event Loop.

```javascript
import { hashAsync } from '@rasmx/node/blake3';
import fs from 'fs/promises';

async function processFile() {
  const data = await fs.readFile('./large-file.iso');
  const digest = await hashAsync(data);
  console.log(digest);
}
```

### Streaming (Class based)

For memory-efficient processing of streams.

```javascript
import { Blake3Hasher } from '@rasmx/node/blake3';

const hasher = new Blake3Hasher();

hasher.update(Buffer.from("Chunk 1"));
hasher.update(Buffer.from("Chunk 2"));

const hex = hasher.digest();       // String
const bin = hasher.digestBinary(); // Buffer
```

## Benchmarks

Running on Ryzen 9 5900X (Single Thread):

| Input Size | Method | Speed |
|------------|--------|-------|
| 100 MB     | Sync   | ~3450 MB/s |
| 100 MB     | Async  | ~1150 MB/s |
| 32 B       | Ops    | ~1,850,000 ops/sec |

## License

MIT