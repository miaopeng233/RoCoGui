# -*- coding: utf8 -*-
import zlib
import miniamf


class Config:
    def __init__(self, ):
        self.SPIRIT_CONFIG = {}  # 宠物id组
        self.SPIRIT_SKILL_CONFIG = {}  # 技能id组
        self.decode()

    def decode(self):
        """
            解析 Config 文件
        :return:
        """
        with open('static/Angel.config', 'rb') as f:
            _lo2_ = int.from_bytes(f.read(1), byteorder='big', signed=True)
            _lo3_ = int.from_bytes(f.read(4), byteorder='big', signed=False)
            _lo4_ = int.from_bytes(f.read(2), byteorder='big', signed=True)
            for i in miniamf.decode(zlib.decompress(f.read())):
                if i.tag == "SpiritConfig":
                    self.spirit_config(i)
                elif i.tag == "SpiritSkillConfig":
                    self.spirit_skill_config(i)

    def spirit_config(self, data):
        """
            解析宠物资源
        :return:
        """
        for i in data:
            if int(i.attrib['id']) > 10000:
                continue
            self.SPIRIT_CONFIG[i.attrib['id']] = i.attrib

    def spirit_skill_config(self, data):
        """
            解析技能信息
        :return:
        """
        for i in data:
            if i.tag != "SpiritSkillDes" or int(i.attrib['id']) >= 10000:
                continue
            self.SPIRIT_SKILL_CONFIG[i.attrib['id']] = i.attrib


if __name__ == '__main__':
    pass
    # c = Config()
    # print(c.SPIRIT_SKILL_CONFIG.get("1771"))
