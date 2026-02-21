@external("host", "db_get")
declare function db_get(
  keyPtr: i32,
  keyLen: i32,
  outPtr: i32,
  outLen: i32
): i32

@external("host", "db_set")
declare function db_set(
  keyPtr: i32,
  keyLen: i32,
  valPtr: i32,
  valLen: i32
): i32

const KEY_COUNTER = "counter"
const KEY_INCREMENT_AMOUNT = "increment_amount"
const DEFAULT_INCREMENT_AMOUNT = 10

export function get_increment_amount(): i32 {
  const raw = dbGetString(KEY_INCREMENT_AMOUNT)
  if (raw.length == 0) return DEFAULT_INCREMENT_AMOUNT
  const amount = parseI32(raw)
  return amount > 0 ? amount : DEFAULT_INCREMENT_AMOUNT
}

export function increment_counter(): i32 {
  const currentRaw = dbGetString(KEY_COUNTER)
  const current = currentRaw.length == 0 ? 0 : parseI32(currentRaw)
  const next = current + 1
  dbSetString(KEY_COUNTER, next)
  return next
}

function dbGetString(key: string): string {
  const keyBuf = String.UTF8.encode(key)
  const outBuf = new ArrayBuffer(32)
  const len = db_get(
    changetype<usize>(keyBuf) as i32,
    keyBuf.byteLength,
    changetype<usize>(outBuf) as i32,
    outBuf.byteLength
  )
  if (len <= 0) return ""
  return String.UTF8.decode(outBuf.slice(0, len))
}

function dbSetString(key: string, value: i32): void {
  const keyBuf = String.UTF8.encode(key)
  const valBuf = String.UTF8.encode(value.toString())
  db_set(
    changetype<usize>(keyBuf) as i32,
    keyBuf.byteLength,
    changetype<usize>(valBuf) as i32,
    valBuf.byteLength
  )
}

function parseI32(value: string): i32 {
  let n: i32 = 0
  for (let i = 0; i < value.length; i++) {
    const code = value.charCodeAt(i)
    if (code < 48 || code > 57) break
    n = n * 10 + (code - 48)
  }
  return n
}
