from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np

from cal_recv_location import cal_recv_point
from read_broadcast import get_gps_data, cal_satXYZ
from read_observation import get_observation_data

if __name__ == '__main__':
    # 获取观测文件所有数据
    o1 = get_observation_data('./测点4.21O')
    o1_approx_cord = [-2615526.2208, 4732498.4359, 3371474.6413]  # 接收机近似坐标，在观测文件中获取，也可以从0开始
    # o1 = get_observation_data('./测点11.21O')
    # o1_approx_cord = [-2615422.5120, 4733126.5519, 3370663.4723]  # 接收机近似坐标，在观测文件中获取，也可以从0开始
    o2 = get_observation_data('./测点5.21O')
    o2_approx_cord = [-2615310.5308, 4732437.1085, 3371721.3689]

    # 获取星历文件所有数据
    gps_data = get_gps_data('./brdc1660.21n')

    # 指定电离层参数
    ION_alpha = [0.5588e-08, 0.1490e-07, -0.5960e-07, -0.1192e-06]
    ION_beta = [0.8397e+05, 0.9830e+05, -0.6554e+05, -0.5243e+06]

    # 实际距离
    o1_o2_D = 332.0934
    # o1_o2_D = 1268.9192
    o1_o2_acc = []
    o1_o2_acc_no_ION_delay = []

    # 获取最晚开始时间和最早结束时间
    s_date_1 = datetime.strptime(sorted(o1)[0], '%Y-%m-%d %H:%M:%S')
    e_date_1 = datetime.strptime(sorted(o1)[-1], '%Y-%m-%d %H:%M:%S')
    s_date_2 = datetime.strptime(sorted(o2)[0], '%Y-%m-%d %H:%M:%S')
    e_date_2 = datetime.strptime(sorted(o2)[-1], '%Y-%m-%d %H:%M:%S')
    if s_date_1 < s_date_2:
        s_date = s_date_2
    else:
        s_date = s_date_1
    if e_date_1 < e_date_2:
        e_date = e_date_1
    else:
        e_date = e_date_2

    time_gap = (e_date - s_date).seconds + 1  # 计算需要遍历的时间长度
    print("解算时间范围：{} 到 {}，解算时间长度：{}秒".format(s_date, e_date, time_gap))

    with open('visible_satellite_position.txt', 'w') as f:  # 输出观测时段内的可见卫星坐标
        for s in range(time_gap):  # 遍历所有时间范围
            date = s_date + timedelta(seconds=s)
            sat_location = cal_satXYZ(gps_data, date)

            f.write('Date (UTC): %s\n' % str(date))  # 输出观测时间点

            # 计算接收机每个时间点的位置
            try:
                o1_date = o1[str(date)]  # 提取指定时间点的伪距
                o2_date = o2[str(date)]
            except:
                continue

            o1_satID = []  # 接收机观测卫星PRN
            o1_satRange = []  # 接收机对应卫星伪距
            o1_sat_cord_dt = []  # 接收机对应卫星坐标和钟偏差
            o2_satID = []
            o2_satRange = []
            o2_sat_cord_dt = []

            for key in o1_date.keys():
                if key[1] == '0':
                    PRN_ = key[2:]
                else:
                    PRN_ = key[1:]
                o1_satID.append(PRN_)  # 提取观测卫星序号
                o1_satRange.append(o1_date[key])  # 提取伪距
                o1_sat_cord_dt.append(sat_location[PRN_])  # 计算指定观测卫星的坐标
                f.write('PRN: %s  XYZ & dt: %s\n' % (str(key), str(sat_location[PRN_])))  # 输出卫星坐标和钟差
            f.write('\n')

            for key in o2_date.keys():
                if key[1] == '0':
                    PRN_ = key[2:]
                else:
                    PRN_ = key[1:]
                o2_satID.append(PRN_)  # 提取观测卫星序号
                o2_satRange.append(o2_date[key])  # 提取伪距
                o2_sat_cord_dt.append(sat_location[PRN_])  # 计算指定观测卫星的坐标

            t_GPS = date.hour * 3600 + date.minute * 60 + date.second
            try:  # 尝试解算接收机坐标，如果 结果发散 或 可用卫星数不足 则弃用本次观测记录
                o1_XYZ = cal_recv_point(o1_sat_cord_dt, o1_approx_cord, o1_satRange, t_GPS,  # 启用截止高度角限制，启用电离层修正
                                        ION_alpha, ION_beta, True, True)
                o2_XYZ = cal_recv_point(o2_sat_cord_dt, o2_approx_cord, o2_satRange, t_GPS,
                                        ION_alpha, ION_beta, True, True)

                # 计算无电离层延迟修正、无截止高度角时的坐标
                o1_XYZ_noID = cal_recv_point(o1_sat_cord_dt, o1_approx_cord, o1_satRange, t_GPS,  # 禁用截止高度角限制，禁用电离层修正
                                             ION_alpha, ION_beta, False, False)
                o2_XYZ_noID = cal_recv_point(o2_sat_cord_dt, o2_approx_cord, o2_satRange, t_GPS,
                                             ION_alpha, ION_beta, False, False)
            except:
                continue

            o1_o2_d = np.sqrt(np.sum((o1_XYZ - o2_XYZ) ** 2))  # 计算距离
            o1_o2_d_noID = np.sqrt(np.sum((o1_XYZ_noID - o2_XYZ_noID) ** 2))
            o1_o2_acc.append((o1_o2_d - o1_o2_D) / o1_o2_D)  # 计算相对误差
            o1_o2_acc_no_ION_delay.append((o1_o2_d_noID - o1_o2_D) / o1_o2_D)
            print("解算时间：{}，接收机1坐标：{}，接收机2坐标：{}，距离：{}".format(date, o1_XYZ, o2_XYZ, o1_o2_d))

    plt.figure(1)
    plt.plot([0.05 for _ in range(len(o1_o2_acc))], 'k--', label="5% Indicators")  # 绘制5%水平线
    plt.plot([-0.05 for _ in range(len(o1_o2_acc))], 'k--')
    plt.plot(o1_o2_acc_no_ION_delay, color='grey', linestyle='-', label="Without Any Correction")
    plt.plot(o1_o2_acc, color='k', linestyle='-', label="With ION and Cut-off Elevation Angle Correction")
    plt.legend(loc='upper right')
    plt.xlabel('Time Series (Seconds)')
    plt.ylabel('Error Ratios (*100%)')
    plt.savefig(fname="Error_Ratios.svg", format="svg")
    plt.show()
