# WifeGacha
AnimeWife数据记录版的完全重置

背景：之前那个版本，用查询语句写的，拓展性很差，于是我问GPT，如何对敌？

GPT说，用sqlalchemyORM和DDD领域设计模式，很方便！

我说，好！

然后GPT传授了我一些完全搞不懂的东西，但是没办法，只能硬着头皮干了，干一点问一点，问一点干一点，于是不是程序员的我写出来了这个项目。



## 如何安装

1. 在HoshinoBot的插件目录modules下clone本项目

    `git clone https://github.com/Rlezzo/WifeGacha.git`

2. 下载 `Releases` 中的图包
3. **需要保证图片名不重名**，不看后缀的文件名，重名初次导入，添加重复时会提示：
 ```
Insertion failed: BaseName '伊地知虹夏' already exists.                        
导入伊地知虹夏.jpeg失败, 可能出现重名                                          
Insertion failed: BaseName '莱妮丝·埃尔梅罗·阿奇佐尔缇' already exists.        
导入莱妮丝·埃尔梅罗·阿奇佐尔缇.jpeg失败, 可能出现重名     
```
图片的文件夹结构
```
img
    └── wife
        ├── default
        │   ├── D杀手妻子.png
        │   ├── KDA阿狸.png
        │   ├── NIKKE-伊莱格.png
        │   ├── NIKKE-爱丽丝.png
        ├── kotone
        │   ├── 藤田琴音我老婆.jpg
        │   ├── 藤田琴音A.jpeg
        │   ├── 藤田琴音B.jpeg
        │   ├── 藤田琴音D.jpeg
        ....
```
wife文件夹下有default、kotone等卡池文件夹，可以按照卡池分类图片

**注意**：除了初始化，和替换同名图片以外，不要手动修改卡池、图片名称、位置，会导致与数据库信息不一致的问题
4. 在 `config/__bot__.py`的模块列表里加入 `WifeGacha`

5. 重启HoshinoBot

## 怎么使用

```
-[抽老婆] 看看今天的二次元老婆是谁
-[添加老婆+人物名称+卡池名称(选填)+图片] 群管理员每天可以添加一次人物
※为防止bot被封号和数据污染请勿上传太涩与功能无关的图片※
-[交换老婆] @某人 + 交换老婆
-[牛老婆] 50%概率牛到别人老婆(1次/日)
-[查老婆] 加@某人可以查别人老婆，不加查自己
-[离婚] 清楚当天老婆信息，可以重新抽老婆（管理）
-[重置牛老婆] 加@某人可以重置别人牛的次数（管理）
-[设置日老婆CD] 后接数字（管理）
-[用户档案] 统计用户的一些数据，@某人可以查看他人的数据
-[老婆图鉴] 查看老婆解锁情况，@某人可以查看他人的数据
-[老婆档案] 统计老婆的一些数据，后接老婆名字可以查看具体角色的数据
-[清理抽老婆用户] 清除不在的群和群成员(可能会很卡)（管理）
-[切换NTR图鉴开关状态] 开启图鉴统计NTR所得
```
### 抽老婆
效果图：

![image](https://github.com/user-attachments/assets/161ebac8-4bb1-4928-ac28-10fd7ed78fc0)

重复抽到会显示`重复了！`
### 查老婆
效果图：

![image](https://github.com/user-attachments/assets/dfd9b163-68a6-4189-83c1-a2f87d8e217b)

### 日老婆
效果图：

![image](https://github.com/user-attachments/assets/cc8635ea-c5fe-4f15-b5a0-8ee27486e52c)

![image](https://github.com/user-attachments/assets/cf22b49f-80b0-45ac-a858-a0b9e0e90d02)

暂时没有想到什么其他玩法，之前是准备引入AI，然后随机回复甜言蜜语，但是要比较好的提示词，不然回复很尬，可以参考我之前的aichat项目，自己简单加一个ai试试。

### 牛老婆&交换老婆(和之前一样)

### 用户档案
@某人得到的回复：

![image](https://github.com/user-attachments/assets/229cdd99-c38c-47bc-b9c7-83840ece8c2d)

单独发送得到的回复：

![image](https://github.com/user-attachments/assets/02b7c310-9287-4e10-ad3f-544cf2200147)

### 老婆档案
单独发送得到的回复：

![image](https://github.com/user-attachments/assets/1dbba44f-7aeb-4d1d-aef0-cd2aad1fbd28)

后接模糊名称：

![image](https://github.com/user-attachments/assets/46d46a47-2a07-4367-93ef-3bb4a276af33)


后接精确名称：

![image](https://github.com/user-attachments/assets/fe5b456a-d489-4213-83e1-b7783077e10a)

![image](https://github.com/user-attachments/assets/e27d35d4-b034-420d-9709-125b6b739806)

## 项目结构简析
```
WifeGacha
├── __init__.py
├── application
│   ├── __init__.py
│   └── services  # main.py调用应用层功能，实现抽老婆等
│       ├── __init__.py
│       ├── action_application_service.py
│       ├── character_application_service.py
│       ├── current_user_group_character_application_service.py
│       ├── event_service.py
│       ├── statistics_application_service.py
│       ├── user_group_application_service.py
│       └── user_group_character_application_service.py
├── domain # 领域模型
│   ├── __init__.py
│   ├── entities
│   │   ├── __init__.py
│   │   ├── acquisition_method.py
│   │   ├── action_type.py
│   │   ├── character.py
│   │   ├── current_user_group_character.py
│   │   ├── double_user_character_event.py
│   │   ├── group.py
│   │   ├── single_user_character_event.py
│   │   ├── user.py
│   │   ├── user_group.py
│   │   ├── user_group_character.py
│   │   └── user_group_character_stats.py
│   └── services 
│       ├── __init__.py
│       └── exchange_manager.py # 交换老婆锁
├── group_cd_manager.py
├── infrastructure
│   ├── __init__.py
│   ├── database
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── database_init.py
│   │   ├── orm # ORM模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── character_orm.py
│   │   │   ├── current_user_group_character_orm.py
│   │   │   ├── double_user_character_event_orm.py
│   │   │   ├── group_orm.py
│   │   │   ├── single_user_character_event_orm.py
│   │   │   ├── user_group_character_orm.py
│   │   │   ├── user_group_character_stats_orm.py
│   │   │   ├── user_group_orm.py
│   │   │   └── user_orm.py
│   │   └── wife.db
│   ├── factories # 应用工厂
│   │   ├── __init__.py
│   │   ├── action_application_service_factory.py
│   │   ├── character_service_factory.py
│   │   ├── current_user_group_character_service_factory.py
│   │   ├── event_service_factory.py
│   │   ├── statistics_application_factory.py
│   │   ├── user_group_character_service_factory.py
│   │   └── user_group_service_factory.py
│   ├── mappers 
│   │   ├── __init__.py
│   │   ├── domain_to_orm.py
│   │   └── orm_to_domain.py
│   └── repositories # 仓储
│       ├── __init__.py
│       ├── character_repository.py
│       ├── current_user_group_character_repository.py
│       ├── double_user_character_events_repository.py
│       ├── group_repository.py
│       ├── impl
│       │   ├── __init__.py
│       │   ├── character_repository_impl.py
│       │   ├── current_user_group_character_repository_impl.py
│       │   ├── double_user_character_events_repository_impl.py
│       │   ├── group_repository_impl.py
│       │   ├── single_user_character_events_repository_impl.py
│       │   ├── user_group_character_repository_impl.py
│       │   ├── user_group_character_stats_repository_impl.py
│       │   ├── user_group_repository_impl.py
│       │   └── user_repository_impl.py
│       ├── single_user_character_events_repository.py
│       ├── user_group_character_repository.py
│       ├── user_group_character_stats_repository.py
│       ├── user_group_repository.py
│       └── user_repository.py
├── main.py
└── utils.py # 杂七杂八
```
都是GPT教的结构，也不知道对不对，反正能用。

## 可自行修改的部分
- 抽老婆
这里是测试用的，可以帮别人抽老婆，目前是默认bot管理员才能用，如果想让管理能用就修改下面关于管理员权限的部分。

不需要可以只用on_fullmatch，并且删除下面部分的内容
```
@sv.on_prefix('抽老婆')
@sv.on_suffix('抽老婆')
# @sv.on_fullmatch('抽老婆')

    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id in hoshino.config.SUPERUSERS:
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv < sv.manage_priv:
        # return
        
        # 这是帮别人抽老婆的功能，如果不需要
        # 可以把上面权限相关的，和下面这部分都删除或注释掉
        # 然后on_suffix和on_prefix改成on_fullmatch
        target_id = None
        # 提取目标用户的QQ号
        for seg in ev.message:
            if seg.type == 'at' and seg.data['qq'] != 'all':
                target_id = int(seg.data['qq'])
                break
        # 没有@任何人，且没有附带其他消息，只有“抽老婆”命令
        if not target_id and ev.message.extract_plain_text().strip() == "":
            pass
        elif not target_id:
            # 谈论“抽老婆”不做反应
            return
        else:
            user_id=target_id
```
- 添加老婆
默认还是bot管理员可用，因为现在添加图片，如果大小超过2MB会自动压缩到2MB以下，包括gif动图，会比较慢，如果放开添加，不知道会不会出现问题。

加上老婆池是通用的，管理起来挺麻烦，bot管理员统一用命令添加删除，数据不容易出错。推荐bot管理员统一管理。
```
    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id not in hoshino.config.SUPERUSERS:
        return

    #判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)

    # if u_priv < sv.manage_priv:
    #     return
    # elif not _add_lmt.check(key):
    #     # 检查用户今天是否已添加过老婆信息
    #     await bot.send(ev, _add_max_notice, at_sender=True)
    #     return
```
- 离婚
同抽老婆

## 可能出现的问题
有人反馈@hoshino.get_bot().server_app.before_serving不能使用，但是如此修改可用
```
bot = hoshino.get_bot()
@bot.server_app.before_serving
```

NapCat1.6.0以及之后的版本会出现subType报错，目前不清楚如何解决

该插件使用到的某些特性在python3.8是不支持的如 tuple[str, str]。如果你使用的是python3.8的环境运行bot将可能无法使用该插件。

## 更新日志
|     日期     | 内容                                                                             |
|:----------:|:-------------------------------------------------------------------------------|
| 2024-08-01 | 添加老婆图鉴的功能。老婆图鉴功能参考[login_bonus](https://github.com/SonderXiaoming/login_bonus) |
| 2024-08-19 | 添加切换NTR图鉴开关状态，开启后老婆图鉴将点亮你NTR到的老婆（牛牛牛，还在牛）                                      |
| 2024-09-01 | 解决内存占用过高的问题1.预加载图片进行缩放后加载；2.增加开关”PRELOAD“关闭后将不进行图片预加载                          |
| 2024-09-09 | 被牛走老婆的受害者，会增加一次牛老婆次数，避免被牛走老婆还无法还击，导致破防                                         |
| 2024-11-02 | 老婆图鉴可以通过交换老婆解锁图鉴了，开启NTR图鉴即可开启该功能                                               |
| 2024-11-20 | 兼容NapCat新版本(4.1.12)参考[xqa](https://github.com/azmiao/XQA)                      |
