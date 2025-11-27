PRIM = 0x11d
GF_SIZE = 256

class ReedSolomonError(Exception):
    pass

_exp = [0] * (GF_SIZE * 2)
_log = [0] * GF_SIZE

def _init_tables():
    x = 1
    for i in range(GF_SIZE - 1):
        _exp[i] = x
        _log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= PRIM
    for i in range(GF_SIZE - 1, GF_SIZE * 2):
        _exp[i] = _exp[i - (GF_SIZE - 1)]

_init_tables()

def gf_add(a, b):
    return a ^ b

def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return _exp[_log[a] + _log[b]]

def gf_div(a, b):
    if b == 0:
        raise ZeroDivisionError()
    if a == 0:
        return 0
    return _exp[(_log[a] - _log[b]) % (GF_SIZE - 1)]

def gf_pow(a, power):
    if power == 0:
        return 1
    if a == 0:
        return 0
    return _exp[(_log[a] * power) % (GF_SIZE - 1)]

def gf_inverse(a):
    if a == 0:
        raise ZeroDivisionError()
    return _exp[(GF_SIZE - 1) - _log[a]]

# операции с многочленами 
def poly_strip(p):
    i = 0
    while i < len(p) - 1 and p[i] == 0:
        i += 1
    return p[i:]

def poly_add(a, b):
    if len(a) < len(b):
        a, b = b, a
    res = a.copy()
    offset = len(a) - len(b)
    for i in range(len(b)):
        res[i + offset] ^= b[i]
    return poly_strip(res)

def poly_scale(p, x):
    return [gf_mul(coef, x) for coef in p]

def poly_mul(a, b):
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        for j, bj in enumerate(b):
            if bj == 0:
                continue
            res[i + j] ^= gf_mul(ai, bj)
    return poly_strip(res)

def poly_eval(p, x):
    y = 0
    for coef in p:
        y = gf_mul(y, x) ^ coef
    return y

# генераторный многочлен 
def rs_generator(nsym):
    g = [1]
    for i in range(nsym):
        g = poly_mul(g, [1, _exp[i]])  # (x - alpha^i) but coefficients highest->lowest: [1, alpha^i]
    return g

# кодирование 
def encode(msg_bytes: bytes, nsym: int) -> bytes:
    gen = rs_generator(nsym)
    msg_padded = msg + [0] * nsym
    for i in range(len(msg)):
        coef = msg_padded[i]
        if coef != 0:
            for j in range(len(gen)):
                msg_padded[i + j] ^= gf_mul(gen[j], coef)
    parity = msg_padded[-nsym:]

    return bytes(msg + parity)

# декодирование 
def _calc_syndromes(codeword, nsym):
    return [poly_eval(list(codeword), _exp[i]) for i in range(nsym)]

def _berlekamp_massey(syndromes):
    err_loc = [1]
    old_loc = [1]
    for i in range(len(syndromes)):
        delta = syndromes[i]
        for j in range(1, len(err_loc)):
            delta ^= gf_mul(err_loc[-1 - j], syndromes[i - j])
        old_loc.append(0)
        if delta != 0:
            if len(old_loc) > len(err_loc):
                new_loc = poly_scale(old_loc, delta)
                old_loc = poly_scale(err_loc, gf_inverse(delta))
                err_loc = new_loc
            err_loc = poly_add(err_loc, poly_scale(old_loc, delta))
    return poly_strip(err_loc)

def _chien_search(err_loc, nmess):
    errs = []
    for i in range(nmess):
        x = _exp[(GF_SIZE - 1 - i) % (GF_SIZE - 1)]
        if poly_eval(err_loc, x) == 0:
            errs.append(nmess - 1 - i)
    return errs

def decode(codeword: bytes, nsym: int):
    if nsym <= 0:
        raise ValueError("nsym must be > 0")
    if len(codeword) < nsym:
        raise ValueError("codeword too short")
    cw = list(codeword)
    synd = _calc_syndromes(cw, nsym)
    if max(synd) == 0:
        # no errors
        return bytes(cw[:len(cw) - nsym]), 0

    err_loc = _berlekamp_massey(synd)
    err_pos = _chien_search(err_loc, len(cw))
    if len(err_pos) == 0:
        raise ReedSolomonError("Could not locate errors")

    if len(err_pos) * 2 > nsym:
        raise ReedSolomonError("Too many errors to correct")

    synd_poly = synd[:] + [0]
    err_loc_poly = err_loc[:]
    omega = poly_mul(synd_poly, err_loc_poly)
    omega = omega[len(omega) - (nsym):] if len(omega) >= nsym else omega

    err_loc_deriv = []
    for i in range(len(err_loc_poly) - 1):
        power = len(err_loc_poly) - 1 - i
        if power % 2 == 1:
            err_loc_deriv.append(err_loc_poly[i])

    for p in err_pos:
        x = _exp[(p + GF_SIZE - 1) % (GF_SIZE - 1)]
        xi_inv = gf_inverse(x)
        numerator = poly_eval(omega, xi_inv)
        denominator = poly_eval(err_loc_deriv, xi_inv)
        if denominator == 0:
            raise ReedSolomonError("Zero denominator while computing error magnitude")
        magnitude = gf_div(numerator, denominator)
        cw[p] ^= magnitude

    synd2 = _calc_syndromes(cw, nsym)
    if max(synd2) != 0:
        raise ReedSolomonError("Could not correct message")

    return bytes(cw[:len(cw) - nsym]), len(err_pos)


if __name__ == "__main__":
    msg = b"Hello RS"
    nsym = 10
    code = encode(msg, nsym)
    print("encoded:", code.hex())

    c = bytearray(code)
    c[2] ^= 0x23
    c[5] ^= 0x7f
    c[10] ^= 0x11
    print("with errors:", bytes(c).hex())

    try:
        decoded, n = decode(bytes(c), nsym)
        print("decoded:", decoded, "errors corrected:", n)
    except ReedSolomonError as e:
        print("decode failed:", e)
