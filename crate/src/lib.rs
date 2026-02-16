#![deny(clippy::all)]

use napi_derive::napi;
use napi::bindgen_prelude::*;
use napi::Task;

#[global_allocator]
static ALLOC: mimalloc::MiMalloc = mimalloc::MiMalloc;

pub struct AsyncHashTask {
    data: Vec<u8>,
}

#[napi]
impl Task for AsyncHashTask {
    type Output = String;
    type JsValue = String;

    fn compute(&mut self) -> Result<Self::Output> {
        let hash = blake3::hash(&self.data);
        Ok(hash.to_hex().to_string())
    }

    fn resolve(&mut self, _env: Env, output: Self::Output) -> Result<Self::JsValue> {
        Ok(output)
    }
}

#[napi]
pub fn hash_sync(data: Buffer) -> String {
    blake3::hash(&data).to_hex().to_string()
}

#[napi]
pub fn hash_async(data: Buffer) -> AsyncTask<AsyncHashTask> {
    AsyncTask::new(AsyncHashTask {
        data: data.to_vec(),
    })
}

#[napi]
pub struct Blake3Hasher {
    hasher: blake3::Hasher,
}

#[napi]
impl Blake3Hasher {
    #[napi(constructor)]
    pub fn new() -> Self {
        Self {
            hasher: blake3::Hasher::new(),
        }
    }

    #[napi]
    pub fn update(&mut self, data: Buffer) -> &Self {
        self.hasher.update(&data);
        self
    }

    #[napi]
    pub fn digest(&self) -> String {
        self.hasher.finalize().to_hex().to_string()
    }

    #[napi]
    pub fn digest_binary(&self) -> Buffer {
        let hash = self.hasher.finalize();
        Buffer::from(hash.as_bytes().as_slice())
    }

    #[napi]
    pub fn reset(&mut self) {
        self.hasher.reset();
    }
}

#[napi]
pub fn init_logger() {
    println!("Rasmx BLAKE3: Optimized Crypto Engine Initialized (Rayon+SIMD)");
}