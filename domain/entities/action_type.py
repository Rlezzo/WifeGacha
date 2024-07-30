from enum import Enum

class ActionType(Enum):
    MATING = 1
    DIVORCE = 2
    # 其他动作类型可以在这里添加

# 定义动作类型到统计字段的映射
ACTION_TYPE_TO_FIELD = {
    ActionType.MATING: 'mating_count',
    ActionType.DIVORCE: 'divorce_count'
    # 其他动作类型的映射可以在这里添加
}
