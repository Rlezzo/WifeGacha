from enum import Enum

class AcquisitionMethod(Enum):
    DRAW = 1
    EXCHANGE = 2
    NTR = 3

# 定义获取方式到统计字段的映射
ACQ_METHOD_TO_FIELD = {
    AcquisitionMethod.DRAW: 'draw_count',
    AcquisitionMethod.EXCHANGE: 'acquired_by_ex_count',
    AcquisitionMethod.NTR: 'acquired_by_ntr_count'
}