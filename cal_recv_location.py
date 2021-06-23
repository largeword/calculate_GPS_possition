import math

import numpy as np

import cal_Elevation_Zenith_Angle
import cal_ION_delay


# 计算测站位置
def cal_recv_point(sat_location_dt, init_point, persudo_range, t_GPS, ION_alpha, ION_beta, use_AltAngleCorrection=False,
                   use_IonDelayCorrection=False):
    """
    :param t_GPS: 信号接收的GPS时间，单位秒
    :param ION_alpha: 广播星历电离层参数1，输入数组
    :param ION_beta: 广播星历电离层参数2，输入数组
    :param sat_location_dt: 卫星坐标和钟差，输入数组
    :param init_point: 接收机大致坐标，输入数组
    :param persudo_range: 接收机和对应卫星的伪距，输入数组
    :param use_AltAngleCorrection: 是否使用截止高度角，默认否
    :param use_IonDelayCorrection: 是否使用电离层延迟修正，默认否
    :return: 接收机精确坐标，输出数组
    """

    persudo_range = np.array(persudo_range)  # 接收机伪距
    is_valid = (persudo_range > 1e6)  # 检查伪距数值是否大于10^6米
    persudo_range = persudo_range[is_valid]

    sat_location_dt = np.array(sat_location_dt)[is_valid]
    sat_location = sat_location_dt[:, :-1]  # 卫星坐标
    init_xyz = np.array(init_point)  # 初始迭代坐标，可随意设置
    approx_revXYZ = init_xyz.copy()
    init_xyz = np.tile(init_xyz, (sat_location.shape[0], 1))

    dt = sat_location_dt[:, -1]  # 卫星种偏差
    c = np.array([299792458])  # 光速
    c_dt1 = 0

    point_previous = np.zeros((4, 1))

    i = 0
    while True:
        i += 1
        # 计算站星距
        rou0_j = np.sqrt(np.sum((sat_location - init_xyz) ** 2, axis=1)).reshape(-1, 1)

        # 计算A
        # one = np.ones((sat_location.shape[0], 1)) * -1
        one = np.ones((sat_location.shape[0], 1))
        A = np.concatenate(((sat_location - init_xyz) / np.tile(rou0_j, (1, sat_location.shape[1])), one), axis=1)

        # 是否使用电离层延迟修正
        dis_corr = np.zeros(sat_location.shape[0])
        if use_IonDelayCorrection:
            # 电离层缩短信号传播时间，应该加上改正距离，而不是相减
            Ele = np.zeros(sat_location.shape[0])
            Azi = np.zeros(sat_location.shape[0])
            for i, sat_cord in enumerate(sat_location):
                Ele[i], Azi[i] = cal_Elevation_Zenith_Angle.cal_E_A(init_xyz[0, 0], init_xyz[0, 1], init_xyz[0, 2],
                                                                    sat_cord[0], sat_cord[1], sat_cord[2])
                B, L, _ = cal_Elevation_Zenith_Angle.xyz2blh(approx_revXYZ)
                _, dis_corr[i] = cal_ION_delay.cal_ION_delay(Ele[i], Azi[i], B, L, t_GPS, ION_alpha, ION_beta)
        else:
            Ele = np.zeros(sat_location.shape[0])
            Azi = np.zeros(sat_location.shape[0])
            for i, sat_cord in enumerate(sat_location):
                Ele[i], Azi[i] = cal_Elevation_Zenith_Angle.cal_E_A(init_xyz[0, 0], init_xyz[0, 1], init_xyz[0, 2],
                                                                    sat_cord[0], sat_cord[1], sat_cord[2])

        # 检查是否需要进行卫星高度角修正
        if use_AltAngleCorrection:
            is_use = ((math.pi / 6) < Ele)  # 弃用高度角过小的卫星，设置截止角度为30°
            if np.sum(is_use == True) < 8:
                raise ValueError("截止高度角限制导致可用卫星数不足8个")
        else:
            is_use = np.ones(A.shape[0]) == 1

        A = A[is_use]

        # 计算L
        L = rou0_j[is_use].reshape(-1, 1) - persudo_range[is_use].reshape(-1, 1) - \
            np.tile(c, (A.shape[0], 1)).reshape(-1, 1) * dt[is_use].reshape(-1, 1) + \
            np.tile(c_dt1, (A.shape[0], 1)).reshape(-1, 1) - dis_corr[is_use].reshape(-1, 1)

        # 计算坐标
        # d_point = np.dot(np.linalg.pinv(A.T @ A), (A.T @ L)).reshape(4, 1)
        d_point = (np.linalg.pinv(A.T @ A) @ (A.T @ L)).reshape(4, 1)
        point = init_xyz[0, :3].reshape(3) + d_point[:3].reshape(3)
        c_dt1 = c_dt1 + d_point[3]

        dd = np.sum((point - point_previous) ** 2)  # 计算迭代差值
        if dd <= 0.001:
            init_xyz = point
            break
        elif i > 1e4:  # 超过最大迭代次数视为结果无法收敛
            raise ValueError("位置结算结果发散")
        else:
            point_previous = point
            init_xyz = np.tile(point[:3].reshape((3)), (sat_location.shape[0], 1))

    return init_xyz
