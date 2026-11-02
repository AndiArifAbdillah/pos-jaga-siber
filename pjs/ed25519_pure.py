"""Tanda tangan Ed25519 dalam Python murni (mengikuti RFC 8032).

Dipakai hanya kalau pustaka `cryptography` tidak terpasang. Lebih lambat,
tetapi hasilnya sama persis dengan pustaka resmi. Lihat docs/belajar/07.
"""

import hashlib

p = 2**255 - 19
q = 2**252 + 27742317777372353535851937790883648493  # jumlah titik dalam grup
d = -121665 * pow(121666, p - 2, p) % p
sqrt_m1 = pow(2, (p - 1) // 4, p)


def _sha512_int(data):
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


def _recover_x(y, sign):
    if y >= p:
        return None
    x2 = (y * y - 1) * pow(d * y * y + 1, p - 2, p)
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (p + 3) // 8, p)
    if (x * x - x2) % p != 0:
        x = x * sqrt_m1 % p
    if (x * x - x2) % p != 0:
        return None
    if (x & 1) != sign:
        x = p - x
    return x


_g_y = 4 * pow(5, p - 2, p) % p
_g_x = _recover_x(_g_y, 0)
G = (_g_x, _g_y, 1, _g_x * _g_y % p)


def _add(P, Q):
    a = (P[1] - P[0]) * (Q[1] - Q[0]) % p
    b = (P[1] + P[0]) * (Q[1] + Q[0]) % p
    c = 2 * P[3] * Q[3] * d % p
    e = 2 * P[2] * Q[2] % p
    E, F, H, I = b - a, e - c, e + c, b + a
    return (E * F, H * I, F * H, E * I)


def _mul(s, P):
    Q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            Q = _add(Q, P)
        P = _add(P, P)
        s >>= 1
    return Q


def _equal(P, Q):
    if (P[0] * Q[2] - Q[0] * P[2]) % p != 0:
        return False
    return (P[1] * Q[2] - Q[1] * P[2]) % p == 0


def _compress(P):
    zinv = pow(P[2], p - 2, p)
    x = P[0] * zinv % p
    y = P[1] * zinv % p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


def _decompress(data):
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % p)


def _expand(secret):
    h = hashlib.sha512(secret).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_key(secret):
    a, _ = _expand(secret)
    return _compress(_mul(a, G))


def sign(secret, message):
    a, prefix = _expand(secret)
    A = _compress(_mul(a, G))
    r = _sha512_int(prefix + message) % q
    R = _compress(_mul(r, G))
    h = _sha512_int(R + A + message) % q
    s = (r + h * a) % q
    return R + int.to_bytes(s, 32, "little")


def verify(public, message, signature):
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _decompress(public)
    R = _decompress(signature[:32])
    if A is None or R is None:
        return False
    s = int.from_bytes(signature[32:], "little")
    if s >= q:
        return False
    h = _sha512_int(signature[:32] + public + message) % q
    return _equal(_mul(s, G), _add(R, _mul(h, A)))
