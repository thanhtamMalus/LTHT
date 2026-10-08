#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grade_datalab.py - Tự động build, chạy test, đếm toán tử (ops) và chấm điểm datalab.c
(Lab01 - Data Lab - Bộ đề 2, ANTT.2)

Cách dùng (để 3 file cùng thư mục):
    python check_datalab.py
    python check_datalab.py --n 300 --seed 1 --show 10
    python check_datalab.py --only getNibble remPw2
    python check_datalab.py --report ketqua.md

Với mỗi câu, script in:
  - Bảng: Test case (PT mẫu trong đề) | Mong đợi (theo đề) | Thực tế (chạy datalab.exe) | Đúng/Sai
  - Test bổ sung (biên + ngẫu nhiên): số đúng/tổng (chỉ liệt kê các test sai)
  - Số ops đã dùng / Max Ops, kiểm tra luật (toán tử/cấu trúc/hằng số bị cấm)
Cuối cùng là bảng tổng kết: câu nào ĐẠT (đúng hết test, ops <= Max Ops, không vi phạm luật).
"""
import argparse
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

try:  # in tiếng Việt đúng trên Windows
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

M32 = 0xFFFFFFFF
INT_MIN, INT_MAX = -(1 << 31), (1 << 31) - 1


def u32(v):
    return v & M32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def f32(bits):
    return struct.unpack("<f", struct.pack("<I", u32(bits)))[0]


def is_nan(bits):
    return (bits & 0x7FFFFFFF) > 0x7F800000


# ============================================================================
# HÀM THAM CHIẾU (đáp án đúng theo đề)
# ============================================================================
def r_subtract(x, y):      return u32(x - y)
def r_cal100x(x):          return u32(100 * x)
def r_getNibble(x, n):     return (u32(x) >> (4 * n)) & 0xF
def r_clearByte(x, n):     return u32(x) & ~(0xFF << (8 * n)) & M32
def r_mulpw2(x, n):        return u32(s32(x) >> (-n))          # x > 0, -31 <= n <= -1
def r_remPw2(x, n):                                            # x % 2^n kiểu C
    r = abs(s32(x)) % (1 << n)
    return u32(-r if s32(x) < 0 else r)
def r_isNegation(x, y):    return int(u32(-x) == u32(y))
def r_isMul8Not16(x):      return int(u32(x) & 15 == 8)
def r_isNonPositive(x):    return int(s32(x) <= 0)
def r_isTopBit(x, n):      return int(s32(x) > 0 and (1 << n) <= s32(x) < (1 << (n + 1)))
def r_addOK(x, y):         return int(INT_MIN <= s32(x) + s32(y) <= INT_MAX)
def r_allOddBits(x):       return int(u32(x) & 0xAAAAAAAA == 0xAAAAAAAA)
def r_float_nabs(uf):      return u32(uf) if is_nan(u32(uf)) else u32(uf) | 0x80000000
def r_float_sign(uf):
    uf = u32(uf)
    if is_nan(uf) or (uf & 0x7FFFFFFF) == 0:
        return 0
    return u32(-1) if uf >> 31 else 1
def r_float_pwr2(x):
    x = s32(x)
    if x < -149: return 0
    if x < -126: return 1 << (x + 149)
    if x <= 127: return (x + 127) << 23
    return 0x7F800000
def r_float_isInt(uf):
    uf = u32(uf)
    if ((uf >> 23) & 0xFF) == 0xFF:
        return 0
    v = f32(uf)
    return int(v == math.floor(v))


# ============================================================================
# THÔNG TIN TỪNG CÂU (theo đề): STT, tên, ref, kiểu tham số, điểm, Max Ops, phần, PT mẫu
#   kiểu tham số: 'i' = int có dấu, 'u' = unsigned (hiển thị hex)
# ============================================================================
def _F(stt, name, ref, kinds, pts, mx, part, sig, ex):
    return dict(stt=stt, name=name, ref=ref, kinds=kinds, pts=pts, maxops=mx, part=part, sig=sig, ex=ex)


FUNCS = [
    _F("1.1", "subtract", r_subtract, "ii", 0.5, 8, 1, "int subtract(x,y)",
       [((10, 3), 7), ((0, 5), -5), ((-4, -9), 5)]),
    _F("1.2", "cal100x", r_cal100x, "i", 1, 10, 1, "int cal100x(x)",
       [((0,), 0), ((7,), 700), ((-3,), -300)]),
    _F("1.3", "getNibble", r_getNibble, "ii", 1, 10, 1, "int getNibble(x,n)",
       [((0x12345678, 0), 0x8), ((0x12345678, 5), 0x3), ((0xABCDEF01, 7), 0xA)]),
    _F("1.4", "clearByte", r_clearByte, "ii", 1.5, 20, 1, "int clearByte(x,n)",
       [((0x12345678, 1), 0x12340078), ((-1, 0), 0xFFFFFF00), ((0x5501, 0), 0x5500)]),
    _F("1.5", "mulpw2", r_mulpw2, "ii", 1.5, 8, 1, "int mulpw2(x,n)",
       [((20, -1), 10), ((60, -2), 15), ((32, -4), 2)]),
    _F("1.6", "remPw2", r_remPw2, "ii", 1.5, 20, 1, "int remPw2(x,n)",
       [((15, 2), 3), ((-15, 2), -3), ((-16, 3), 0), ((-1, 4), -1)]),
    _F("2.1", "isNegation", r_isNegation, "ii", 1.5, 8, 2, "int isNegation(x,y)",
       [((4, -4), 1), ((0, 0), 1), ((5, -6), 0), ((3, 3), 0)]),
    _F("2.2", "isMul8Not16", r_isMul8Not16, "i", 0.5, 10, 2, "int isMul8Not16(x)",
       [((8,), 1), ((24,), 1), ((16,), 0), ((12,), 0)]),
    _F("2.3", "isNonPositive", r_isNonPositive, "i", 1, 15, 2, "int isNonPositive(x)",
       [((10,), 0), ((-5,), 1), ((0,), 1)]),
    _F("2.4", "isTopBit", r_isTopBit, "ii", 1, 20, 2, "int isTopBit(x,n)",
       [((5, 2), 1), ((8, 2), 0), ((7, 3), 0), ((1, 0), 1)]),
    _F("2.5", "addOK", r_addOK, "ii", 1.5, 20, 2, "int addOK(x,y)",
       [((3, 4), 1), ((0x7FFFFFFF, 1), 0), ((0x80000000, -1), 0),
        ((0x80000000, 0x7FFFFFFF), 1), ((-1, -1), 1)]),
    _F("2.6", "allOddBits", r_allOddBits, "i", 1.5, 20, 2, "int allOddBits(x)",
       [((0xFFFFFFFD,), 0), ((0xAAAAAAAA,), 1), ((0xFFFFFFFF,), 1), ((0x2AAAAAAA,), 0)]),
    _F("3.1", "float_nabs", r_float_nabs, "u", 1, 10, 3, "unsigned float_nabs(uf)",
       [((0x3F800000,), 0xBF800000), ((0xC0200000,), 0xC0200000),
        ((0x00000000,), 0x80000000), ((0x7FC00000,), 0x7FC00000)]),
    _F("3.2", "float_sign", r_float_sign, "u", 1, 15, 3, "int float_sign(uf)",
       [((0x3F800000,), 1), ((0xC0200000,), -1), ((0x80000000,), 0),
        ((0x7FC00000,), 0), ((0x00000001,), 1)]),
    _F("3.3", "float_pwr2", r_float_pwr2, "i", 2, 30, 3, "unsigned float_pwr2(x)",
       [((0,), 0x3F800000), ((-1,), 0x3F000000), ((-127,), 0x00400000),
        ((-149,), 0x00000001), ((-150,), 0), ((128,), 0x7F800000)]),
    _F("3.4", "float_isInt", r_float_isInt, "u", 2, 30, 3, "int float_isInt(uf)",
       [((0x40400000,), 1), ((0x3FC00000,), 0), ((0x80000000,), 1),
        ((0x3F000000,), 0), ((0x4B000001,), 1), ((0x7F800000,), 0)]),
]

HEX_RET = {"getNibble", "clearByte", "float_nabs", "float_pwr2"}   # hàm hiển thị kết quả dạng hex


# ============================================================================
# SINH TEST BỔ SUNG (đúng miền giá trị theo đề)
# ============================================================================
INT_EDGES = [s32(e) for e in [
    0, 1, -1, 2, -2, 7, 8, 15, 16, 100, -100, 0x7F, 0x80, 0xFF, 0x100, 0x7FFF, 0x8000,
    0xFFFF, 0x10000, 0x12345678, -0x12345678, 0x55555555, 0xAAAAAAAA, 0xA5A5A5A5,
    0xFFFFFFFF, INT_MAX, INT_MIN, INT_MAX - 1, INT_MIN + 1, 0x40000000, 0x80000000,
    0x0F0F0F0F, 0xF0F0F0F0]]
POS_EDGES = sorted({e for e in INT_EDGES if e > 0} | {3, 4, 5, 6, 9, 31, 32, 33, 1000})

FLOAT_EDGES = [0x00000000, 0x80000000, 0x00000001, 0x80000001, 0x007FFFFF, 0x807FFFFF,
               0x00800000, 0x80800000, 0x3F800000, 0xBF800000, 0x3F000000, 0xBF000000,
               0x3FC00000, 0x40000000, 0x40490FDB, 0x40A00000, 0x4B000000, 0x4AFFFFFF,
               0x4B800000, 0x4B7FFFFF, 0x4EFFFFFF, 0x4F000000, 0xCF000000, 0x7F7FFFFF,
               0xFF7FFFFF, 0x7F800000, 0xFF800000, 0x7F800001, 0x7FC00000, 0xFFC00000,
               0x7FFFFFFF, 0xFFFFFFFF, 0x3F7FFFFF, 0x3F800001, 0x40400000, 0x41200000]

LIM100 = INT_MAX // 100   # |x| tối đa để 100*x không tràn


def gen_tests(n_rand, seed):
    rnd = random.Random(seed)
    rint = lambda: s32(rnd.getrandbits(32))
    rsmall = lambda: s32(rnd.getrandbits(rnd.randint(1, 32)))
    rpos = lambda: max(1, rnd.getrandbits(rnd.randint(1, 31)))   # số dương, độ dài bit đa dạng
    rnonneg = lambda: rnd.getrandbits(rnd.randint(1, 31))
    T = {}

    def uniq(lst):
        seen, out_ = set(), []
        for t in lst:
            k = tuple(u32(a) for a in t)
            if k not in seen:
                seen.add(k)
                out_.append(t)
        return out_

    T["subtract"] = uniq([(a, b) for a in INT_EDGES for b in INT_EDGES[:12] + [INT_MAX, INT_MIN]]
                         + [(rint(), rint()) for _ in range(n_rand)])
    T["cal100x"] = uniq([(a,) for a in INT_EDGES if -LIM100 <= a <= LIM100] + [(LIM100,), (-LIM100,)]
                        + [(rnd.randint(-LIM100, LIM100) >> rnd.randint(0, 24),) for _ in range(n_rand)])
    T["getNibble"] = uniq([(a, n) for a in INT_EDGES for n in range(8)]
                          + [(rint(), rnd.randint(0, 7)) for _ in range(n_rand)])
    T["clearByte"] = uniq([(a, n) for a in INT_EDGES for n in range(4)]
                          + [(rint(), rnd.randint(0, 3)) for _ in range(n_rand)])
    T["mulpw2"] = uniq([(a, n) for a in POS_EDGES for n in range(-31, 0)]
                       + [(rpos(), rnd.randint(-31, -1)) for _ in range(n_rand)])
    T["remPw2"] = uniq([(a, n) for a in INT_EDGES for n in range(0, 31)]
                       + [(rint(), rnd.randint(0, 30)) for _ in range(n_rand)])

    T["isNegation"] = uniq([(a, u32(-a)) for a in INT_EDGES]
                           + [(a, u32(-a) ^ (1 << rnd.randint(0, 31))) for a in INT_EDGES]
                           + [(a, b) for a in INT_EDGES[:15] for b in INT_EDGES[:15]]
                           + [(x, -x) for x in (rint() for _ in range(n_rand))]
                           + [(rint(), rint()) for _ in range(n_rand // 2)])
    T["isMul8Not16"] = uniq([(a,) for a in INT_EDGES if a >= 0]
                            + [(8 + 16 * k,) for k in range(0, 10)] + [(16 * k,) for k in range(0, 10)]
                            + [(((rnonneg() & ~15) | 8) & INT_MAX,) for _ in range(n_rand // 3)]
                            + [((rnonneg() & ~7),) for _ in range(n_rand // 3)]
                            + [(rnonneg(),) for _ in range(n_rand // 3)])
    T["isNonPositive"] = uniq([(a,) for a in INT_EDGES] + [(rsmall(),) for _ in range(n_rand)])
    tb = [(a, n) for a in POS_EDGES for n in range(31)]
    tb += [(1 << n, n) for n in range(31)]
    tb += [((1 << n) | (rnd.getrandbits(31) & ((1 << n) - 1)), n) for n in range(31)]
    tb += [((1 << n), m) for n in range(31) for m in (n - 1, n + 1) if 0 <= m <= 30]
    tb += [(rpos(), rnd.randint(0, 30)) for _ in range(n_rand)]
    T["isTopBit"] = uniq(tb)
    T["addOK"] = uniq([(INT_MAX, 1), (INT_MAX, INT_MAX), (INT_MIN, -1), (INT_MIN, INT_MIN),
                       (INT_MAX, INT_MIN), (INT_MIN, INT_MAX), (0, 0), (-1, 1), (1 << 30, 1 << 30)]
                      + [(a, b) for a in INT_EDGES for b in INT_EDGES]
                      + [(rint(), rint()) for _ in range(n_rand)]
                      + [(rnd.randint(INT_MAX // 2, INT_MAX), rnd.randint(INT_MAX // 2, INT_MAX)) for _ in range(n_rand // 4)]
                      + [(rnd.randint(INT_MIN, INT_MIN // 2), rnd.randint(INT_MIN, INT_MIN // 2)) for _ in range(n_rand // 4)])
    odd_full = 0xAAAAAAAA
    T["allOddBits"] = uniq([(a,) for a in INT_EDGES] + [(s32(odd_full ^ (1 << i)),) for i in range(32)]
                           + [(s32(odd_full | rnd.getrandbits(32)),) for _ in range(n_rand // 2)]
                           + [(rint(),) for _ in range(n_rand // 2)])

    rfloat = lambda: rnd.getrandbits(32)
    rfloat_exp = lambda: (rnd.getrandbits(1) << 31) | (rnd.randint(100, 170) << 23) | rnd.getrandbits(23)
    rfloat_int = lambda: struct.unpack("<I", struct.pack("<f", float(rnd.randint(-10**6, 10**6))))[0]
    T["float_nabs"] = uniq([(a,) for a in FLOAT_EDGES] + [(rfloat(),) for _ in range(n_rand)])
    T["float_sign"] = uniq([(a,) for a in FLOAT_EDGES] + [(rfloat(),) for _ in range(n_rand)])
    T["float_pwr2"] = uniq([(x,) for x in range(-160, -100)] + [(x,) for x in range(-10, 11)]
                           + [(x,) for x in range(120, 135)]
                           + [(x,) for x in (INT_MIN, INT_MAX, -1000, 1000, -150, -149, -148, -127, -126, -125, 127, 128)]
                           + [(rnd.randint(-200, 200),) for _ in range(n_rand // 2)])
    T["float_isInt"] = uniq([(a,) for a in FLOAT_EDGES] + [(rfloat(),) for _ in range(n_rand // 2)]
                            + [(rfloat_exp(),) for _ in range(n_rand)]
                            + [(rfloat_int(),) for _ in range(n_rand // 2)])
    return T


# ============================================================================
# ĐẾM TOÁN TỬ + KIỂM TRA LUẬT (phân tích văn bản datalab.c)
# ============================================================================
TOKEN_RE = re.compile(r"<<=|>>=|&&|\|\||==|!=|<=|>=|<<|>>|\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|->|[~!&^|+\-*/%<>?=]")
COUNT12 = {"~", "!", "&", "^", "|", "<<", ">>", "+"}
COUNT3 = COUNT12 | {"-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"}
FORBID12 = {"&&", "||", "-", "==", "!=", "*", "/", "%", "<", ">", "<=", ">=", "?", "++", "--", "->"}
CTRL_RE = re.compile(r"\b(if|else|for|while|do|switch|case|goto)\b")
COMPOUND = {"+=": "+", "-=": "-", "*=": "*", "/=": "/", "%=": "%", "&=": "&", "|=": "|",
            "^=": "^", "<<=": "<<", ">>=": ">>"}


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    src = re.sub(r"//[^\n]*", " ", src)
    return re.sub(r'"(\\.|[^"\\])*"', '""', src)


def extract_body(src, name):
    m = re.search(r"\b%s\s*\([^)]*\)\s*\{" % re.escape(name), src)
    if not m:
        return None
    i, depth = m.end(), 1
    start = i
    while i < len(src) and depth:
        depth += (src[i] == "{") - (src[i] == "}")
        i += 1
    return src[start:i - 1]


def analyze_body(body, part):
    """Trả về (số ops, danh sách toán tử đã đếm, danh sách vi phạm)."""
    toks = TOKEN_RE.findall(body)
    counted = COUNT12 if part < 3 else COUNT3
    ops = [COMPOUND.get(t, t) for t in toks if COMPOUND.get(t, t) in counted]
    viol = []
    if part < 3:
        bad = sorted({t for t in toks if t in FORBID12})
        if bad:
            viol.append("toán tử cấm: " + " ".join(bad))
        ctrl = sorted(set(CTRL_RE.findall(body)))
        if ctrl:
            viol.append("cấu trúc cấm: " + " ".join(ctrl))
        big = []
        for lit in re.findall(r"\b0[xX][0-9a-fA-F]+|\b\d+", body):
            try:
                val = int(lit, 16) if lit[:2] in ("0x", "0X") else int(lit, 10)
            except ValueError:
                continue
            if val > 0xFF:
                big.append(lit)
        if big:
            viol.append("hằng số > 0xFF: " + " ".join(sorted(set(big))))
    else:
        if re.search(r"\b(float|double|union)\b", body):
            viol.append("dùng float/double/union")
        nohex = re.sub(r"\b0[xX][0-9a-fA-F]+", " ", body)
        if re.search(r"\b\d+\.\d*|\.\d+", nohex):
            viol.append("dùng hằng số thực")
    return len(ops), ops, viol


# ============================================================================
# BUILD + CHẠY
# ============================================================================
OUT = []


def out(s=""):
    print(s)
    OUT.append(s)


def table(headers, rows):
    w = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            w[i] = max(w[i], len(c))
    line = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    fmt = lambda r: "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(r)) + " |"
    for s in [line, fmt(headers), line] + [fmt(r) for r in rows] + [line]:
        out(s)


def build(c_file, main_file, exe):
    gcc = shutil.which("gcc")
    if not gcc:
        sys.exit("Không tìm thấy gcc. Hãy cài gcc/MinGW và thêm vào PATH.")
    cmd = [gcc, "-O1", "-Wall", "-fwrapv", c_file, main_file, "-o", exe]
    out("Build: gcc -O1 -Wall -fwrapv %s %s -o <exe>" % (os.path.basename(c_file), os.path.basename(main_file)))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.stderr.strip():
        out("--- Cảnh báo/lỗi của trình biên dịch ---")
        out(p.stderr.strip())
        out("----------------------------------------")
    if p.returncode != 0:
        sys.exit("BUILD THẤT BẠI -> 0 điểm. Hãy sửa lỗi biên dịch trước.")
    out("Build OK.\n")


def fmt_arg(v, kind):
    return str(s32(v)) if kind == "i" else "0x%08X" % u32(v)


def disp_arg(v, kind):
    if kind == "u":
        return "0x%08X" % u32(v)
    s = s32(v)
    return str(s) if -65536 < s < 65536 else "0x%08X" % u32(v)


def disp_ret(name, v):
    if name in HEX_RET:
        return "0x%X" % u32(v) if name == "getNibble" else "0x%08X" % u32(v)
    return str(s32(v))


def run_one(exe, fn, args):
    try:
        p = subprocess.run([exe, fn] + args, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    if p.returncode != 0:
        return None, "CRASH(%d)" % p.returncode
    s = p.stdout.strip()
    try:
        return int(s, 16), ""
    except ValueError:
        return None, "output lạ: " + s[:20]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Chấm điểm datalab.c")
    ap.add_argument("--c", default=os.path.join(here, "datalab.c"), help="file bài làm")
    ap.add_argument("--main", default=os.path.join(here, "datalab_main_set2.c"), help="file main của GV")
    ap.add_argument("--n", type=int, default=150, help="số test ngẫu nhiên mỗi hàm (mặc định 150)")
    ap.add_argument("--seed", type=int, default=2024)
    ap.add_argument("--show", type=int, default=5, help="số test bổ sung sai hiển thị tối đa mỗi hàm")
    ap.add_argument("--only", nargs="*", help="chỉ chấm các hàm này")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--report", help="ghi toàn bộ kết quả ra file (vd ketqua.md)")
    a = ap.parse_args()

    for f in (a.c, a.main):
        if not os.path.isfile(f):
            sys.exit("Không thấy file: " + f)

    # tự kiểm tra: PT mẫu trong đề phải khớp hàm tham chiếu
    for F in FUNCS:
        for args, exp in F["ex"]:
            if u32(F["ref"](*args)) != u32(exp):
                print("[CẢNH BÁO nội bộ] PT mẫu %s%s không khớp hàm tham chiếu" % (F["name"], args))

    with open(a.c, encoding="utf-8", errors="replace") as fh:
        src = strip_comments(fh.read())

    tmp = tempfile.mkdtemp(prefix="datalab_")
    exe = os.path.join(tmp, "datalab_grader" + (".exe" if os.name == "nt" else ""))
    try:
        build(a.c, a.main, exe)
        extra = gen_tests(a.n, a.seed)
        summary = []

        for F in FUNCS:
            if a.only and F["name"] not in a.only:
                continue
            name, kinds = F["name"], F["kinds"]
            ex_keys = {tuple(u32(v) for v in args) for args, _ in F["ex"]}
            extras = [t for t in extra[name] if tuple(u32(v) for v in t) not in ex_keys]

            def job(item, name=name, kinds=kinds):
                args, exp = item
                got, err = run_one(exe, name, [fmt_arg(v, k) for v, k in zip(args, kinds)])
                return args, u32(exp), got, err

            with ThreadPoolExecutor(max_workers=a.workers) as ex:
                r_ex = list(ex.map(job, F["ex"]))
                r_extra = list(ex.map(job, [(t, F["ref"](*t)) for t in extras]))

            out("=" * 78)
            out("Câu %s: %s   [%g điểm | Max Ops %d]" % (F["stt"], F["sig"], F["pts"], F["maxops"]))
            out("=" * 78)

            call = lambda args: "%s(%s)" % (name, ", ".join(disp_arg(v, k) for v, k in zip(args, kinds)))
            rows = []
            for i, (args, exp, got, err) in enumerate(r_ex, 1):
                rows.append([str(i), call(args), disp_ret(name, exp),
                             disp_ret(name, got) if got is not None else err,
                             "ĐÚNG" if got == exp else "SAI"])
            bad_extra = [r for r in r_extra if r[2] != r[1]]
            for args, exp, got, err in bad_extra[: a.show]:
                rows.append(["+", call(args), disp_ret(name, exp),
                             disp_ret(name, got) if got is not None else err, "SAI"])
            if len(bad_extra) > a.show:
                rows.append(["+", "... còn %d test bổ sung sai nữa" % (len(bad_extra) - a.show), "", "", ""])
            table(["#", "Test case", "Mong đợi (theo đề)", "Thực tế", "Kết quả"], rows)

            n_ex_ok = sum(1 for r in r_ex if r[2] == r[1])
            n_extra_ok = len(r_extra) - len(bad_extra)
            out("PT mẫu trong đề                : %d/%d đúng" % (n_ex_ok, len(r_ex)))
            out("Test bổ sung (biên + ngẫu nhiên): %d/%d đúng   (dòng '+' ở bảng là test sai)" %
                (n_extra_ok, len(r_extra)))
            all_ok = n_ex_ok == len(r_ex) and not bad_extra

            body = extract_body(src, name)
            if body is None:
                n_ops, op_list, viol = None, [], ["không tìm thấy hàm trong file"]
            else:
                n_ops, op_list, viol = analyze_body(body, F["part"])
            ops_ok = n_ops is not None and n_ops <= F["maxops"]
            out("Số ops đã dùng                 : %s / %d %s" %
                ("?" if n_ops is None else n_ops, F["maxops"], "(%s)" % " ".join(op_list) if op_list else ""))
            out("Kiểm tra luật                  : %s" % ("OK" if not viol else "VI PHẠM - " + "; ".join(viol)))
            passed = all_ok and ops_ok and not viol
            out("=> Câu này                     : %s\n" % ("ĐẠT" if passed else "CHƯA ĐẠT"))

            n_all = len(r_ex) + len(r_extra)
            n_ok = n_ex_ok + n_extra_ok
            if viol:
                pts, note = 0.0, "vi phạm luật -> 0 điểm"
            elif not all_ok:
                pts, note = 0.0, "sai %d test" % (n_all - n_ok)
            elif not ops_ok:
                pts, note = F["pts"] / 2, "vượt Max Ops -> chia đôi điểm"
            else:
                pts, note = F["pts"], ""
            summary.append((F, all_ok, n_ops, ops_ok, viol, passed, pts, note, n_ok, n_all))

        # ----------------------------- BẢNG TỔNG KẾT -----------------------------
        out("=" * 78)
        out("BẢNG TỔNG KẾT")
        out("=" * 78)
        rows = []
        for F, all_ok, n_ops, ops_ok, viol, passed, pts, note, n_ok, n_all in summary:
            rows.append([F["stt"], F["name"], "%d/%d" % (n_ok, n_all), "Đúng hết" if all_ok else "Có test sai",
                         "?" if n_ops is None else str(n_ops), str(F["maxops"]),
                         "OK" if ops_ok else "Vượt", "OK" if not viol else "Vi phạm",
                         "%g/%g" % (pts, F["pts"]), "ĐẠT" if passed else "CHƯA ĐẠT", note])
        table(["STT", "Hàm", "Test đúng", "Kết quả", "Ops", "Max", "So Max", "Luật", "Điểm", "Kết luận", "Ghi chú"], rows)
        total = sum(s[6] for s in summary)
        total_max = sum(s[0]["pts"] for s in summary)
        n_pass = sum(1 for s in summary if s[5])
        out("Số câu ĐẠT (đúng hết test + ops <= Max Ops + không vi phạm luật): %d/%d" % (n_pass, len(summary)))
        out("Điểm ước tính: %g / %g   (sai hoặc vi phạm luật = 0; đúng nhưng vượt Max Ops = chia đôi)" % (total, total_max))
        out("Lưu ý: số ops do script tự đếm (heuristic); công cụ chấm chính thức của GV có thể đếm hơi khác.")

        if a.report:
            with open(a.report, "w", encoding="utf-8") as fh:
                fh.write("\n".join(OUT) + "\n")
            print("\nĐã ghi báo cáo: " + a.report)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()