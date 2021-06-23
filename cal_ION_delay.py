import math


def semi2deg(semi):  # semicircles转角度（度）
    return semi * 180


def deg2semi(deg):  # 角度（度）转semicircles
    return deg / 180


def semi2rad(semi):  # semicircles转角度（弧度）
    return semi * math.pi


def rad2semi(rad):  # 角度（弧度）转semicircles
    return rad / math.pi


def cal_ION_delay(Ele, Azi, lat, lon, t_GPS, ION_alpha, ION_beta):
    """
    :param Ele: 卫星高度角，单位弧度
    :param Azi: 卫星方位角，单位弧度
    :param lat: 接收机纬度，单位弧度，等于BLH坐标系中的B
    :param lon: 接收机经度，单位弧度，等于BLH坐标系中的L
    :param t_GPS: GPS时间，单位秒
    :param ION_alpha: 广播星历电离层参数1，输入数组
    :param ION_beta: 广播星历电离层参数2，输入数组
    :return: 电离层延迟，单位秒；伪距改正数，单位米
    """
    c = 299792458  # 定义光速

    phi = 0.0137 / (rad2semi(Ele) + 0.11) - 0.022

    phi_I = rad2semi(lat) + phi * math.cos(Azi)
    if phi_I > 0.416:
        phi_I = 0.416
    elif phi_I < -0.416:
        phi_I = -0.416

    lam_I = rad2semi(lon) + phi * math.sin(Azi) / math.cos(semi2rad(phi_I))
    phi_m = phi_I + 0.064 * math.cos(semi2rad(lam_I) - 1.617)

    t = 43200 * lam_I + t_GPS
    if t > 86400:
        t = t - 86400
    elif t < 0:
        t = t + 86400

    '''
    A_I = 0
    for i in range(4):
        A_I += ION_alpha[i] * (phi_m ** i)
    if A_I < 0:
        A_I = 0
    '''

    P_I = 0
    for i in range(4):
        P_I += ION_beta[i] * (phi_m ** i)
    if P_I < 72000:
        P_I = 72000

    X_I = 2 * math.pi * (t - 50400) / P_I
    F = 1.0 + 16.0 * ((0.53 - rad2semi(Ele)) ** 3)

    if abs(X_I) <= 1.57:
        sum_i = 0
        for i in range(4):
            sum_i += ION_alpha[i] * (phi_m ** i)
        I_L1GPS = F * (5e-9 + sum_i * (1 - (X_I ** 2) / 2 + (X_I ** 4) / 24))
    else:
        I_L1GPS = F * 5e-9

    return I_L1GPS, c * I_L1GPS


if __name__ == '__main__':
    print(deg2semi(7.2))
    print(semi2deg(0.215))
    print(cal_ION_delay(20, 210, 40, -100, 2045, [3.82e-8, 1.49e-8, -1.79e-7, 0], [1.42e5, 0, -3.28e5, 1.13e5]))
