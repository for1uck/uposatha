# -*- coding: utf-8 -*-
"""
Myanmar calendar kernel — faithful Python port of the algorithm embedded in
the "美德雅 / Metteyya" Android app (package cn.com.metteyya.news, v1.3.4):

  com.mmcalendar.MyanmarDateKernelA
  com.mmcalendar.Era
  com.mmcalendar.BinarySearchUtil
  com.haibin.calendarview.CalendarUtil (moon-name / festival rules)

The app marks Uposatha (布萨/伍波思特) days purely on-device with this code;
no server data is involved. This port reproduces the exact same arithmetic
(floating point constants included) so the generated dates match the app.

Port reference: smali bytecode decompiled from classes2.dex.
"""

import math
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Era constants  (from Era.smali -> G_ERAS)
#
# Each era: eid, begin (ME), end (ME), WO (waso offset), NM, fme (full-moon
# corrections [myear, days]), wte (watat exceptions [myear, watat]).
# ---------------------------------------------------------------------------

_ERAS_RAW = [
    dict(eid=1.1, begin=-999, end=797, wo=-1.1, nm=-1,
         fme=[(205, 1), (246, 1), (471, 1), (572, -1), (651, 1), (653, 2),
              (656, 1), (672, 1), (729, 1), (767, -1)],
         wte=[]),
    dict(eid=1.2, begin=798, end=1099, wo=-1.1, nm=-1,
         fme=[(813, -1), (849, -1), (851, -1), (854, -1), (927, -1),
              (933, -1), (936, -1), (938, -1), (949, -1), (952, -1),
              (963, -1), (968, -1), (1039, -1)],
         wte=[]),
    dict(eid=1.3, begin=1100, end=1216, wo=-0.85, nm=-1,
         fme=[(1120, 1), (1126, -1), (1150, 1), (1172, -1), (1207, 1)],
         wte=[(1201, 1), (1202, 0)]),
    dict(eid=2.0, begin=1217, end=1311, wo=-1.0, nm=-1,
         fme=[(1234, 1), (1261, -1)],
         wte=[(1263, 1), (1264, 0)]),
    dict(eid=3.0, begin=1312, end=9999, wo=-0.5, nm=8,
         fme=[(1377, 1)],
         wte=[(1344, 1), (1345, 0)]),
]

SY = 1577917828.0 / 4320000.0          # solar year  = 365.2587564814815
LM = 1577917828.0 / 53433336.0         # lunar month = 29.53058794607172
MO = 1954168.050623                    # origin offset
SE3 = 132.88764575732273
E9 = 0.9076417607184055
JD_2000_01_01 = 2451545                # app convention (local midnight)


def _search(myear, table):
    """Lcom/mmcalendar/BinarySearchUtil;->search(D[[I)I

    Exact-key binary search over rows [year, value]: returns the row index
    only when the year itself is listed, otherwise -1. (Corrections in the
    fme/wte tables apply to the listed years alone.)
    """
    if not table:
        return -1
    lo, hi = 0, len(table) - 1
    while lo <= hi:
        mid = (lo + hi) >> 1
        key = table[mid][0]
        if key < myear:
            lo = mid + 1
        elif key > myear:
            hi = mid - 1
        else:
            return mid
    return -1


def _era_for(myear):
    e = len(_ERAS_RAW) - 1
    while myear < _ERAS_RAW[e]["begin"]:
        e -= 1
    return _ERAS_RAW[e]


def chk_watat(myear):
    """Lcom/mmcalendar/MyanmarDateKernelA;->chk_watat(D)Ljava/util/Map;"""
    e = _era_for(myear)
    nm = e["nm"]
    wo = e["wo"]

    v = (12 - nm) * E9
    t = ((myear + 3739.0) * SY) % LM
    if t < v:
        t += LM
    t2 = myear * SY + MO - t + SE3 + wo
    fm = round(t2)

    if e["eid"] >= 2.0:
        watat = 1.0 if t >= (LM - nm * E9) else 0.0
    else:
        w = (myear * 7.0 + 2.0) % 19.0
        if w < 0:
            w += 19.0
        watat = math.floor(w / 12.0)

    i = _search(myear, e["wte"])
    if i >= 0:
        watat = float(e["wte"][i][1])
    if watat > 0:
        i = _search(myear, e["fme"])
        if i >= 0:
            fm += e["fme"][i][1]
    return {"fm": float(fm), "watat": watat}


def chk_my(myear):
    """Lcom/mmcalendar/MyanmarDateKernelA;->chk_my(D)Ljava/util/Map;"""
    cur = chk_watat(myear)
    watat = cur["watat"]
    i = 0
    while True:
        i += 1
        prev = chk_watat(myear - i)
        if not (prev["watat"] == 0.0 and i < 3):
            break

    werr = 0.0
    if watat > 0:
        myt = (cur["fm"] - prev["fm"]) % 354.0
        myt = math.floor(myt / 31.0) + 1.0
        fm = cur["fm"]
        if myt != 30.0 and myt != 31.0:
            werr = 1.0
    else:
        myt = 0.0
        fm = prev["fm"] + i * 354.0

    tg1 = prev["fm"] + i * 354.0 - 102.0
    return {"myt": myt, "tg1": tg1, "fm": fm, "werr": werr}


def gregorian_to_jd(d: date) -> float:
    """getJdDay1 for a local-midnight Gregorian date (all inputs are exact
    calendar days, so Java long-division truncation never changes sign)."""
    return float(JD_2000_01_01 + (d - date(2000, 1, 1)).days)


def get_moon_day(jd: float) -> int:
    """Lcom/mmcalendar/MyanmarDateKernelA;->getMoonDay(D)I

    Returns (among other values) 1 = full moon day, 3 = new moon day.
    """
    mm = float(round(jd))
    my = math.floor((mm - 0.5 - MO) / SY)
    info = chk_my(my)
    tg1 = info["tg1"]
    myt = info["myt"]

    a = mm - tg1 + 1.0
    b1 = math.floor(myt / 2.0)
    c1 = math.floor(1.0 / (myt + 1.0))

    d = math.floor((1.0 - c1) * 30.0 + 354.0 + b1)
    # smali: v0 after .line 88 is `a`; .line 94 does `v16 = v0 - 1.0` only
    # for the (a-1)/yearLength division, but `v0` itself stays equal to `a`.
    # Then `v0 -= e*yearLength`, so f = a - e*yearLength (NOT a-1-e*d).
    e = math.floor((a - 1.0) / d)
    f = a - e * d
    g = math.floor((f + 423.0) / 512.0)
    h = math.floor((f - g * b1 + g * c1 * 30.0 + 29.26) / 29.544)
    k = math.floor((h + 12.0) / 16.0)
    hh = math.floor((h + 11.0) / 16.0)

    f = f - math.floor(29.544 * h - 29.26)
    f = f - b1 * k
    f = f + c1 * hh * 30.0

    n3 = hh * 3.0 - k * 4.0
    rem = (h + n3) % 2.0
    length = 30.0 - rem
    if h + n3 == 3.0:
        length += b1

    result = math.floor((1.0 + f) / 16.0) + math.floor(f / 16.0) + math.floor(f / length)
    return int(result)


# ---------------------------------------------------------------------------
# CalendarUtil rules (Chinese labels used by the app)
# ---------------------------------------------------------------------------

FULL_MOON = "月圆日"
NEW_MOON = "月黑日"
LAST_QUARTER = "下弦月"
FIRST_QUARTER = "上弦月"


def get_moon_name(d: date) -> str:
    """Lcom/haibin/calendarview/CalendarUtil;->getMoonName(Calendar)"""
    jd = gregorian_to_jd(d)
    md = get_moon_day(jd)
    if md == 1:
        return FULL_MOON
    if md == 3:
        return NEW_MOON
    md = get_moon_day(jd - 8.0)
    if md == 1:
        return LAST_QUARTER
    if md == 3:
        return FIRST_QUARTER
    return ""


def _prev_day_full_moon(d: date) -> bool:
    return get_moon_name(d - timedelta(days=1)) == FULL_MOON


def calculate_days(d: date, moon_name: str):
    """Lcom/haibin/calendarview/CalendarUtil;->calculateDays(Calendar)
    Returns (day_label, festival_name); either may be "".
    """
    year, month, day = d.year, d.month, d.day
    festival = ""

    if moon_name == FULL_MOON:
        if month == 2:
            festival = "敬僧节"
        elif month == 5:
            festival = "敬佛节"
        elif month == 7:
            # leap second-Waso years: first Waso full moon carries no label
            if year not in (2020, 2023, 2031) and year != 2039:
                festival = "敬法节"
        elif month == 8:
            if year in (2020, 2023, 2031) or year == 2039:
                if year != 2023 or day == 1:
                    festival = "敬法节"
        elif month == 10:
            # smali: year 2039 has no October label (see November); years
            # 2020/2031 label only when the full moon is the 31st; every
            # other year's October full moon is Pavarana (出雨安居).
            if year != 2039:
                if year in (2020, 2031):
                    if day == 31:
                        festival = "出雨安居"
                else:
                    festival = "出雨安居"
        elif month == 11:
            if year == 2039 and day == 1:
                festival = "出雨安居"

    # Vassa entry is observed the day after the (first/second) Waso full moon.
    if year in (2020, 2023, 2031) or year == 2039:
        if month == 8 and _prev_day_full_moon(d):
            festival = "入雨安居"
    else:
        if month == 7 and _prev_day_full_moon(d):
            festival = "入雨安居"

    day_label = "伍波思特日" if festival == "" and moon_name != "" else ""
    # NOTE (faithful to app bytecode): the app's calculateDays() only emits
    # the generic "伍波思特日" string as a register initialiser; ordinary
    # phase days are shown via MoonDate.moonName (月圆日/月黑日/上弦月/下弦月).
    return moon_name, festival
