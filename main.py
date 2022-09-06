# coding:utf-8
import binascii
from parsetcp import TcpStickyBag

from scapy.all import *  # 导入scapy较慢，如果无法导入，就将py文件放到scapy库，C:\Python27\Scripts\scapy-master文件夹下执行

tcp_parse = TcpStickyBag()


def mySplit3(string):
    t = string.upper()
    return ' '.join(
        [t[2 * i:2 * (i + 1)] for i in range(len(t) // 2)]
    )


# 175
def pack_callback(packet):
    if packet["TCP"].payload:  # 检测tcp负载是否有数据，有Ethernet、IP、TCP几个阶段
        tcp_code = mySplit3(str(binascii.b2a_hex(bytes(packet["TCP"].payload)))[2:-1])
        print(tcp_code)
        print(tcp_parse.bt_array.bt_array)
        # try:
        tcp_parse.push_stream(tcp_code)
        tcp_parse.pull_stream()
        # except Exception as e:
        #     print('error', e)
        # print('*' * 100)


# 嗅探数据包，参数：过滤器，回调函数，网卡，个数
ifacestr = "Realtek PCIe GbE Family Controller"  # 网口名称，这里要换成自己的网卡名称
filterstr = "host 101.91.21.39"  # 过滤条件，为空表示不限制
sniff(filter=filterstr, prn=pack_callback, iface=ifacestr, count=0)  # count等0表示一直监听，要想监听数据包，需要首先安装 winpcap
