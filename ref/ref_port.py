# Independent port of github.com/Beautiful-Days/mm-cal-js (TS), verbatim logic.
import math

SY = 365.2587564814815
LM = 29.53058794607172
MO = 1954168.050623

# only era 3 is exercised by 2000-2050, others included for completeness
_ERAS = [
    (1.1, -999, 797, -1.1, -1,
     [(205,1),(246,1),(471,1),(572,-1),(651,1),(653,2),(656,1),(672,1),(729,1),(767,-1)], []),
    (1.2, 798, 1099, -1.1, -1,
     [(813,-1),(849,-1),(851,-1),(854,-1),(927,-1),(933,-1),(936,-1),(938,-1),
      (949,-1),(952,-1),(963,-1),(968,-1),(1039,-1)], []),
    (1.3, 1100, 1216, -0.85, -1,
     [(1120,1),(1126,-1),(1150,1),(1172,-1),(1207,1)], [1201,1202]),
    (2.0, 1217, 1311, -1.0, 4, [(1234,1),(1261,-1)], [1263,1264]),
    (3.0, 1312, 9999, -0.5, 8, [(1377,1)], [1344,1345]),
]

def _consts(my):
    for eid, b, e, wo, nm, fme, wte in _ERAS:
        if b <= my <= e:
            break
    off = 0
    for i, (yr, o) in enumerate(fme):
        if yr == my:
            off = o
    ew = 1 if my in wte else 0
    return eid, wo + off, nm, ew

def check_watat(my):
    eid, wo, nm, ew = _consts(my)
    threshold = (SY/12 - LM) * (12 - nm)
    excess = (SY * (my + 3739)) % LM
    if excess < threshold:
        excess += LM
    fm = round(SY*my + MO - excess + 4.5*LM + wo)
    if eid >= 2:
        tw = LM - (SY/12 - LM) * nm
        watat = 1 if excess >= tw else 0
    else:
        watat = (my*7 + 2) % 19
        if watat < 0: watat += 19
        watat = watat // 12
    watat ^= ew
    return fm, watat

def check_my(my):
    fm2, w2 = check_watat(my)
    myt = w2
    yd = 0
    fm1, w1 = fm2, w2
    while True:
        yd += 1
        fm1, w1 = check_watat(my - yd)
        if not (w1 == 0 and yd < 3):
            break
    if myt:
        nd = (fm2 - fm1) % 354
        myt = nd // 31 + 1
        fm = fm2
    else:
        fm = fm1 + 354*yd
    tagu1 = fm1 + 354*yd - 102
    return myt, tagu1

def jd_to_my(jdn):
    jdn = int(round(jdn))
    my = math.floor((jdn - 0.5 - MO) / SY)
    myt, tagu1 = check_my(my)
    dd = jdn - tagu1 + 1
    b = myt // 2
    c = 1 // (myt + 1)
    year_len = 354 + (1 - c)*30 + b
    mt = (dd - 1) // year_len
    dd -= mt * year_len
    a = (dd + 423) // 512
    month = (dd - b*a + c*a*30 + 29.26) // 29.544
    month = int(math.floor(month))
    e = (month + 12) // 16
    f = (month + 11) // 16
    md = dd - int(math.floor(29.544*month - 29.26)) - b*e + c*f*30
    month += f*3 - e*4 + 12*mt
    mlen = 30 - (month % 2)
    if month == 3:
        mlen += myt // 2
    return my, myt, month, md, mlen

def moon_phase(md, mlen):
    return (md + 1)//16 + md//16 + md//mlen
