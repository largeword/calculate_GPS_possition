import math
from datetime import datetime


# 获取星历文件中距离目标日期最近的日期
def find_closest_date(sat_dict, date):
    dates = sorted(sat_dict)
    gap = 1e8
    for i, date_ in enumerate(dates):
        date_ = datetime.strptime(date_, '%Y-%m-%d %H:%M:%S')
        gap_ = math.fabs((date_ - date).days*24*3600 + (date_ - date).seconds)
        if gap_ < gap:
            gap = gap_
            continue
        elif gap_ > gap:
            return dates[i-1]


# 获取第一行数据
def get_line1_data(line):
    line_ = line[2:]  # 去除PRN号
    line1_split = line_.split(' ')  # 分割时间
    idx = 0
    for i in line1_split:
        if i == '':
            continue
        else:
            idx = idx + 1
            if idx == 1:
                year = 2000 + int(i)
                continue
            elif idx == 2:
                month = int(i)
                continue
            elif idx == 3:
                day = int(i)
                continue
            elif idx == 4:
                hour = int(i)
                continue
            elif idx == 5:
                min = int(i)
                continue
            elif idx == 6:
                if len(i) > 5:
                    sec = i.split('-')[0]
                    sec = round(float(sec))
                else:
                    sec = round(float(i))
                break
    sat_date = datetime(year, month, day, hour, min, sec)
    sat_clock_dev = float(line[22:41].replace('D', 'E', 1))
    sat_clock_drift = float(line[41:60].replace('D', 'E', 1))
    sat_clock_drift_speed = float(line[60:79].replace('D', 'E', 1))
    return [sat_date, sat_clock_dev, sat_clock_drift, sat_clock_drift_speed]


# 获取第二到八行数据
def get_line2_8_data(line):
    data1 = float(line[3:22].replace('D', 'E', 1))
    data2 = float(line[22:41].replace('D', 'E', 1))
    data3 = float(line[41:60].replace('D', 'E', 1))
    data4 = float(line[60:79].replace('D', 'E', 1))
    return [data1, data2, data3, data4]


# 获取整个星历文件数据
def get_gps_data(gps_file_path):
    gps_data_dict = {}

    line1 = ['PRN', '年月日时分秒', '卫星钟偏差', '卫星钟漂移', '卫星钟漂移速度']
    line2 = ['IODE', 'C_rs', 'Delta_n', 'M_0']
    line3 = ['C_uc', 'e', 'C_us', 'A_sqrt']
    line4 = ['TOE', 'C_ic', 'Omega_0', 'C_is']
    line5 = ['i_0', 'C_rc', 'omega', 'Omega_Dot']
    line6 = ['i_Dot', 'L2', 'GPS_week', 'L2_P']
    line7 = ['卫星精度', '卫星健康状态', 'TGD', 'IODC']
    line8 = ['电文发送时刻', '拟合区间']
    XYZ = ['X', 'Y', 'Z']
    with open(gps_file_path, 'r') as gps_f:
        hearder_end = 0
        sat_num = -1
        for line in gps_f.readlines():
            if 'END OF HEADER' in line:
                hearder_end = 1
                continue
            if hearder_end:  # 判断当前行是否属于头文件
                if line[1] == ' ':  # 如果某一行第二个字符为空，即数据行在2-8行
                    count_line = count_line + 1

                    # 按不同卫星数据的行序号读取信息
                    if count_line == 2:
                        data2 = get_line2_8_data(line)
                        continue
                    elif count_line == 3:
                        data3 = get_line2_8_data(line)
                        continue
                    elif count_line == 4:
                        data4 = get_line2_8_data(line)
                        continue
                    elif count_line == 5:
                        data5 = get_line2_8_data(line)
                        continue
                    elif count_line == 6:
                        data6 = get_line2_8_data(line)
                        continue
                    elif count_line == 7:
                        data7 = get_line2_8_data(line)
                        continue
                    elif count_line == 8:  # 读取最后一行，需要封装数据字典
                        data8 = get_line2_8_data(line)[0:2]

                        line_all = line1 + line2 + line3 + line4 + line5 + line6 + line7 + line8
                        data_all = data1 + data2 + data3 + data4 + data5 + data6 + data7 + data8
                        line_all = line_all[2:]
                        data_all = data_all[2:]

                        data_dict = dict(zip(line_all, data_all))  # 封装数据项字典
                        time_dict = dict(zip([str(time)], [data_dict]))  # 封装日期字典

                        # 判断字典中是否存在当前卫星序号的数据
                        if str(sat_num) in gps_data_dict.keys():  # 如果存在则追加日期字典数据
                            gps_data_dict[str(sat_num)][str(time)] = data_dict
                        else:
                            gps_data_dict[str(sat_num)] = time_dict
                        continue
                else:  # 如果某一行第二个字符不为空，即数据行在1行
                    if line[0] != ' ':
                        sat_num = int(line[0]) * 10 + int(line[1])
                    else:
                        sat_num = int(line[1])
                    count_line = 1
                    data1 = [sat_num] + get_line1_data(line)
                    time = data1[1]
    return gps_data_dict


# 解算指定时间的卫星坐标
def cal_satXYZ(sat_data_all, date):
    # WGS-84基本参数
    Omega_e = 7.2921151467e-5  # 地球自转角速度（rad/s）
    mu = 3.986005e14  # 地球引力常数GM（m^3/s^2）

    sat_ID = []
    XYZ_dt = []
    for key in sat_data_all.keys():  # 按照卫星序号读取数据
        sat_ID.append(key)
        closest_date = find_closest_date(sat_data_all[key], date)  # 寻找距离指定日期最近的星历文件日期
        closest_date_ = datetime.strptime(closest_date, '%Y-%m-%d %H:%M:%S')
        sat_data = sat_data_all[key][closest_date]

        # 星历参数
        date=date
        t_oe=sat_data['TOE']
        A_sqrt=sat_data['A_sqrt']
        e=sat_data['e']
        i_0=sat_data['i_0']
        Omega_0=sat_data['Omega_0']
        omega=sat_data['omega']
        M_0=sat_data['M_0']
        Delta_n=sat_data['Delta_n']
        i_Dot=sat_data['i_Dot']
        Omega_Dot=sat_data['Omega_Dot']
        C_uc=sat_data['C_uc']
        C_us=sat_data['C_us']
        C_rc=sat_data['C_rc']
        C_rs=sat_data['C_rs']
        C_ic=sat_data['C_ic']
        C_is=sat_data['C_is']
        dt=sat_data['卫星钟偏差']

        # 计算规化时间
        A = A_sqrt ** 2  # 卫星轨道半长轴

        # 距周日0点的秒数
        #t = (date.weekday()+1) * 24 * 3600 + int(date.hour) * 3600 + int(date.minute) * 60 + int(date.second)
        #t_k = t - t_oe

        if (date - closest_date_).days*24*3600 + (date - closest_date_).seconds > 7200:  # 判断解算指定时间是否超出2小时
            raise ValueError("指定时间距离星历文件最近时间太远，超出两小时")
        t_k = (date - closest_date_).days*24*3600 + (date - closest_date_).seconds
        if t_k > 302400:
            t_k -= 604800
        if t_k < -302400:
            t_k += 604800
        #print("t_k={}".format(t_k))

        # 计算校正后的卫星平均角速度
        n_0 = math.sqrt(mu / A ** 3)  # 卫星平均角速度
        n = n_0 + Delta_n  # 校正后的卫星平均角速度
        #print("n={}".format(n))

        # 平近点角
        M_k = M_0 + n * t_k
        '''
        if M_k < 0:
            M_k += 2 * math.pi
        if M_k > 2 * math.pi:
            M_k -= 2 * math.pi
            '''
        #print("M_k={}".format(M_k))

        # 偏近点角
        E_old = M_k
        E_new = M_k + e * math.sin(E_old)
        i = 1
        while abs(E_new - E_old) > 1e-8:
            #print("i={},E={}".format(i, E_new))
            E_old = E_new
            E_new = M_k + e * math.sin(E_old)
            i += 1
            if (i > 10):
                break
        E_k = E_new
        #print("E_k={}".format(E_k))

        # 真近点角
        cosNu_k = (math.cos(E_k) - e) / (1 - e * math.cos(E_k))
        sinNu_k = (math.sqrt(1 - e ** 2) * math.sin(E_k)) / (1 - e * math.cos(E_k))
        #print("cosNu_k={}".format(cosNu_k))
        #print("sinNu_k={}".format(sinNu_k))
        if cosNu_k == 0:
            if sinNu_k > 0:
                Nu_k = math.pi / 2
            else:
                Nu_k = -math.pi / 2
        else:
            Nu_k = math.atan(sinNu_k / cosNu_k)
        if cosNu_k < 0:
            if sinNu_k >= 0:
                Nu_k += math.pi
            else:
                Nu_k -= math.pi
        #Nu_k = math.atan(sinNu_k / cosNu_k)
        Nu_k = math.atan2((math.sqrt(1 - e ** 2) * math.sin(E_k)), (math.cos(E_k) - e))
        #print("Nu_k={}".format(Nu_k))

        # 计算升交点角距
        Phi_k = Nu_k + omega
        #print("Phi_k={}".format(Phi_k))

        # 计算摄动校正后的升交点角距、卫星矢径长度、轨道倾角
        delta_u_k = C_us * math.sin(2 * Phi_k) + C_uc * math.cos(2 * Phi_k)
        delta_r_k = C_rs * math.sin(2 * Phi_k) + C_rc * math.cos(2 * Phi_k)
        delta_i_k = C_is * math.sin(2 * Phi_k) + C_ic * math.cos(2 * Phi_k)
        #print("delta_u_k={}".format(delta_u_k))
        #print("delta_r_k={}".format(delta_r_k))
        #print("delta_i_k={}".format(delta_i_k))
        u_k = Phi_k + delta_u_k
        r_k = A * (1 - e * math.cos(E_k)) + delta_r_k
        i_k = i_0 + i_Dot * t_k + delta_i_k
        #print("u_k={}".format(u_k))
        #print("r_k={}".format(r_k))
        #print("i_k={}".format(i_k))

        # 坐标转换
        x_p_k = r_k * math.cos(u_k)
        y_p_k = r_k * math.sin(u_k)
        #print("x_p_k={}".format(x_p_k))
        #print("y_p_k={}".format(y_p_k))
        Omega_k = Omega_0 + (Omega_Dot - Omega_e) * t_k - Omega_e * t_oe
        #print("Omega_k={}".format(Omega_k))
        x_k = x_p_k * math.cos(Omega_k) - y_p_k * math.cos(i_k) * math.sin(Omega_k)
        y_k = x_p_k * math.sin(Omega_k) + y_p_k * math.cos(i_k) * math.cos(Omega_k)
        z_k = y_p_k * math.sin(i_k)
        #print("x_k={}".format(x_k))
        #print("y_k={}".format(y_k))
        #print("z_k={}".format(z_k))
        XYZ_dt.append([x_k, y_k, z_k, dt])  # dt为卫星钟差

    return dict(zip(sat_ID, XYZ_dt))


if __name__ == '__main__':
    gps_file = './brdc3030.20n'  # 读取文件路径

    # 设定要提取的卫星编号和对应日期
    sat_list = [6, 13, 21]
    date_list = ['2012-1-18 14:29:36', '2012-1-18 14:29:36', '2012-1-18 14:29:36']

    # 读取一整个星历文件到字典
    gps_data_dict = get_gps_data(gps_file)

    for i, sat_num in enumerate(sat_list):
        print("****************PRN: {}, date: {}, 参数如下****************".format(str(sat_num), date_list[i]))
        cal_satXYZ(gps_data_dict[sat_num], date_list[i])

    #cal_XYZ(gps_data_dict, 6, '2012-1-18 0:0:0')