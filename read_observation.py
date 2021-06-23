import re
from datetime import datetime


def get_observation_data(o_file_path):  # 获取整个星历文件数据
    o_data_dict = {}

    line1 = ['年月日时分秒']
    line2 = ['PRN', '伪距']

    with open(o_file_path, 'r') as o_f:
        hearder_end = 0
        PRN = []
        persudo_range = []

        for line in o_f.readlines():
            if 'END OF HEADER' in line:
                hearder_end = 1
                continue
            if hearder_end:
                if line[0] == '>':  # 如果某一行第一个字符为空，即当前为观测时间行
                    # 获取观测时间数据
                    raw_data = re.sub(' +', ' ', line[2:])
                    raw_data = raw_data.split(' ')
                    # second = line[19:21]
                    date_str = '{}-{}-{} {}:{}:{}'.format(raw_data[0], raw_data[1], raw_data[2],
                                                          int(raw_data[3]), raw_data[4], raw_data[5].split('.')[0])
                    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    continue
                elif line[0] == 'G':  # 如果当前行第一个字符为G，则为GPS数据行
                    raw_data = re.sub(' +', ' ', line)
                    raw_data = raw_data.split(' ')
                    PRN.append(raw_data[0])
                    persudo_range.append(float(raw_data[1]))
                else:  # 保存上一个观测时间段获取的数据
                    if len(PRN) != 0:
                        o_data_dict[str(date)] = dict(zip(PRN, persudo_range))
                        PRN = []
                        persudo_range = []

    return o_data_dict


if __name__ == '__main__':
    o_dict = get_observation_data('./第三组.20o')
    print(o_dict)
