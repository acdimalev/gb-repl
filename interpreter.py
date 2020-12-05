#!/usr/bin/env python3


from machine import r8, r16, flag, mem8, mem16, mem32


def tokenize(s):
    S = s.upper()

    x = None

    if '-' == S[0]:
        sign = -1
        n = S[1:]
    else:
        sign = 1
        n = S

    if all(c in "0123456789" for c in n):
        x = sign * int(n)

    if '%' == n[0] and all(c in "01" for c in n[1:]):
        x = sign * int(n[1:], 2)

    if '$' == n[0] and all(c in "0123456789ABCDEF" for c in n[1:]):
        x = sign * int(n[1:], 16)

    if x is not None:
        if 0o0 <= x <= 0o7:
            return (['u3', 'e8', 'n8', 'n16'], x)
        if -0x80 <= x <= 0x7f:
            return (['e8', 'n8', 'n16'], x)
        if -0x80 <= x <= 0xff:
            return (['n8', 'n16'], x)
        if -0x8000 <= x <= 0xffff:
            return (['n16'], x)

    if 'A' == S:
        return (['A', 'r8'], S)

    if 'C' == S:
        return (['r8', 'cc'], S)

    if S in ['B', 'D', 'E', 'H', 'L']:
        return (['r8'], S)

    if 'HL' == S:
        return (['HL', 'r16'], 'HL')

    if S in ['BC', 'DE', 'HL']:
        return (['r16'], S)

    if S in ['SP', '[HL]', '[HLI]', '[HLD]']:
        return (S,)

    return ('unknown', s)


def _chunks(n, xs):
    for i in range(0, len(xs), n):
        yield xs[i:i+n]


def _flags(z=0, n=0, h=0, c=0):
    return z << 7 | n << 6 | h << 5 | c << 4


def _zero(f):
    return bool(f & 0x80)


def _carry(f):
    return bool(f & 0x10)


def _add(a, x):
    tmp = a + x
    return (tmp & 0xff, _flags(
        z=not bool(tmp & 0xff),
        h=bool((a ^ x ^ tmp) & 0x10),
        c=bool(tmp & 0x100),
    ))


def _add16(hl, x, f):
    tmp = hl + x
    return (tmp & 0xffff, _flags(
        z=_zero(f),
        h=bool((hl ^ x ^ tmp) & 0x1000),
        c=bool(tmp & 0x10000),
    ))


def _adc(a, x, f):
    return _add(a, x + _carry(f))


def _dec8(x, f):
    tmp = x - 1
    return (tmp & 0xff, _flags(
        z=not bool(tmp & 0xff),
        n=True,
        h=not bool(x & 0xf),
        c=_carry(f),
    ))


def _dec16(x):
    return (x - 1) & 0xffff


def _inc8(x, f):
    tmp = x + 1
    return (tmp & 0xff, _flags(
        z=not bool(tmp & 0xff),
        h=bool(x ^ tmp & 0x10),
        c=_carry(f),
    ))


def _inc16(x):
    return (x + 1) & 0xffff


def _rrca(a):
    c = 1 & a
    return (a >> 1 | c << 7, _flags(
        c=c,
    ))


def _srl(x):
    return (x >> 1, _flags(
        z=not bool(x >> 1),
        c=bool(x & 1),
    ))


def _sub(a, x):
    tmp = a - x
    return (tmp & 0xff, _flags(
        z=not bool(tmp & 0xff),
        n=True,
        h=(a & 0xf) - (x & 0xf) < 0,
        c=bool(tmp < 0),
    ))


def _sbc(a, x, f):
    return _sub(a, x + _carry(f))


def _swap(a):
    tmp = a << 4 & 0xf0 | a >> 4
    return (tmp, _flags(
        z=not bool(tmp),
    ))


def _xor(a, x):
    tmp = a ^ x
    return (tmp, _flags(z=not bool(tmp)))


def err(*args):
    print("err")


def adc(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (r8.A, r8.F) = _adc(r8.A, x, r8.F)
        return
    return err(args)


def add(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'HL' in dst[0] and 'r16' in src[0]:
        (r16.HL, r8.F) = _add16(r16.HL, r16[src[1]], r8.F)
        return
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (r8.A, r8.F) = _add(r8.A, x)
        return
    return err(args)


def cp(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (_, r8.F) = _sub(r8.A, x)
        return
    return err(args)


def cpl(*args):
    if 0 != len(args):
        return err(args)
    r8.A = ~r8.A & 0xff
    r8.F |= _flags(n=1, h=1)


def dec(*args):
    if 1 != len(args):
        return err(args)
    (dst,) = args
    if 'r8' in dst[0]:
        (r8[dst[1]], r8.F) = _dec8(r8[dst[1]], r8.F)
        return
    if 'r16' in dst[0]:
        r16[dst[1]] = _dec16(r16[dst[1]])
        return
    return err(args)


def inc(*args):
    if 1 != len(args):
        return err(args)
    (dst,) = args
    if 'r8' in dst[0]:
        (r8[dst[1]], r8.F) = _inc8(r8[dst[1]], r8.F)
        return
    if 'r16' in dst[0]:
        r16[dst[1]] = _inc16(r16[dst[1]])
        return
    return err(args)


def ld(*args):
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'r8' in dst[0]:
        if 'n8' in src[0]:
            r8[dst[1]] = src[1]
            return
        if 'r8' in src[0]:
            r8[dst[1]] = r8[src[1]]
            return
        if '[HL]' in src[0]:
            r8[dst[1]] = mem8[r16.HL]
            return
    if '[HL]' in dst[0]:
        if 'n8' in src[0]:
            mem8[r16.HL] = src[1]
            return
        if 'r8' in src[0]:
            mem8[r16.HL] = r8[src[1]]
            return
    if 'A' in dst[0] and '[HLD]' in src[0]:
        r8.A = mem8[r16.HL]
        r16.HL -= 1
        return
    if 'A' in dst[0] and '[HLI]' in src[0]:
        r8.A = mem8[r16.HL]
        r16.HL += 1
        return
    if '[HLD]' in dst[0] and 'A' in src[0]:
        mem8[r16.HL] = r8.A
        r16.HL -= 1
        return
    if '[HLI]' in dst[0] and 'A' in src[0]:
        mem8[r16.HL] = r8.A
        r16.HL += 1
        return
    if 'r16' in dst[0]:
        if 'n16' in src[0]:
            r16[dst[1]] = src[1]
            return
    if 'SP' in dst[0]:
        if 'n16' in src[0]:
            r16.SP = src[1]
            return
    return err(args)


def nop(*args):
    if 0 != len(args):
        return err(args)
    pass


def pop(*args):
    if 1 != len(args):
        return err(args)
    (dst,) = args
    if 'r16' in dst[0]:
        r16[dst[1]] = mem16[r16.SP]
        r16.SP += 2
        return
    return err(args)


def print_d(*args):
    if 1 != len(args):
        return err(args)
    (src,) = args
    if 'n16' in src[0]:
        print(src[1])
        return
    if 'r8' in src[0]:
        print(r8[src[1]])
        return
    if 'r16' in src[0]:
        print(r16[src[1]])
        return
    return err(args)


def push(*args):
    if 1 != len(args):
        return err(args)
    (src,) = args
    if 'r16' in src[0]:
        r16.SP -= 2
        mem16[r16.SP] = r16[src[1]]
        return
    return err(args)


def r_1(*args):
    if 1 != len(args):
        return err(args)
    (addr,) = args
    if 'n16' in addr[0]:
        x = mem8[addr[1]]
        print(f"${x:02x}")
        return
    return err(args)


def r_2(*args):
    if 1 != len(args):
        return err(args)
    (addr,) = args
    if 'n16' in addr[0]:
        i = addr[1]
        if 0x10000 - 2 < i:
            return err(args)
        print(f"${mem16[i]:04x}")
        return
    return err(args)


def r_4(*args):
    if 1 != len(args):
        return err(args)
    (addr,) = args
    if 'n16' in addr[0]:
        i = addr[1]
        if 0x10000 - 4 < i:
            return err(args)
        print(f"${mem32[i]:08x}")
        return
    return err(args)


def rrca(*args):
    if 0 != len(args):
        return err(args)
    (r8.A, r8.F) = _rrca(r8.A)


def sbc(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (r8.A, r8.F) = _sbc(r8.A, x, r8.F)
        return
    return err(args)


def srl(*args):
    if 1 != len(args):
        return err(args)
    (dst,) = args
    if 'r8' in dst[0]:
        (r8[dst[1]], r8.F) = _srl(r8[dst[1]])
        return
    if '[HL]' in dst[0]:
        (mem8[r16.HL], r8.F) = _srl(mem8[r16.HL])
        return
    return err(args)


def status(*args):
    z = "Z" if flag.Z else "-"
    n = "N" if flag.N else "-"
    h = "H" if flag.H else "-"
    c = "C" if flag.C else "-"
    print(f"A: {r8.A:02x}  F: {r8.F:02x}  (AF: {r16.AF:04x})")
    print(f"B: {r8.B:02x}  C: {r8.C:02x}  (BC: {r16.BC:04x})")
    print(f"D: {r8.D:02x}  E: {r8.E:02x}  (DE: {r16.DE:04x})")
    print(f"H: {r8.H:02x}  L: {r8.L:02x}  (HL: {r16.HL:04x})")
    print(f"PC: {r16.PC:04x}  SP: {r16.SP:04x}")
    print(f"F: [{z}{n}{h}{c}]")


# status (mgba)
# A: 01  F: B0  (AF: 01B0)
# B: 00  C: 13  (BC: 0013)
# D: 00  E: D8  (DE: 00D8)
# H: 01  L: 4D  (HL: 014D)
# PC: 0100  SP: FFFE
# F: [Z-HC]
# ROM: 01  RAM: 00  WRAM: 01  VRAM: 00
# IE: 00  IF: E1  IME: 0
# LCDC: 91  STAT: 84  LY: 00
# Next video mode: 18
# 00:0100:  F3    di


def sub(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (r8.A, r8.F) = _sub(r8.A, x)
        return
    return err(args)


def swap(*args):
    if 1 != len(args):
        return err(args)
    (dst,) = args
    if 'r8' in dst[0]:
        (r8[dst[1]], r8.F) = _swap(r8[dst[1]])
        return
    if '[HL]' in dst[0]:
        (mem8[r16.HL], r8.F) = _swap(mem8[r16.HL])
        return
    return err(args)


def x_1(*args):
    if 2 != len(args):
        return err(args)
    (offset, count) = args
    if not 'n16' in offset[0]:
        return err(args)
    if not 'n8' in count[0]:
        return err(args)
    (offset, count) = (offset[1], count[1])
    if (0x10000 < count + offset):
        return err(args)
    for xs in _chunks(0x10 // 1, range(offset, count + offset)):
        print(f"${xs.start:04x}:", end='')
        for x in xs:
            print(f" {mem8[x]:02x}", end='')
        print()


def x_2(*args):
    if 2 != len(args):
        return err(args)
    (offset, count) = args
    if not 'n16' in offset[0]:
        return err(args)
    if not 'n8' in count[0]:
        return err(args)
    (offset, count) = (offset[1], count[1])
    if (0x10000 < 2 * count + offset):
        return err(args)
    for xs in _chunks(0x10 // 2, range(offset, 2 * count + offset, 2)):
        print(f"${xs.start:04x}:", end='')
        for x in xs:
            print(f" {mem16[x]:04x}", end='')
        print()


def x_4(*args):
    if 2 != len(args):
        return err(args)
    (offset, count) = args
    if not 'n16' in offset[0]:
        return err(args)
    if not 'n8' in count[0]:
        return err(args)
    (offset, count) = (offset[1], count[1])
    if (0x10000 < 4 * count + offset):
        return err(args)
    for xs in _chunks(0x10 // 4, range(offset, 4 * count + offset, 4)):
        print(f"${xs.start:04x}:", end='')
        for x in xs:
            print(f" {mem32[x]:08x}", end='')
        print()


def xor(*args):
    if 1 == len(args):
        args = [(['A', 'r8'], 'A'), args[0]]
    if 2 != len(args):
        return err(args)
    (dst, src) = args
    if 'A' not in dst[0]:
        return err(args)
    x = None
    if 'n8' in src[0]:
        x = src[1]
    if 'r8' in src[0]:
        x = r8[src[1]]
    if x is not None:
        (r8.A, r8.F) = _xor(r8.A, x)
        return
    return err(args)


mnemonics = {
    'adc': adc,
    'add': add,
    'cp': cp,
    'cpl': cpl,
    'dec': dec,
    'inc': inc,
    'ld': ld,
    'nop': nop,
    'p': print_d,
    'pop': pop,
    'print': print_d,
    'push': push,
    'r/1': r_1,
    'r/2': r_2,
    'r/4': r_4,
    'rrca': rrca,
    'sbc': sbc,
    'srl': srl,
    'status': status,
    'sub': sub,
    'swap': swap,
    'x/1': x_1,
    'x/2': x_2,
    'x/4': x_4,
    'xor': xor,
}


def instruction(s):
    s = str.split(s, ';', maxsplit=1).pop(0)
    s = str.split(s, maxsplit=1)
    if not s:
        return ('nop', [])
    mnemonic = s.pop(0)
    args = list(map(tokenize, map(str.strip, str.split(s.pop(), ',')))) if s else []
    return (mnemonic, args)
