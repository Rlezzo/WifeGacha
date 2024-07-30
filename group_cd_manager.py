import json
import os

class GroupCDManager:
    def __init__(self, config_filename):
        self.config_file = os.path.join(os.path.dirname(__file__), config_filename)
        self.default_cd = 600  # 默认CD时间为600秒
        self.group_cd = self.load_or_create_config()

    def load_or_create_config(self):
        if not os.path.exists(self.config_file):
            # 如果配置文件不存在，则创建默认配置文件
            default_config = {
                "123456": self.default_cd  # 示例群组的CD时间
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        else:
            with open(self.config_file, 'r') as f:
                return json.load(f)

    def get_group_cd(self, group_id):
        if group_id not in self.group_cd:
            # 如果群组ID不存在于配置中，则添加并设置默认CD时间
            self.group_cd[group_id] = self.default_cd
            self.save_config()
        return self.group_cd[group_id]

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.group_cd, f, indent=4)
            
    def set_group_cd(self, group_id, cd_seconds):
        """设置特定群组的CD时间并保存配置"""
        self.group_cd[group_id] = cd_seconds
        self.save_config()