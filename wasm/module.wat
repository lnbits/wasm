(module
  (import "host" "db_get" (func $db_get (param i32 i32 i32 i32) (result i32)))
  (import "host" "db_set" (func $db_set (param i32 i32 i32 i32) (result i32)))

  (memory (export "memory") 1)
  (global $heap (mut i32) (i32.const 1024))
  (data (i32.const 0) "counter")
  (data (i32.const 16) "increment_amount")

  (func $alloc (param $size i32) (result i32)
    (local $old i32)
    global.get $heap
    local.set $old
    global.get $heap
    local.get $size
    i32.add
    global.set $heap
    local.get $old)

  (func $atoi (param $ptr i32) (param $len i32) (result i32)
    (local $i i32)
    (local $acc i32)
    (local $ch i32)
    (local.set $i (i32.const 0))
    (local.set $acc (i32.const 0))
    (block $done
      (loop $loop
        local.get $i
        local.get $len
        i32.ge_u
        br_if $done
        local.get $ptr
        local.get $i
        i32.add
        i32.load8_u
        local.set $ch
        local.get $ch
        i32.const 48
        i32.sub
        local.set $ch
        local.get $acc
        i32.const 10
        i32.mul
        local.get $ch
        i32.add
        local.set $acc
        local.get $i
        i32.const 1
        i32.add
        local.set $i
        br $loop)))
    local.get $acc)

  (func $itoa (param $value i32) (param $buf i32) (param $buflen i32) (result i32)
    (local $i i32)
    (local $v i32)
    (local $tmp i32)
    (local $start i32)
    (local $end i32)
    local.get $value
    i32.eqz
    if
      local.get $buf
      i32.const 48
      i32.store8
      i32.const 1
      return
    end
    local.get $value
    local.set $v
    i32.const 0
    local.set $i
    (block $done
      (loop $loop
        local.get $v
        i32.eqz
        br_if $done
        local.get $v
        i32.const 10
        i32.rem_u
        i32.const 48
        i32.add
        local.set $tmp
        local.get $buf
        local.get $i
        i32.add
        local.get $tmp
        i32.store8
        local.get $v
        i32.const 10
        i32.div_u
        local.set $v
        local.get $i
        i32.const 1
        i32.add
        local.set $i
        br $loop)))
    i32.const 0
    local.set $start
    local.get $i
    i32.const 1
    i32.sub
    local.set $end
    (block $rev_done
      (loop $rev
        local.get $start
        local.get $end
        i32.ge_u
        br_if $rev_done
        local.get $buf
        local.get $start
        i32.add
        i32.load8_u
        local.set $tmp
        local.get $buf
        local.get $start
        i32.add
        local.get $buf
        local.get $end
        i32.add
        i32.load8_u
        i32.store8
        local.get $buf
        local.get $end
        i32.add
        local.get $tmp
        i32.store8
        local.get $start
        i32.const 1
        i32.add
        local.set $start
        local.get $end
        i32.const 1
        i32.sub
        local.set $end
        br $rev)))
    local.get $i)

  (func $increment_counter (result i32)
    (local $buf i32)
    (local $len i32)
    (local $val i32)
    i32.const 64
    local.set $buf
    i32.const 32
    local.set $len
    i32.const 0
    i32.const 7
    local.get $buf
    local.get $len
    call $db_get
    local.set $len
    local.get $len
    i32.eqz
    if
      i32.const 0
      local.set $val
    else
      local.get $buf
      local.get $len
      call $atoi
      local.set $val
    end
    local.get $val
    i32.const 1
    i32.add
    local.set $val
    local.get $val
    local.get $buf
    i32.const 32
    call $itoa
    local.set $len
    i32.const 0
    i32.const 7
    local.get $buf
    local.get $len
    call $db_set
    drop
    local.get $val)

  (func $get_increment_amount (result i32)
    (local $buf i32)
    (local $len i32)
    (local $val i32)
    i32.const 64
    local.set $buf
    i32.const 32
    local.set $len
    i32.const 16
    i32.const 16
    local.get $buf
    local.get $len
    call $db_get
    local.set $len
    local.get $len
    i32.eqz
    if
      i32.const 10
      local.set $val
    else
      local.get $buf
      local.get $len
      call $atoi
      local.set $val
    end
    local.get $val)

  (export "increment_counter" (func $increment_counter))
  (export "get_increment_amount" (func $get_increment_amount))
)
