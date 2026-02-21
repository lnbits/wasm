# AssemblyScript example

This example mirrors `module.wat` and the Rust example. It exports:

- `get_increment_amount`
- `increment_counter`

Build:

```bash
cd extensions/wasmexample/wasm/assemblyscript-example
npm install
npm run asbuild
cp build/module.wasm ../module.wasm
```
