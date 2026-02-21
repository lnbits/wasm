#![no_std]

extern "C" {
    fn db_get(key_ptr: *const u8, key_len: i32, out_ptr: *mut u8, out_len: i32) -> i32;
    fn db_set(key_ptr: *const u8, key_len: i32, val_ptr: *const u8, val_len: i32) -> i32;
}

const KEY_COUNTER: &[u8] = b"counter";
const KEY_INCREMENT_AMOUNT: &[u8] = b"increment_amount";
const DEFAULT_INCREMENT_AMOUNT: i32 = 10;

#[no_mangle]
pub extern "C" fn get_increment_amount() -> i32 {
    let raw = db_get_string(KEY_INCREMENT_AMOUNT);
    let amount = raw.as_ref().map(parse_i32).unwrap_or(0);
    if amount > 0 {
        amount
    } else {
        DEFAULT_INCREMENT_AMOUNT
    }
}

#[no_mangle]
pub extern "C" fn increment_counter() -> i32 {
    let current = db_get_string(KEY_COUNTER)
        .as_ref()
        .map(parse_i32)
        .unwrap_or(0);
    let value = current + 1;
    db_set_string(KEY_COUNTER, value);
    value
}

fn db_get_string(key: &[u8]) -> Option<[u8; 32]> {
    let mut buf = [0u8; 32];
    let read_len = unsafe {
        db_get(
            key.as_ptr(),
            key.len() as i32,
            buf.as_mut_ptr(),
            buf.len() as i32,
        )
    };
    if read_len <= 0 {
        None
    } else {
        Some(buf)
    }
}

fn db_set_string(key: &[u8], value: i32) {
    let mut out = [0u8; 32];
    let out_len = write_i32(value, &mut out);
    unsafe {
        db_set(
            key.as_ptr(),
            key.len() as i32,
            out.as_ptr(),
            out_len as i32,
        );
    }
}

fn parse_i32(bytes: &[u8]) -> i32 {
    let mut n: i32 = 0;
    for &b in bytes {
        if b < b'0' || b > b'9' {
            break;
        }
        n = n * 10 + (b - b'0') as i32;
    }
    n
}

fn write_i32(mut n: i32, out: &mut [u8]) -> usize {
    if n == 0 {
        out[0] = b'0';
        return 1;
    }

    let mut tmp = [0u8; 32];
    let mut len = 0;
    while n > 0 {
        tmp[len] = b'0' + (n % 10) as u8;
        n /= 10;
        len += 1;
    }

    for i in 0..len {
        out[i] = tmp[len - 1 - i];
    }

    len
}
