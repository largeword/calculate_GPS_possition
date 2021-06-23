import math

import numpy as np


def xyz2blh(xyz):  # 空间直角坐标转换为大地坐标
    blh = [0, 0, 0]
    # 长半轴
    a = 6378137.0
    # 扁率
    f = 1.0 / 298.257223563
    e2 = f * (2 - f)
    r2 = xyz[0] * xyz[0] + xyz[1] * xyz[1]
    z = xyz[2]
    zk = 0.0

    while (abs(z - zk) >= 0.0001):
        zk = z
        sinp = z / math.sqrt(r2 + z * z)
        v = a / math.sqrt(1.0 - e2 * sinp * sinp)
        z = xyz[2] + v * e2 * sinp

    if (r2 > 1E-12):
        blh[0] = math.atan(z / math.sqrt(r2))
        blh[1] = math.atan2(xyz[1], xyz[0])
    else:
        if (r2 > 0):
            blh[0] = math.pi / 2.0
        else:
            blh[0] = -math.pi / 2.0
        blh[1] = 0.0

    blh[2] = math.sqrt(r2 + z * z) - v
    return blh


def blh2xyz(blh):  # 大地坐标转空间直角坐标
    a = 6378137.0
    f = 1.0 / 298.257223563
    e = math.sqrt(2 * f - f * f)
    e2 = 0.00669437999013

    lat = blh[0]
    lon = blh[1]
    height = blh[2]

    slat = np.sin(lat)
    clat = np.cos(lat)
    slon = np.sin(lon)
    clon = np.cos(lon)

    t2lat = (np.tan(lat)) * (np.tan(lat))
    tmp = 1 - e * e
    tmpden = np.sqrt(1 + tmp * t2lat)
    tmp2 = np.sqrt(1 - e * e * slat * slat)
    N = a / tmp2

    x = (N + height) * clat * clon
    y = (N + height) * clat * slon
    z = (a * tmp * slat) / tmp2 + height * slat
    return [x, y, z]


def xyz2enu(xyz, orgblh):  # 空间直角坐标转站心坐标系

    lat = orgblh[0]
    lon = orgblh[1]
    height = orgblh[2]

    slat = np.sin(lat)
    clat = np.cos(lat)
    slon = np.sin(lon)
    clon = np.cos(lon)

    tmpxyz = [0, 0, 0]
    orgxyz = [0, 0, 0]
    tmporg = [0, 0, 0]
    difxyz = [0, 0, 0]
    enu = [0, 0, 0]

    orgxyz = blh2xyz(orgblh)

    for i in range(3):
        tmpxyz[i] = xyz[i]
        tmporg[i] = orgxyz[i]
        difxyz[i] = tmpxyz[i] - tmporg[i]

    R_list = [[-slon, clon, 0], [-slat * clon, -slat * slon, clat], [clat * clon, clat * slon, slat]]

    for i in range(3):
        enu[0] = enu[0] + R_list[0][i] * difxyz[i]
        enu[1] = enu[1] + R_list[1][i] * difxyz[i]
        enu[2] = enu[2] + R_list[2][i] * difxyz[i]
    return enu


def cal_E_A(rec_x, rec_y, rec_z, sat_x, sat_y, sat_z):
    b, l, _ = xyz2blh([rec_x, rec_y, rec_z])
    t = np.array([[-math.sin(b) * math.cos(l), -math.sin(b) * math.sin(l), math.cos(b)],
                  [-math.sin(l), math.cos(l), 0],
                  [math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)]])  # (XYZ to NEU)
    d_xyz = np.array([sat_x, sat_y, sat_z]) - np.array([rec_x, rec_y, rec_z])
    NEU = t @ ((d_xyz).T)
    Ele = math.atan(NEU[2] / math.sqrt(NEU[0] ** 2 + NEU[1] ** 2))
    Azi = math.atan(abs(NEU[1] / NEU[0]))
    if NEU[0] > 0:
        if NEU[1] <= 0:
            Azi = 2 * math.pi - Azi
    else:
        if NEU[1] > 0:
            Azi = math.pi - Azi
        else:
            Azi = math.pi + Azi

    return Ele, Azi


if __name__ == '__main__':
    print(xyz2blh([1546823.34, -3879765.13, 4804185.05]))
    print(blh2xyz([0.8584720669885771, -1.1914198187699665, 27.479064020328224]))
