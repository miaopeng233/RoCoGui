# -*- coding: utf8 -*-
"""
    粘包半包处理
"""
import binascii
from unconfig import Config

CONFIG = Config()


class Dict(dict):
    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, name):
        self[key] = name


class ADFHead:
    def __init__(self, b):
        self.version = b.readUnsignedShort()
        self.cmdID = b.readUnsignedInt()
        self.uin = b.readUnsignedInt()
        self.uiSerialNum = b.readUnsignedInt()
        self.checkSum = b.readUnsignedShort()
        self.length = b.readUnsignedShort()


class TcpStickyBag:
    def __init__(self, ):
        self.bt_array = BtArray()
        self.head = None  # ADFHead
        self.mapper = {
            196629: 查询用户详细信息,
            720900: 发招,
            720897: 战斗,
            # 720899: 请求战斗,
            720904: ReqAllMovieEndP,
        }

    def read_head(self):
        """
            读包头 没包头时读包头 不够读包头制空
        :return:
        """
        # 有包头 不需要处理
        if self.head:
            return
        # 如果没有包头 先读到 正确的包头开始
        while len(self.bt_array) > 20:
            # 第一个字节 和第二个字节 是 95 和 27 时
            if self.bt_array.bt_array[0] == "95" and self.bt_array.bt_array[1] == '27':
                self.bt_array.readUnsignedShort()
                # 读包头
                self.head = ADFHead(self.bt_array)
                return
            else:
                # 去掉脏数据
                self.bt_array.readByte()

    def read_body(self, length: int):
        """
            读出包体
        :return:
        """
        res = self.bt_array.bt_array[:length]
        self.bt_array.bt_array = self.bt_array.bt_array[length:]
        return res

    def push_stream(self, stream: str):
        """
            流入 进制流
        :param stream: 进制流
        :return:
        """
        self.bt_array.extend(stream.strip().split(' '))

    def pull_stream(self):
        """
            流出 进制流
        :return:
        """
        while True:
            # 现在没有包头 也不够读出包头
            self.read_head()
            if not self.head:
                return
            # 包体够长
            if len(self.bt_array) >= self.head.length:
                # 获取包头信息 并 清除包头 防止处理函数报错
                length = self.head.length
                cmd_id = self.head.cmdID
                self.head = None
                # 执行处理函数
                self.commit(self.read_body(length), cmd_id)
            # 包体不够长
            else:
                # 返回数据
                return

    def commit(self, bit_list, cmd_id):
        """
            分析执行处理函数
        :return:
        """
        fun = self.mapper.get(cmd_id)
        if fun:
            print(f"调用 {fun.__name__} 函数解析")
            fun(BtArray(bit_list))
        else:
            print("没有对应的解析函数")


class BtArray:
    def __init__(self, bit_list: list = None):
        if bit_list is None:
            bit_list = []
        self.bt_array = bit_list

    def __len__(self):
        return len(self.bt_array)

    def extend(self, bit_list: list):
        self.bt_array.extend(bit_list)

    def readByte(self):
        """
            读取 有符号字节 一个
        :return:
        """
        val = int(self.byte_read(1), 16)
        if val & (1 << (16 - 1)):
            val -= 1 << 16
        return val

    def byte_read(self, length: int):
        """
            读出字节数
        :param length: 读出字节数
        :return: 返回字节
        """
        res = self.bt_array[:length]
        self.bt_array = self.bt_array[length:]
        return ''.join(res)

    def readShort(self):
        """
            读取有符号
        :return:
        """
        val = int(self.byte_read(2), 16)
        if val & (1 << (16 - 1)):
            val -= 1 << 16
        return val

    def readInt(self):
        val = int(self.byte_read(4), 16)
        if val & (1 << (16 - 1)):
            val -= 1 << 16
        return val

    def readUnsignedByte(self):
        """
            读取一个字节
        :return: 返回字节
        """
        return int(self.byte_read(1), 16)

    def readUnsignedShort(self):
        """
            返回一个整数
        :return:
        """
        return int(self.byte_read(2), 16)

    def readUnsignedInt(self):
        return int(self.byte_read(4), 16)

    def readMultiByte(self, length: int, charset: str = 'gbk'):
        """
            字符串解码
        :param length: 长度
        :param charset: 编码格式
        :return: 字符串
        """
        hex_str = self.byte_read(length)
        str_bin = binascii.unhexlify(hex_str.encode(charset))
        return str_bin.decode(charset)


class Define:
    @staticmethod
    def ReadIP(par: BtArray):
        """
            获取 ip
        :return:
        """
        v = par.readUnsignedInt()
        return f"{v & 255}.{int(v >> 8) & 255}.{int(v >> 16) & 255}.{int(v >> 24) & 255}"

    @staticmethod
    def ReadString(par: BtArray):
        v: int = par.readUnsignedShort()
        return par.readMultiByte(v)

    @staticmethod
    def ReadChars(par: BtArray, param2: int):
        """
            读一个字符
        :param par: 字节对象
        :param param2: 长度
        :return:
        """
        return par.readMultiByte(param2)


class PReturnCode:
    @staticmethod
    def readExternal(b: BtArray):
        """
            读 code
        :return:
        """
        code = b.readInt()
        _lo2_ = b.readUnsignedShort()
        # print('code', code)
        # print('_lo2_', _lo2_)


# class

class SpiritDes:
    """
        宠物 des 信息
    """

    def __init__(self):
        self.STATE_NORMAL: int = 0
        self.STATE_HOT: int = 1
        self.STATE_NEW: int = 2
        self.id: int = 0
        self.name: str = ""
        self.features: list = []
        self.src: str = ""
        self.avatar: str = ""
        self.iconSrc: str = ""
        self.previewSrc: str = ""
        self.linkName: str = ""
        self.mType: int = 0
        self.mSpeed: int = 3
        self.description: str = ""
        self.height: str = ""
        self.weight: str = ""
        self.color: str = ""
        self.interest: str = ""
        self.habitat: str = ""
        self.evolution: str = ""
        self.evolutionLevel: int = 0
        self.evolutionID: int = 0
        self.catchrate: int = 0
        self.group: list = []
        self.bossPhyle: str = ""
        self.bossReward: str = ""
        self.sceneId: int = 0
        self.condition: str = ""
        self.requireLevel: str = ""
        self.wg: int = 0
        self.mg: int = 0
        self.mk: int = 0
        self.sm: int = 0
        self.sd: int = 0
        self.fy: int = 0
        self.EvolutionFormID: int = 0
        self.EvolutiontoIDs: list = []
        self.getForm: str = ""
        self.state: int = 0
        self.startTime: str = ""
        self.endTime: str = ""
        self.firstID: int = 0
        self.propoLevel: int = -1
        self.isInBook: bool = True
        self.expType: int = 0
        self.reward: int = 0


class ObjCombatInfo:
    def __init__(self):
        self.type: int = 0
        self.id: int = 0
        self.nickName: str = ""
        self.cIndex: int = 0
        self.spirits: list = []
        self.guardianPetEnergy: int = 0
        self.guardianPetAttack: int = 0
        self.guardianPetDefend: int = 0
        self.guardianPetMA: int = 0
        self.guardianPetMD: int = 0
        self.loadProgress: int = 0


class CombatData:
    def __init__(self):
        # self.changeSpiritHandler: Function
        self.canCombat = 0
        # self.myCurSpirit: SpiritInfo
        # self.rivalCurSpirit: SpiritInfo
        # self.changeRivalSpirit: SpiritInfo
        self.code = PReturnCode()  # 实例化
        self.combatType = 0  # combatType
        # self.changeMySpririt: SpiritInfo
        self.pkID = 0
        # self.rivalInfo = ObjCombatInfo()
        # self.myInfo = ObjCombatInfo()


class SpiritEquipmentDes:
    """
        装备设计
    """

    def __init__(self):
        self.id: int = 0
        self.type: int = 0
        self.level: int = 0
        self.cdtLevel: int = 0
        self.name: str = ''
        self.getFrom: str = ''
        self.price: list = []
        self.src: str = ''


class SpiritEquipmentInfo:
    """
        装备信息
    """

    def __init__(self):
        self.id: int = 0
        self.type: int = 0
        self.quality: int = 0
        self.price: int = 0
        self.baseAttr: int = 0
        self.baseValue: int = 0
        self.specialAttr: int = 0
        self.specialValue: int = 0
        self._serverID: int = 0
        self.catchTime: int = 0
        self.des: SpiritEquipmentDes = SpiritEquipmentDes()
        self.spiritID: int = 0
        self.spiritCatchTime: int = 0
        self.selectValue: int = 0


class SpiritInfo:
    """
        宠物信息
    """

    def __init__(self):
        self.index: int = 0
        self.id: int = 0
        self.level: int = 0
        self.sex: int = 0
        self.curHP: int = 0
        self.maxHP: int = 0
        self.skills: list = []
        self.spiritDes: SpiritDes = SpiritDes()
        self.equips: list = []
        self.superFormId: int = 0
        self.closeness: int = 0
        self.affiliation: int = 0


class SpiritInfoEx(SpiritInfo):
    """
        宠物信息 EX
    """

    def __init__(self):
        super(SpiritInfoEx, self).__init__()
        self.talentLevel: int = 0
        self.talentType: int = 0


class PropertyDes:
    """
        属性设计
    """

    def __init__(self):
        self.FEATURES: list = []
        self.BUFFS: list = []
        self.GroupTypes: list = []
        self.TEMPERS: list = [
            "孤僻", "固执", "调皮", "勇敢", "大胆", "淘气", "无虑", "悠闲", "保守", "稳重", "马虎", "冷静", "沉着", "温顺", "慎重", "狂妄", "胆小", "急躁",
            "开朗", "天真", "坦率", "害羞", "认真", "实干", "浮躁"
        ]
        self.TEMPER_DES: list = [
            ["攻击", "防御"], ["攻击", "魔攻"], ["攻击", "魔防"], ["攻击", "速度"], ["防御", "攻击"], ["防御", "魔攻"],
            ["防御", "魔防"], ["防御", "速度"], ["魔攻", "攻击"], ["魔攻", "防御"], ["魔攻", "魔防"], ["魔攻", "速度"],
            ["魔防", "攻击"], ["魔防", "防御"], ["魔防", "魔攻"], ["魔防", "速度"], ["速度", "攻击"], ["速度", "防御"],
            ["速度", "魔攻"], ["速度", "魔防"], ["属性不变"], ["属性不变"], ["属性不变"], ["属性不变"], ["属性不变"]
        ]
        self.EQUIPMENT_PROPETY: list = []
        self.EQUIPMENT_TYPE: list = ["武器", "防具", "饰品"]
        self.id: int = 0
        self.name: str = ""


class SpiritSkillDes:
    """
        宠物详情
    """

    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.description: str = ""
        self.description2: str = ""
        self.power: str = ""
        self.ppMax: int = 0
        self.src: str = ""
        self.property: PropertyDes = PropertyDes()
        self.attackType: int = 0
        self.linkName: str = ""
        self.speed: int = 0
        self.damageType: int = 0
        self.superSkillBgSrc: str = ""
        self.catchRate: int = 0
        self.superFormId: int = 0
        self.superFormSrc: str = ""


class SpiritSkillInfo:
    """
        宠物信息
    """

    def __init__(self):
        self.id: int = 0
        self.ppLeft: int = 0
        self.isHeredity: int = 0
        self.skillDes: SpiritSkillDes = SpiritSkillDes()


class PReadHelp:
    @staticmethod
    def readSpiritInfo(b: BtArray, param2: int, param3: bool = False):
        # _loc8_: SpiritEquipmentInfo = SpiritEquipmentInfo()  # 宠物装备信息
        _loc8_ = {}
        _loc10_: int = 0
        _loc11_: int = 0
        # __loc4__: SpiritInfoEx = SpiritInfoEx()
        __loc4__ = {
            'index': param2 + 1,  # 索引
            'id': b.readUnsignedInt(),  #
            'level': b.readUnsignedByte(),  # 等级
            'sex': b.readUnsignedByte(),  # 性别
            'curHP': b.readUnsignedShort(),  # 血量
            'maxHP': b.readUnsignedShort()  # 最大血量
        }

        _loc6_: int = b.readUnsignedShort()
        __loc4__['closeness'] = _loc6_ & 127
        __loc4__['affiliation'] = _loc6_ >> 7 & 7

        _loc7_: int = 0
        if (_loc7_ := b.readUnsignedShort()) > 0:
            __loc4__['skills'] = []  # 技能
            _loc10_ = 0
            while _loc10_ < _loc7_:
                __loc4__['skills'].append(
                    # 又一层
                    PReadHelp.readSpiritSkillInfo(b)
                )
                _loc10_ += 1
        # TODO 没找到 应该是数据库 _loc5_ 是宠物 id
        __loc4__['spiritDes'] = CONFIG.SPIRIT_CONFIG[str(__loc4__['id'])]
        __loc4__['equips'] = []
        # TODO 也是数据代理 Constants.SEQUIP_DES_DATA = "sequipDesProxy"
        if param3:
            _loc11_ = 0
            while _loc11_ < 6:
                _loc8_ = {
                    'serverID': b.readUnsignedInt()
                }
                __loc4__['equips'].append(_loc8_)
                _loc11_ += 1

        return __loc4__

    @staticmethod
    def readSpiritSkillInfo(param1: BtArray):
        """
            宠物携带技能信息
        :return:
        """
        # __loc2__: SpiritSkillInfo = SpiritSkillInfo()
        __loc2__ = {}
        _loc3_: int = param1.readUnsignedShort()
        __loc2__['id'] = _loc3_  # id 技能id
        __loc2__['ppLeft'] = param1.readUnsignedByte()  # 总pp
        __loc2__['isHeredity'] = param1.readUnsignedByte()  # 遗传技能 ? isHeredity 不太确定遗传技能
        __loc2__['skillDes'] = CONFIG.SPIRIT_SKILL_CONFIG[str(_loc3_)]
        return __loc2__

    @staticmethod
    def readHPVar(param1: BtArray):
        """
            读取 HP
        :param param1: 字节对象
        :return:
        """
        _loc2_ = Dict()
        _loc2_.hitTimes = param1.readUnsignedByte()
        _loc2_.hpV = param1.readShort()
        _loc2_.hpLeft = param1.readUnsignedShort()
        return _loc2_

    @staticmethod
    def readSpiritProperties(param1: BtArray):
        """
            阅读宠物属性
        :param param1: 字节对象
        :return:
        """
        _loc2_ = Dict()
        _loc2_.pa = param1.readShort()
        _loc2_.pd = param1.readShort()
        _loc2_.ma = param1.readShort()
        _loc2_.md = param1.readShort()
        _loc2_.ve = param1.readShort()
        _loc2_.sp = param1.readShort()
        _loc2_.dp = param1.readShort()
        _loc2_.crit = param1.readShort()
        return _loc2_

    @staticmethod
    def readBuffInfo(param1: BtArray):
        """
            buuf 信息
        :param param1:
        :return:
        """
        _loc2_ = Dict()
        _loc2_.id = param1.readUnsignedByte()
        _loc2_.buffType = param1.readUnsignedByte()
        _loc2_.cause = param1.readUnsignedByte()
        return _loc2_

    @staticmethod
    def readSpiritPropertysVar(param1: BtArray):
        """
            阅读 Spirit 属性 Var
        :return:
        """
        _loc3_: int = 0
        _loc2_ = Dict()  # SpiritPropertysVar
        _loc2_.index = param1.readUnsignedByte()
        _loc2_.exp = param1.readUnsignedInt()
        _loc2_.dLevel = param1.readUnsignedByte()
        _loc2_.cLevel = param1.readUnsignedByte()
        _loc2_.nextExp = param1.readUnsignedInt()
        _loc2_.deffort = param1.readUnsignedShort()
        _loc2_.pa = param1.readUnsignedShort()
        _loc2_.dpa = param1.readUnsignedShort()
        _loc2_.pd = param1.readUnsignedShort()
        _loc2_.dpd = param1.readUnsignedShort()
        _loc2_.ma = param1.readUnsignedShort()
        _loc2_.dma = param1.readUnsignedShort()
        _loc2_.md = param1.readUnsignedShort()
        _loc2_.dmd = param1.readUnsignedShort()
        _loc2_.ve = param1.readUnsignedShort()
        _loc2_.dve = param1.readUnsignedShort()
        _loc2_.sp = param1.readUnsignedShort()
        _loc2_.dsp = param1.readUnsignedShort()
        _loc2_.dp = param1.readUnsignedShort()
        _loc2_.ddp = param1.readUnsignedShort()
        _loc4_: int = 0
        _loc3_ = 4
        _loc2_.currentSkills = []
        _loc4_ = 0
        while _loc4_ < _loc3_:
            _loc2_.currentSkills.append(PReadHelp.readSpiritSkillInfo(param1))
            _loc4_ += 1
        _loc3_ = param1.readUnsignedShort()
        if _loc3_ > 0:
            _loc2_.newSKills = []
            _loc4_ = 0
            while _loc4_ < _loc3_:
                _loc2_.newSKills.append(PReadHelp.readSpiritSkillInfo(param1))
                _loc4_ += 1
        _loc2_.evolveSpiritId = param1.readUnsignedShort()
        return _loc2_

    @staticmethod
    def readUserItem(param1: BtArray):
        """
            用户信息
        :param param1: 字节流
        :return:
        """
        _loc2_ = Dict()  # UserItem
        _loc3_ = param1.readUnsignedInt()
        _loc2_.id = _loc3_
        _loc2_.count = param1.readUnsignedShort()
        # _loc2_.itemDes = itemProxy.select(_loc3_) as ItemDataDes;
        _loc2_.itemDes = {}
        return _loc2_


def readObjCombatInfo(b: BtArray):
    """
        读详情
    :return:
    """
    __lo2__ = {
        'type': b.readUnsignedByte(),
        'id': b.readUnsignedInt(),
        'nickName': Define.ReadString(b),
        'cIndex': b.readUnsignedByte(),
        'spirits': []
    }
    _loc3_: int = b.readUnsignedShort()
    __loc4__: int = 0
    while __loc4__ < _loc3_:
        __lo2__['spirits'].append(
            PReadHelp.readSpiritInfo(b, __loc4__, True)
        )
        __loc4__ += 1
    __lo2__['guardianPetEnergy'] = b.readUnsignedShort()
    __lo2__['guardianPetAttack'] = b.readUnsignedShort()
    __lo2__['guardianPetDefend'] = b.readUnsignedShort()
    __lo2__['guardianPetMA'] = b.readUnsignedShort()
    __lo2__['guardianPetMD'] = b.readUnsignedShort()
    return __lo2__


def readSpiritTalents(b: BtArray, spirits: list):
    """
        获取天赋
    :param b: 字节流
    :param spirits: 宠物列表
    :return:
    """
    readSpiritTalents_loc5_: int = 0
    readSpiritTalents_loc3_: int = 0
    while readSpiritTalents_loc3_ < len(spirits):
        readSpiritTalents_loc4_ = b.readUnsignedShort()
        _loc5_ = b.readUnsignedShort()
        spirits[readSpiritTalents_loc3_]['talentType'] = readSpiritTalents_loc4_
        spirits[readSpiritTalents_loc3_]['talentLevel'] = readSpiritTalents_loc5_
        readSpiritTalents_loc3_ += 1


def readNewEquipment(b: BtArray, spirits: list, param3: int, param4: int):
    """
        查询新内容
    :param b: 字节吗
    :param spirits: 宠物列表
    :param param3:
    :param param4:
    :return:
    """
    _loc6_: int = 0
    # _loc7_: IDataProxy = null
    # _loc8_: SpiritEquipmentDes = null
    # _loc9_: SpiritEquipmentInfo = null
    _loc5_: int = 0
    while _loc5_ < len(spirits):
        _loc6_ = b.readUnsignedShort()
        if spirits[_loc5_] and _loc6_ > 0:
            # __global.SysAPI.getGDataAPI().getDataProxy(Constants.SEQUIP_DES_DATA) =sequipDesProxy
            # _loc8_ = (_loc7_ = __global.SysAPI.getGDataAPI().getDataProxy(Constants.SEQUIP_DES_DATA)).select(param4, param3) as SpiritEquipmentDes;
            _loc8_ = SpiritEquipmentDes()
            _loc9_ = SpiritEquipmentInfo()
            _loc9_.des = _loc8_

            _loc9_.quality = 5
            _loc9_.id = param3
            _loc9_.type = param4
            spirits[_loc5_]['equips'][param4] = _loc9_
        _loc5_ += 1


class SerAttackInfo():
    def __init__(self) -> None:
        spiritIndex: int = 0
        ppLeft: int = 0
        reqType: int = 0
        skillIndex: int = 0
        pCode: dict = {}


def readAttackResInfo(param1: BtArray):
    """
        读取攻击资源信息
    :param param1: 数据包
    :return:
    """
    _loc5_: int = 0
    _loc2_: Dict = Dict()
    _loc2_.offenseID = param1.readUnsignedInt()
    _loc2_.offenseType = param1.readUnsignedByte()
    _loc2_.offenseIndex = param1.readUnsignedByte()
    _loc2_.defenseID = param1.readUnsignedInt()
    _loc2_.defenseType = param1.readUnsignedByte()
    _loc2_.defenseIndex = param1.readUnsignedByte()
    _loc2_.skillType = param1.readUnsignedByte()
    _loc2_.skillID = param1.readUnsignedInt()
    _loc2_.superformType = param1.readUnsignedByte()
    _loc2_.weather = param1.readUnsignedByte()
    _loc2_.skillBgFlag = param1.readUnsignedByte()
    # 查数据库
    # _loc2_.skillDec = PReadHelp.sskillProxy.select(_loc2_.skillID) as SpiritSkillDes;
    _loc2_.skillDec = SpiritSkillDes()
    _loc2_.isHurt = param1.readUnsignedByte() == 1
    _loc2_.isShaut = param1.readUnsignedByte() == 1
    _loc2_.isMiss = param1.readUnsignedByte() == 1
    _loc3_: int = param1.readUnsignedInt()
    _loc2_.myProxy = _loc3_ & 65535
    _loc2_.otherProxy = _loc3_ >> 16 & 65535
    print(f"[FightResultP] 分析出招 功击方:{_loc2_.offenseID} 防守方:{_loc2_.defenseID}")
    if (_loc4_ := param1.readUnsignedShort()) > 0:
        _loc2_.attackAffects = []
        _loc5_ = 0
        while _loc5_ < _loc4_:
            _loc2_.attackAffects.append(readAttackAffect(param1))
            _loc5_ += 1
    return _loc2_


def readAttackAffect(param1: BtArray):
    """
        查看攻击影响
    :param param1: 字节对象
    :return:
    """
    _loc6_: int = 0
    # _loc7_: ImmunityInfo = null
    _loc8_: int = 0
    _loc2_: Dict = Dict()  # AttackAffect
    _loc2_.id = param1.readUnsignedInt()
    _loc2_.type = param1.readUnsignedByte()
    _loc2_.index = param1.readUnsignedByte()
    _loc2_.isPP = param1.readUnsignedByte() == 1
    _loc2_.ppVar = []
    _loc3_: int = 0
    while _loc3_ < 4:
        _loc2_.ppVar.append(param1.readUnsignedByte())
        _loc3_ += 1

    _loc2_.hpVar = PReadHelp.readHPVar(param1)
    _loc2_.proVars = PReadHelp.readSpiritProperties(param1)
    _loc2_.allSpiritsHp = []
    _loc5_: int = 0
    while _loc5_ < 6:
        _loc6_ = param1.readUnsignedShort()
        _loc2_.allSpiritsHp.append(_loc6_)
        _loc5_ += 1
    _loc2_.restrainType = param1.readByte()
    _loc2_.immunityNum = param1.readUnsignedShort()
    # print(_loc2_.immunityNum)
    if _loc2_.immunityNum > 0:
        _loc2_.immunityVars = []
        _loc3_ = 0
        while _loc3_ < _loc2_.immunityNum:
            _loc7_ = Dict()
            _loc7_.immunityType = param1.readUnsignedByte()
            _loc7_.definiteId = param1.readUnsignedByte()
            _loc7_.typeId = 10000 + param1.readUnsignedShort()
            # _loc7_.btName = SpiritSkillDes(PReadHelp.sskillProxy.select(_loc7_.typeId)).name
            _loc7_.btName = 'name'
            _loc2_.immunityVars.append(_loc7_)
            _loc3_ += 1
    _loc2_.buffNum = param1.readUnsignedShort()
    if _loc2_.buffNum > 0:
        _loc2_.buffVars = []
        _loc8_ = 0
        while _loc8_ < _loc2_.buffNum:
            _loc2_.buffVars.append(PReadHelp.readBuffInfo(param1))
        _loc8_ += 1
    return _loc2_


def readBuffAffect(param1: BtArray):
    """
     buff 影响
    :param param1: 字节流
    :return:
    """
    _loc2_ = Dict()
    _loc2_.id = param1.readUnsignedInt()
    _loc2_.type = param1.readUnsignedByte()
    _loc2_.index = param1.readUnsignedByte()
    _loc2_.buffId = param1.readUnsignedByte()
    _loc2_.hpVar = PReadHelp.readHPVar(param1)
    _loc2_.proVars = PReadHelp.readSpiritProperties(param1)
    _loc2_.isremove = param1.readUnsignedByte()
    _loc2_.isOtherPro = bool(param1.readUnsignedByte())
    if _loc2_.isOtherPro:
        _loc2_.otherId = param1.readUnsignedInt()
        _loc2_.otherType = param1.readUnsignedByte()
        _loc2_.otherIndex = param1.readUnsignedByte()
        _loc2_.otherBuffId = param1.readUnsignedByte()
        _loc2_.otherHpVar = PReadHelp.readHPVar(param1)
        _loc2_.otherProVars = PReadHelp.readSpiritProperties(param1)
    return _loc2_


def readCombatResInfo(param1: BtArray, serAttackRes):
    """
        战斗资源信息
    :param serAttackRes: 发招数据
    :param param1: 字节流
    :return:
    """
    _loc6_ = Dict()  # NewSpiritInfo
    _loc2_ = Dict()  # CombatResultInfo
    _loc2_.canCombat = param1.readUnsignedByte()
    _loc2_.finished = param1.readUnsignedByte()
    # CombatResType.IS_FINISHED = _loc2_.finished
    _loc2_.version = param1.readUnsignedInt()
    _loc3_: int = param1.readUnsignedShort()
    _loc4_: int = 0
    _loc5_: int = 0
    _loc2_.spiritPropsVar = []
    if _loc3_ > 0:
        _loc4_ = 0
        while _loc4_ < _loc3_:
            _loc2_.spiritPropsVar.append(PReadHelp.readSpiritPropertysVar(param1))
            _loc4_ += 1
    _loc3_ = param1.readUnsignedShort()
    _loc2_.obtainItems = []
    if _loc3_ > 0:
        _loc4_ = 0
        while _loc4_ < _loc3_:
            _loc2_.obtainItems.append(PReadHelp.readUserItem(param1))
            _loc4_ += 1

    _loc3_ = param1.readUnsignedShort()
    _loc2_.spiritInfos = []
    if _loc3_ > 0:
        _loc4_ = 0
        while _loc4_ < _loc3_:
            _loc6_ = Dict()  # NewSpiritInfo
            _loc6_.propertyList = []
            _loc6_.flairList = []
            _loc6_.id = param1.readUnsignedInt()
            _loc6_.level = param1.readUnsignedByte()
            _loc6_.disposition = param1.readUnsignedByte()
            _loc5_ = 0
            while _loc5_ < 6:
                _loc6_.propertyList.append(param1.readUnsignedShort())
                _loc5_ += 1
            _loc5_ = 0

            while _loc5_ < 6:
                _loc6_.flairList.append(param1.readUnsignedShort())
                _loc5_ += 1
            _loc5_ = 0

            _loc2_.spiritInfos.append(_loc6_)
            _loc4_ += 1
    _loc2_.trainerExp = param1.readUnsignedInt()
    _loc2_.honourPoint = param1.readUnsignedInt()
    _loc2_.nextLevelTrainerExp = param1.readUnsignedInt()
    _loc2_.meetCondition = param1.readUnsignedByte()
    _loc2_.expAddBits = param1.readUnsignedByte()
    serAttackRes.spirit0UID = param1.readUnsignedInt()
    serAttackRes.spirit0BaseProperties = Dict()  # SpiritProperties
    serAttackRes.spirit0BaseProperties.pa = param1.readByte()
    serAttackRes.spirit0BaseProperties.pd = param1.readByte()
    serAttackRes.spirit0BaseProperties.ma = param1.readByte()
    serAttackRes.spirit0BaseProperties.md = param1.readByte()
    serAttackRes.spirit0BaseProperties.ve = param1.readByte()
    serAttackRes.spirit0BaseProperties.sp = param1.readByte()
    serAttackRes.spirit0BaseProperties.dp = param1.readByte()
    serAttackRes.spirit0BaseProperties.crit = param1.readByte()
    serAttackRes.spirit0CaptureRatio = param1.readUnsignedInt()
    serAttackRes.spirit1UID = param1.readUnsignedInt()
    serAttackRes.spirit1BaseProperties = Dict()  # SpiritProperties()
    serAttackRes.spirit1BaseProperties.pa = param1.readByte()
    serAttackRes.spirit1BaseProperties.pd = param1.readByte()
    serAttackRes.spirit1BaseProperties.ma = param1.readByte()
    serAttackRes.spirit1BaseProperties.md = param1.readByte()
    serAttackRes.spirit1BaseProperties.ve = param1.readByte()
    serAttackRes.spirit1BaseProperties.sp = param1.readByte()
    serAttackRes.spirit1BaseProperties.dp = param1.readByte()
    serAttackRes.spirit1BaseProperties.crit = param1.readByte()
    serAttackRes.spirit1CaptureRatio = param1.readUnsignedInt()
    return _loc2_


def decodeByTag(param1: BtArray, serAttackRes):
    """
        发招 tag
    :param serAttackRes: 发招数据
    :param param1: 字节对象
    :return:
    """
    _loc2_: int = param1.readUnsignedByte()
    if _loc2_ == 1:
        serAttackRes.attackList.append(readAttackResInfo(param1))
        decodeByTag(param1, serAttackRes)
    elif _loc2_ == 2:
        serAttackRes.attackList.append(readBuffAffect(param1))
        decodeByTag(param1, serAttackRes)
    elif _loc2_ == 3:
        serAttackRes.attackList.append(readCombatResInfo(param1, serAttackRes))


# 720899
def 请求战斗(_loc2_: BtArray):
    _loc3_ = SerAttackInfo()

    PReturnCode.readExternal(_loc2_)
    _loc3_.pCode = {}

    _loc3_.reqType = _loc2_.readUnsignedByte()
    _loc3_.spiritIndex = _loc2_.readUnsignedByte()
    _loc3_.skillIndex = _loc2_.readUnsignedByte()
    _loc3_.ppLeft = _loc2_.readUnsignedByte()
    print(_loc3_.__dict__)


def print_spirit(data):
    """
        输出宠物信息
    """
    print("""名称：{}\n血量：{}""".format(data['spiritDes']['name'], data['curHP']))
    for i in data['skills']:
        print_skills(i)


def print_skills(data):
    """
        输出技能信息
    """
    print("""\t{}:{}\t{}""".format(data['skillDes']['name'], data['ppLeft'], data['skillDes']['description']))


def print_rivalInfo(data):
    print("""用户名称：{}\nQQ：{}""".format(data['nickName'], data['id']))
    for i in data['spirits']:
        print_spirit(i)


# 720897
def 战斗(_loc2_: BtArray):
    if len(_loc2_) <= 100:
        return
    _loc4_ = CombatData()

    # 拆 code
    p = PReturnCode()
    p.readExternal(_loc2_)
    _loc4_.combatType = _loc2_.readUnsignedByte()
    _loc4_.canCombat = _loc2_.readUnsignedByte()

    _loc4_.myInfo = readObjCombatInfo(_loc2_)
    _loc4_.rivalInfo = readObjCombatInfo(_loc2_)

    if _loc4_.rivalInfo['type'] == 3:
        _loc4_.rivalInfo['id'] ^= _loc4_.myInfo['id']

    readSpiritTalents(_loc2_, _loc4_.myInfo['spirits'])
    readSpiritTalents(_loc2_, _loc4_.rivalInfo['spirits'])

    readNewEquipment(_loc2_, _loc4_.myInfo['spirits'], 10001, 0)
    readNewEquipment(_loc2_, _loc4_.rivalInfo['spirits'], 10001, 0)

    readNewEquipment(_loc2_, _loc4_.myInfo['spirits'], 10002, 0)
    readNewEquipment(_loc2_, _loc4_.rivalInfo['spirits'], 10002, 0)

    readNewEquipment(_loc2_, _loc4_.myInfo['spirits'], 10003, 1)
    readNewEquipment(_loc2_, _loc4_.rivalInfo['spirits'], 10003, 1)

    readNewEquipment(_loc2_, _loc4_.myInfo['spirits'], 10004, 1)
    readNewEquipment(_loc2_, _loc4_.rivalInfo['spirits'], 10004, 1)

    readNewEquipment(_loc2_, _loc4_.myInfo['spirits'], 10005, 2)
    readNewEquipment(_loc2_, _loc4_.rivalInfo['spirits'], 10005, 2)

    _loc4_.myCurSpirit = _loc4_.myInfo['spirits'][_loc4_.myInfo['cIndex'] - 1]
    _loc4_.rivalCurSpirit = _loc4_.rivalInfo['spirits'][_loc4_.rivalInfo['cIndex'] - 1]

    # TODO 展示不知道怎么展示
    # print(
    #     """
    #     ***********************************************
    #     * 对面昵称: {}
    #     """
    # )
    print_rivalInfo(_loc4_.rivalInfo)


# 720900
def 发招(_loc2_: BtArray):
    serAttackRes = Dict()

    serAttackRes.buffAffects = []
    serAttackRes.attackList = []

    serAttackRes.round = _loc2_.readUnsignedInt()
    decodeByTag(_loc2_, serAttackRes)
    print(serAttackRes)
    return serAttackRes


# 196629
def 查询用户详细信息(param1: BtArray):
    """
        SKT_0x030015_QueryUserDetailInfo_S2C
    :param param1: 字节类
    :return:
    """
    res = Dict()
    # 拆 code
    p = PReturnCode()
    p.readExternal(param1)

    res.qqUin = param1.readUnsignedInt()
    res.nickname = Define.ReadChars(param1, 16)
    res.birthDate = param1.readUnsignedInt()
    res.level = param1.readUnsignedShort()
    res.exp = param1.readUnsignedInt()
    res.maxExp = param1.readUnsignedInt()
    res.honor = param1.readUnsignedInt()
    res.strength = param1.readUnsignedInt()
    res.intelligence = param1.readUnsignedInt()
    res.charm = param1.readUnsignedInt()
    res.money = param1.readUnsignedInt()
    res.avatarVersion = param1.readUnsignedShort()
    res.avatar = [0] * 9
    _loc2_: int = 0
    while _loc2_ < 9:
        res.avatar[_loc2_] = param1.readUnsignedInt()
        _loc2_ += 1
    res.badge = param1.readUnsignedByte()
    res.isVip = param1.readByte() != 0
    res.vipLevel = param1.readUnsignedByte()
    res.magicValue = param1.readUnsignedInt()
    res.vipExpireDate = param1.readInt()
    res.vipRemainDays = param1.readUnsignedInt()
    res.pvpMatchWin = param1.readUnsignedInt()
    res.pvpMatchLose = param1.readUnsignedInt()
    res.pvpMatchEscape = param1.readUnsignedInt()
    res.pvpFreePkWin = param1.readUnsignedInt()
    res.pvpFreePkLose = param1.readUnsignedInt()
    res.pvpFreePkEscape = param1.readUnsignedInt()
    res.pvpFreePkConfig = param1.readUnsignedByte()
    res.bossInfoBraveMode = param1.readUnsignedInt()
    res.bossInfoHeroMode = param1.readUnsignedInt()
    res.bossInfoTreasure = param1.readUnsignedInt()
    res.skyTowerMaxFloorNum = param1.readUnsignedByte()
    res.trainerLevel = param1.readUnsignedByte()
    res.trainerExp = param1.readUnsignedInt()
    res.achieveId = param1.readUnsignedByte()
    res.achieveTitleLevel = param1.readUnsignedByte()
    res.avatarTransformID = param1.readUnsignedInt()
    res.avatarEffectID = param1.readUnsignedInt()
    print(res)
    return res


def ReqAllMovieEndP(param1: BtArray):
    print(param1.readUnsignedInt())


if __name__ == '__main__':
    c = TcpStickyBag()

    c.push_stream('95 27 00 00 00 0B 05 19 AA CF F9 F4 00 00 00 64 00 00 00 06 08 F4 F3 BF D6 0A')
    c.pull_stream()
    print(c.bt_array.bt_array)
    print('*' * 100)

    c.push_stream('95 27 00 00 00')
    c.pull_stream()
    print(c.bt_array.bt_array)
    print('*' * 100)
    c.push_stream('0B 05 19 AA CF F9 F4 00 00 00 64 00 00 00 08 0A 04 08 00 12 00 10 00')
    c.pull_stream()
    print(c.bt_array.bt_array)
    print('*' * 100)
    c.push_stream(
        '95 27 00 00 00 0B 00 01 AA CF F9 F4 00 00 00 00 00 00 00 09 11 00 00 00 00 00 00 00 00 95 27 00 00 00 0B 00 01 AA CF F9 F4 00 00 00 00 00 00 03 70 00 00 00 00 00 00 11 31 03 AA CF F9 F4 00 06 D0 A1 C2 E5 BF CB 01 00 06 00 00 09 5C 64 01 02 B1 02 B1')
    c.pull_stream()
    print(c.bt_array.bt_array)
    print('*' * 100)
    c.push_stream(
        '91 64 00 04 06 EB 08 00 01 95 14 00 06 64 0A 00 06 E9 04 00 02 00 00 7D 02 10 00 7B 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0A FA 64 02 02 BC 02 BC C5 E4 00 04 01 D9 28 00 09 85 0C 00 09 83 0C 00 09 81 06 00 02 00 00 7E 02 10 00 7B 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 07 D5 64 01 02 6C 02 6C 95 E4 00 04 06 64 0A 00 01 95 14 00 05 31 08 00 05 2F 01 00 02 00 00 7E 02 10 00 7C 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 09 5A 64 02 02 30 02 30 00 22 00 04 06 D2 0F 00 02 66 0A 00 06 D3 06 00 06 D1 04 00 00 00 00 00 00 00 00 00 02 20 00 74 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 31 64 02 01 4B 01 4B C6 E4 00 04 00 CD 1E 00 00 CB 0A 00 00 6A 05 00 00 22 05 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 09 69 64 02 01 89 01 89 00 5E 00 04 04 C0 05 00 05 A2 0A 00 06 9E 04 00 04 99 05 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 18 00 18 00 18 00 18 00 18 03 C4 CF 86 1E 00 0A BE AB C1 E9 CD F5 D5 BD B6 D3 01 00 06 00 00 0B 85 64 01 02 C1 02 C1 A5 64 00 04 0A 73 0A 00 0A 72 0C 00 0A 71 08 00 04 4E 05 00 02 00 00 7D 02 10 00 7B 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 09 98 64 01 02 D8 02 D8 C9 E4 00 04 07 2E 02 00 07 2F 01 00 07 30 0A 00 07 32 0C 00 02 00 00 7E 02 10 00 7C 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0B 70 64 02 02 A8 02 A8 91 64 00 04 0A 59 0C 00 0A 58 0A 00 0A 57 03 00 0A 56 06 00 02 00 00 7E 02 10 00 7B 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0B 92 64 01 02 8C 02 8C 52 64 00 04 0A 7E 0C 00 0A 7C 0A 00 0A 7B 0A 00 0A 7A 00 00 02 00 00 7D 02 10 00 7C 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 0A FA 64 02 02 C2 02 C2 79 E4 00 04 09 81 06 00 09 85 0C 00 09 84 09 00 09 82 04 00 02 00 00 7E 02 10 00 7C 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 00 07 EE 64 01 02 C3 02 C3 A8 E4 00 04 0A 07 08 00 0A 04 06 00 0A 05 0A 00 0A 06 0A 00 02 00 00 7D 02 10 00 7B 02 20 00 7A 00 00 00 00 00 00 00 00 00 00 00 00 00 25 00 25 00 25 00 25 00 25 00 00 00 00 00 18 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 21 00 01 00 00 00 00 00 00 00 00 00 22 00 01 00 18 00 01 00 1B 00 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00')
    c.pull_stream()
    print(c.bt_array.bt_array)
    print('*' * 100)
