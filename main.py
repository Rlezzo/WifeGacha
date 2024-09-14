import os, re, random, asyncio, hoshino
import base64
from PIL import Image, ImageFont
from io import BytesIO
from hoshino import Service, priv
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter, FreqLimiter
from domain.entities import *
from domain.services import ExchangeManager
from infrastructure.factories import *
from infrastructure.database.database_init import init_db
from infrastructure.database.connection import AsyncSessionFactory, close_engine
from .group_cd_manager import GroupCDManager
from .utils import (
    init_characters,
    handle_ex_wife,
    download_async,
    is_near_midnight,
    rename_image_file,
    update_single_character,
    add_single_character,
    backup_character_image,
    restore_character_image,
    delete_image_and_empty_folder,
    get_card_by_uid_gid,
    format_seconds,
    img_path,
    load_ntr_atlas_statuses,
    save_ntr_atlas_statuses
)
#————————————————————基本参数————————————————————#
# 创建一个全局的ExchangeManager实例，用于交换老婆和牛老婆的锁
ex_manager = ExchangeManager()

# 初始化GroupCDManager实例, 分群管理日老婆CD
cd_manager = GroupCDManager('group_cd_config.json')

# 群管理员每天可添加老婆的次数
_add_max=1
_add_lmt= DailyNumberLimiter(_add_max)
# 当超出次数时的提示
_add_max_notice = f'为防止滥用，管理员一天最多可添加{_add_max}次，若需更多请用"来杯咖啡"联系维护组'

# 牛老婆的成功率
ntr_possibility = 0.5
# 每人每天可牛老婆的次数
_ntr_max=1
_ntr_lmt= DailyNumberLimiter(_ntr_max)
# 当超出次数时的提示
_ntr_max_notice = f'为防止牛头人泛滥，一天最多可牛{_ntr_max}次，若需更多请用"来杯咖啡"联系维护组'

# 通用命令频率限制,5秒
_flmt = FreqLimiter(5)

# 日老婆频率限制
_mating_lmt = FreqLimiter(1800)

# 档案查询频率限制
_archive_lmt = FreqLimiter(30)

# 每人每天可离婚的次数
_divorce_max=1
_divorce_lmt= DailyNumberLimiter(_divorce_max)
# 当超出次数时的提示
_divorce_max_notice = f'本群每天只允许离婚{_divorce_max}次！'
# 在程序启动时调用：载入NTR图鉴状态
# 用来存储所有群组的NTR图鉴状态的路径和状态
ntr_atlas_status_file = 'ntr_atlas_status.json'

# ——————————————————————图鉴预加载配置——————————————————————#
PRELOAD = True  # 是否在启动时直接将所有图片加载到内存中，开启后可以提高查看仓库的速度但会增加内存的占用(大约十几M)
COL_NUM = 10  # 查看仓库时每行显示的卡片个数
# 背景图路径
__BASE = os.path.split(os.path.realpath(__file__))[0]
FRAME_DIR_PATH = os.path.join(__BASE, 'image')
# 老婆路径
DIR_PATH = img_path
# 文字路径，字体大小为16
font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'arial.ttf'), 16)
card_file_names_all = []

# 资源预检
image_cache = {}
# 列出DIR_PATH目录下所有的文件和文件夹名，存储在image_list列表中。
# 卡池文件夹名称list
pool_names = [entry for entry in os.listdir(DIR_PATH) if os.path.isdir(os.path.join(DIR_PATH, entry))]
# 遍历每个子文件夹，并加载其中的图片
for pool_name in pool_names:
    pool_path = os.path.join(DIR_PATH, pool_name)
    image_list = [f for f in os.listdir(pool_path) if os.path.isfile(os.path.join(pool_path, f))]
    for image in image_list:
        # 去除文件名后缀
        file_name_without_ext = os.path.splitext(image)[0]
        # 图像缓存
        if PRELOAD:
            image_path = os.path.join(pool_path, image)
            img = Image.open(image_path)
            # 缩放图片到80x80像素
            img = img.resize((80, 80), Image.ANTIALIAS)
            # 转换为RGBA模式（如果需要）
            img = img.convert('RGBA')
            # 存储到缓存中
            image_cache[file_name_without_ext] = img
        # 将无后缀的文件名添加到card_file_names_all列表中
        card_file_names_all.append(file_name_without_ext)
# 保存输出文件名列表的长度
len_card = len(card_file_names_all)


# 根据给定的图片路径pic_path和是否灰度化的标志grey来返回处理后的图片。
def get_pic(pic_path, grey):
    if PRELOAD:
        sign_image = image_cache[pic_path]
    else:
        # 构造基础路径
        base_path = os.path.join(DIR_PATH)
        # 在每个子文件夹中搜索图片
        for pool_name in pool_names:
            pool_path = os.path.join(base_path, pool_name)
            for entry in os.listdir(pool_path):
                if entry.startswith(pic_path):
                    # 找到图片，加载并处理
                    image_path = os.path.join(pool_path, entry)
                    sign_image = Image.open(image_path)
    # 图片被缩放到80x80像素，并应用抗锯齿算法
    sign_image = sign_image.resize((80, 80), Image.ANTIALIAS)
    # 如果grey为True，则将图片转换为灰度图。
    if grey:
        sign_image = sign_image.convert('L')
    return sign_image

#——————————————————————服务——————————————————————#

sv_help = f'''
-[抽老婆] 看看今天的二次元老婆是谁
-[添加老婆+人物名称+卡池名称(选填)+图片] 群管理员每天可以添加一次人物
※为防止bot被封号和数据污染请勿上传太涩与功能无关的图片※
-[交换老婆] @某人 + 交换老婆
-[牛老婆] {ntr_possibility * 100}%概率牛到别人老婆({_ntr_max}次/日)
-[查老婆] 加@某人可以查别人老婆，不加查自己
-[离婚] 清楚当天老婆信息，可以重新抽老婆（管理）
-[重置牛老婆] 加@某人可以重置别人牛的次数（管理）
-[设置日老婆CD] 后接数字（管理）
-[用户档案] 统计用户的一些数据，@某人可以查看他人的数据
-[老婆图鉴] 查看老婆解锁情况，@某人可以查看他人的数据
-[老婆档案] 统计老婆的一些数据，后接老婆名字可以查看具体角色的数据
-[清理抽老婆用户] 清除不在的群和群成员(可能会很卡)（管理）
-[切换NTR图鉴开关状态] 开启图鉴统计NTR所得
———————————————以下仅限管理员—————————————————————————
[更新老婆][删除老婆][重命名老婆]
'''.strip()

sv = Service(
    name = '抽老婆',  #功能名
    use_priv = priv.NORMAL, #使用权限   
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #可见性
    enable_on_default = True, #默认启用
    bundle = '娱乐', #分组归类
    help_ = sv_help #帮助说明
    )

#—————————————————————初始化—————————————————————#

# 在插件启动时初始化和创建所需的表
bot = hoshino.get_bot()
@bot.server_app.before_serving
async def initialize_database():
    await init_db()
    # 角色表为空的时候初始化添加
    await init_characters()
# 手动初始化，如果首次启动bot超时可以使用以下方法
# @sv.on_prefix('初始化')
# @sv.on_suffix('初始化')
# async def initialize_database(bot, ev: CQEvent):
#     # 获取QQ信息
#     user_id = ev.user_id
#     # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
#     if user_id not in hoshino.config.SUPERUSERS:
#         return
#     await init_db()
#     # 角色表为空的时候初始化添加
#     await init_characters()

# 关闭数据库连接
@bot.server_app.after_serving
async def close_database():
    await close_engine()

#—————————————————————抽老婆—————————————————————#

@sv.on_prefix('抽老婆')
@sv.on_suffix('抽老婆')
# @sv.on_fullmatch('抽老婆')
async def darw_wife(bot, ev: CQEvent):
    # 获取QQ群、群用户QQid
    group_id = ev.group_id
    user_id = ev.user_id
    
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)
    
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
    elif ev.message.extract_plain_text().strip() != "":
        # 群友谈论关键词
        return
        
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user_group_sv = await UserGroupSvFactory(session).create()
            # 获得user_group，如果没有会自动添加
            ug = await user_group_sv.add_and_get_user_group(user_id, group_id)
            # 事件记录服务
            event_sv = await EventSvFactory(session).create()
            # 当前老婆管理服务
            current_sv = await CurrentSvFactory(session).create()
            # 获得角色，如果不是当天信息，或者角色为空，或者初次使用，返回空
            character = await current_sv.get_current_character(ug)
            if character:
                await event_sv.add_double_event(ug, ug, character, character, "查老婆", "self")
                try:
                    await bot.send(
                        ev, 
                        f"\n你的今日老婆：\n"
                        f"{character.pool_name}池：{character.name}\n"
                        f"{character.image_path}",
                        at_sender=True
                        )
                except Exception as e:
                    await bot.send(
                        ev, 
                        f"\n你的今日老婆：\n"
                        f"{character.pool_name}池：{character.name}\n"
                        "[图片发送失败]",
                        at_sender=True
                        )
                return
            
            # 随机获得一个角色
            character_sv = await CharacterSvFactory(session).create()
            character = await character_sv.get_random_character()
            
            # ug_character关联表服务
            ugc_sv = await UGCharacterSvFactory(session).create()
            # 记录是出新还是重复，如果建立过关联就是重复
            if await ugc_sv.has_character(ug, character):
                result = "重复"
                before_stats = await ugc_sv.get_user_group_character_stats(ug, character)
            else:
                result = "出新"
            # 添加ug_character记录，如果已存在会增加一次获得次数
            await ugc_sv.add_or_update_character_by_acquisition_method(ug, character, AcqMethod.DRAW)
            
            # 添加到current表
            await current_sv.add_or_update_current_character(ug, character)
            
            # 记录抽卡事件
            await event_sv.add_single_event(ug, character, "抽老婆", result)
            hoshino.logger.info(f"抽到的老婆是：{character.name}")
            msg = f"\n{result}了！\n你今天的老婆是：{character.name}哒~\n"
            msg_img = f"{character.image_path}"
            msg_time = ""  # 添加默认值
            msg_count = ""  # 添加默认值
            if result == "重复":
                msg_time = f"上次抽到她的时间是：{before_stats.lastest_acquisition_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                msg_count = f"总共抽到她：{before_stats.draw_count + 1}次"
            try:
                await bot.send(ev, msg + msg_img + msg_time + msg_count, at_sender=True)
            except Exception as e:
                await bot.send(ev, msg + "[图片发送失败]\n" + msg_time + msg_count, at_sender=True)

#—————————————————————查老婆—————————————————————#

@sv.on_prefix('查老婆')
@sv.on_suffix('查老婆')
async def check_wife(bot, ev: CQEvent):
    # 获取QQ群、群用户QQid
    group_id = ev.group_id
    user_id = ev.user_id
    
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}后再试')
        return
    _flmt.start_cd(key)
    
    target_id = None
    # 提取目标用户的QQ号
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    # 没有@任何人，且没有附带其他消息，只有“查老婆”命令
    if not target_id  and ev.message.extract_plain_text().strip() == "":
        # 查自己
        target_id = user_id
        lookup_type = "self"
    elif not target_id:
        # 谈论“查老婆”不做反应
        return
    else:
        lookup_type = "other"
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user_group_sv = await UserGroupSvFactory(session).create() # ug服务
            event_sv = await EventSvFactory(session).create() # event服务
            current_ugc_sv = await CurrentSvFactory(session).create() # 当天角色
            # 获得ug对应的当前角色信息
            ug = await user_group_sv.add_and_get_user_group(user_id, group_id)
            character = await current_ugc_sv.get_current_character(ug)
            if lookup_type == "self":
                # 查自己的情况, 如果有老婆
                if character:
                    ugc_sv = await UGCharacterSvFactory(session).create() # ug_c服务
                    stats = await ugc_sv.get_user_group_character_stats(ug, character)
                    try:
                        await bot.send(
                            ev, 
                            "\n今日老婆：\n"
                            f"{character.pool_name}池：{character.name}\n"
                            f"{character.image_path}"
                            f"抽到：{stats.draw_count}次\n"
                            f"交换得到：{stats.acquired_by_ex_count}次\n"
                            f"牛到：{stats.acquired_by_ntr_count}次\n"
                            f"好感度：{stats.mating_count}\n"
                            f"离婚次数：{stats.divorce_count}\n"
                            f"今日获得时间：{stats.lastest_acquisition_time.strftime('%H:%M:%S')}",
                            at_sender=True
                        )
                    except Exception as e:
                        await bot.send(
                            ev, 
                            "\n今日老婆：\n"
                            f"{character.pool_name}池：{character.name}\n"
                            "[图片发送失败]\n"
                            f"抽到：{stats.draw_count}次\n"
                            f"交换得到：{stats.acquired_by_ex_count}次\n"
                            f"牛到：{stats.acquired_by_ntr_count}次\n"
                            f"好感度：{stats.mating_count}\n"
                            f"离婚次数：{stats.divorce_count}\n"
                            f"今日获得时间：{stats.lastest_acquisition_time.strftime('%H:%M:%S')}",
                            at_sender=True
                        )
                    # 记录抽老婆结果
                    await event_sv.add_double_event(ug, ug, character, character, "查老婆", lookup_type)
                else:
                    await bot.send(ev, "今天还没抽老婆哦~", at_sender=True)
            else:
                ug_target = await user_group_sv.add_and_get_user_group(target_id, group_id)
                # 获得ug_target对应的当前角色信息
                character_target = await current_ugc_sv.get_current_character(ug_target)
                nick_name = await get_card_by_uid_gid(target_id, group_id)
                if character_target:
                    ugc_sv = await UGCharacterSvFactory(session).create()
                    stats = await ugc_sv.get_user_group_character_stats(ug_target, character_target)
                    try:
                        await bot.send(
                            ev, 
                            f"\n{nick_name}的今日老婆：\n"
                            f"{character_target.pool_name}池：{character_target.name}\n"
                            f"{character_target.image_path}"
                            f"抽到：{stats.draw_count}次\n"
                            f"交换得到：{stats.acquired_by_ex_count}次\n"
                            f"牛到：{stats.acquired_by_ntr_count}次\n"
                            f"好感度：{stats.mating_count}\n"
                            f"离婚次数：{stats.divorce_count}\n"
                            f"今日获得时间：{stats.lastest_acquisition_time.strftime('%H:%M:%S')}",
                            at_sender=True
                        )
                    except Exception as e:
                        await bot.send(
                            ev, 
                            f"\n{nick_name}的今日老婆：\n"
                            f"{character_target.pool_name}池：{character_target.name}\n"
                            "[图片发送失败]\n"
                            f"抽到：{stats.draw_count}次\n"
                            f"交换得到：{stats.acquired_by_ex_count}次\n"
                            f"牛到：{stats.acquired_by_ntr_count}次\n"
                            f"好感度：{stats.mating_count}\n"
                            f"离婚次数：{stats.divorce_count}\n"
                            f"今日获得时间：{stats.lastest_acquisition_time.strftime('%H:%M:%S')}",
                            at_sender=True
                        )
                    # 记录抽老婆结果
                    await event_sv.add_double_event(ug, ug_target, character, character_target, "查老婆", lookup_type)
                else:
                    await bot.send(ev, f"\n{nick_name}今天还没抽老婆哦~", at_sender=True)

#———————————————————交换老婆—————————————————————#

@sv.on_prefix('交换老婆')
@sv.on_suffix('交换老婆')
async def exchange_wife(bot, ev: CQEvent):
    if await is_near_midnight():
        await bot.send(ev, '日期即将变更，请第二天再进行交换', at_sender=True)
        return
    
    group_id = ev.group_id
    user_id = ev.user_id
      
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)
    
    target_id = None
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    if not target_id:
        if ev.message.extract_plain_text().strip() != "":
            # 谈论交换老婆
            return
        await bot.send(ev, '你想和谁交换？请@他', at_sender=True)
        return    
    # 检查是否尝试交换给自己
    if user_id == target_id:
        await bot.send(ev, '左手换右手？', at_sender=True)
        return
    # 检查发起者或目标者是否已经在任何交换请求中
    if await ex_manager.is_exchange_active(user_id, target_id, group_id):
        await bot.send(ev, '双方有人正在进行换妻play中，请稍后再试', at_sender=True)
        return
    
    async with AsyncSessionFactory() as session:
        async with session.begin():
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            ug_target = await ug_sv.add_and_get_user_group(target_id, group_id)

            # 获得双方的当前老婆信息
            current_sv = await CurrentSvFactory(session).create()
            ug_wife = await current_sv.get_current_character(ug)
            ug_target_wife = await current_sv.get_current_character(ug_target)
            if not ug_wife or not ug_target_wife:
                await bot.send(ev, '需要双方都有老婆才能交换', at_sender=True)
                return
            # 添加交易状态锁，防止交易期间他人再对双方发起交易，或重复发起交易
            await ex_manager.add_exchange(user_id, target_id, group_id)
            # 启动超时计时器
            asyncio.create_task(handle_timeout(ug, ug_target, ug_wife, ug_target_wife))
            # 发送交换请求
            await bot.send(ev, f'[CQ:at,qq={target_id}] 用户 [CQ:at,qq={user_id}] 想要和你交换老婆，是否同意？\n如果同意(拒绝)请在60秒内发送“同意(拒绝)”', at_sender=False)

# 交换老婆超时处理
async def handle_timeout(ug: UserGroup, ug_target: UserGroup, wife: Character, wife_target: Character):
    await asyncio.sleep(60)
    if await ex_manager.get_initiator_if_target(ug_target.user_id, ug_target.group_id):
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    event_sv = await EventSvFactory(session).create()
                    await event_sv.add_double_event(ug, ug_target, wife, wife_target, "交换老婆", "超时")
                    await hoshino.get_bot().send_group_msg(group_id=ug.group_id, message=f"[CQ:at,qq={ug.user_id}] 你的交换请求已超时，对方无视了你")
            await ex_manager.remove_exchange(ug.user_id, ug.group_id)

# 交换老婆回复处理
@sv.on_message('group')
async def ex_wife_reply(bot, ev: CQEvent):
    # 如果该群组内没有交换请求
    if not await ex_manager.has_active_exchanges_in_group(ev.group_id):
        return
    # 存在交换请求
    group_id = ev.group_id
    target_id = ev.user_id
    # 判断该用户是否是被申请者，返回申请者id就说明是
    user_id = await ex_manager.get_initiator_if_target(target_id, group_id)
    # 不为空则说明有记录
    if user_id:
        # 提取消息文本
        keyword = "".join(seg.data['text'].strip() for seg in ev.message if seg.type == 'text')

        # 寻找关键词的索引位置
        agree_index = keyword.find('同意')
        disagree_index = keyword.find('不同意')
        refuse_index = keyword.find('拒绝')
        # 如果“同意”、“不同意”和“拒绝”都没有出现，则什么都不做
        if agree_index == -1 and disagree_index == -1 and refuse_index == -1:
            return
        # 找出“不同意”和“拒绝”首次出现的位置
        disagree_first_index = min(filter(lambda x: x != -1, [disagree_index, refuse_index]), default=-1)

        # 进行判断
        if disagree_first_index != -1 and (agree_index == -1 or disagree_first_index < agree_index):
            # 如果找到“不同意”或“拒绝”，且它们在“同意”之前出现，或者没找到“同意”
            await handle_ex_wife(user_id, target_id, group_id, False)
            await bot.send(ev, '对方拒绝了你的交换请求', at_sender=True)
        elif agree_index != -1:
            # 如果找到“同意”，且它在“不同意”或“拒绝”之前出现，或者“不同意”或“拒绝”不存在
            await handle_ex_wife(user_id, target_id, group_id, True)
            await bot.send(ev, '交换成功', at_sender=True)
        # 删除exchange_manager中该用户的请求
        await ex_manager.remove_exchange(user_id, group_id)

#—————————————————————牛老婆—————————————————————#

@sv.on_prefix('牛老婆')
@sv.on_suffix('牛老婆')
async def ntr_wife(bot, ev: CQEvent):
    if await is_near_midnight():
        await bot.send(ev, '日期即将变更，请第二天再牛', at_sender=True)
        return
    group_id = ev.group_id
    user_id = ev.user_id
      
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)
    
    # 牛老婆次数限制
    if not _ntr_lmt.check(key):
        await bot.send(ev, _ntr_max_notice, at_sender=True)
        return
    
    target_id = None
    # 提取目标用户的QQ号
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    if not target_id:
        if ev.message.extract_plain_text().strip() != "":
            return
        await bot.send(ev, '请@一个要下手的目标', at_sender=True)
        return
    # 检查是否尝试交换给自己
    if user_id == target_id:
        await bot.send(ev, '不能牛自己', at_sender=True)
        return
    # 检查发起者或目标者是否已经在任何交换请求中
    if await ex_manager.is_exchange_active(user_id, target_id, group_id):
        await bot.send(ev, '双方有人正在进行换妻play中，请稍后再牛', at_sender=True)
        return
    
    async with AsyncSessionFactory() as session:
        async with session.begin():
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            ug_target = await ug_sv.add_and_get_user_group(target_id, group_id)

            # 获得对方的当前老婆信息
            current_sv = await CurrentSvFactory(session).create()
            ug_wife = await current_sv.get_current_character(ug)
            ug_target_wife = await current_sv.get_current_character(ug_target)
            # 检查对方是否有老婆
            if not ug_target_wife:
                await bot.send(ev, '需要对方有老婆才能牛', at_sender=True)
                return
            # 满足牛人条件，添加进交换请求列表中，防止牛人期间他人对双方发起交易，产生bug
            await ex_manager.add_exchange(user_id, target_id, group_id)
            # 事件记录服务
            event_sv = await EventSvFactory(session).create()
            
            if random.random() < ntr_possibility: 
                # 记录一次“牛老婆”动作,成功
                await event_sv.add_double_event(ug, ug_target, ug_wife, ug_target_wife, "牛老婆", "成功")
                # user相当于通过牛老婆的方式抽到一个新老婆
                ugc_sv = await UGCharacterSvFactory(session).create()
                # 建立关联，或者增加一次牛老婆获得次数
                await ugc_sv.add_or_update_character_by_acquisition_method(ug, ug_target_wife, AcqMethod.NTR)
                # 更新当前老婆
                await current_sv.add_or_update_current_character(ug, ug_target_wife)
                # 目标用户当前老婆置空
                await current_sv.remove_cid_by_user_group(ug_target)
                nick = await get_card_by_uid_gid(
                    user_id=target_id,
                    group_id=group_id
                )
                await bot.send(ev, f'你的阴谋已成功！已成功将 {nick} 的老婆占为己有', at_sender=True)
                # 被牛走的人，补偿一次牛老婆机会
                _ntr_lmt.increase(f"{ug_target.user_id}_{group_id}", int(-1))
            else:
                # 记录一次“牛老婆”动作,失败
                await event_sv.add_double_event(ug, ug_target, ug_wife, ug_target_wife, "牛老婆", "失败")
                await bot.send(ev, f'你的阴谋失败了，黄毛被干掉了，黄毛被干掉了！你还有{_ntr_max - _ntr_lmt.get_num(key)}条命', at_sender=True)
            # 清除交换请求锁
            await ex_manager.remove_exchange(user_id, group_id)
            # 牛老婆次数减少
            _ntr_lmt.increase(key)
    
# 重置牛老婆次数限制
@sv.on_prefix('重置牛老婆')
@sv.on_suffix('重置牛老婆')
async def reset_ntr_wife(bot, ev: CQEvent):
    # 获取QQ信息
    user_id = ev.user_id
    group_id = ev.group_id
    # # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id not in hoshino.config.SUPERUSERS:
        await bot.send(ev,"该功能仅限bot管理员使用")
        return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv < sv.manage_priv:
    #     await bot.send(ev,"该功能仅限群管理员或为bot设置的超级管理员使用")
    #     return
    target_id = None
    # 提取目标用户的QQ号
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    target_id = target_id or user_id
    _ntr_lmt.reset(f"{target_id}_{group_id}")
    await bot.send(ev,"已重置次数")

#————————————————————日老婆——————————————————————#

@sv.on_fullmatch('日老婆')
async def mating_wife(bot, ev: CQEvent):
    group_id = ev.group_id
    user_id = ev.user_id
      
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)
    
    # 日老婆CD
    if not _mating_lmt.check(key):
        await bot.send(ev, f'贤者时间，请等待{format_seconds(_mating_lmt.left_time(key))}')
        return
    
    # 获得当日老婆
    async with AsyncSessionFactory() as session:
        async with session.begin():
            try:
                ug_sv = await UserGroupSvFactory(session).create()
                ug = await ug_sv.add_and_get_user_group(user_id, group_id)
                current_sv = await CurrentSvFactory(session).create()
                ug_wife = await current_sv.get_current_character(ug)
                if not ug_wife:
                    await bot.send(ev, "日天日地日空气？请得到老婆后再日")
                    return
                action_sv = await ActionSvFactory(session).create()
                
                # 事件记录服务
                event_sv = await EventSvFactory(session).create()
                await event_sv.add_single_event(ug, ug_wife, "日老婆", "")
                
                # 日老婆次数加一
                await action_sv.update_action_count(ug, ug_wife, ActionType.MATING)
            except Exception as e:
                await bot.send(ev, "注入失败！")
                hoshino.logger.error(f"日老婆异常: {e}")
                return
            await bot.send(ev, f"誰にでも優しくしないで, でもそこが好き！\n({ug_wife.name}好感度加一)")
            # 获取特定群组的CD时间
            cd_time = cd_manager.get_group_cd(f"{group_id}")
            # 日老婆CD
            _mating_lmt.start_cd(key, cd_time)

#———————————————————添加老婆—————————————————————#

@sv.on_prefix('添加老婆')
@sv.on_suffix('添加老婆')
async def add_wife(bot, ev: CQEvent):
    # 获取QQ信息
    user_id = ev.user_id
    group_id = ev.group_id
    key = f"{user_id}_{group_id}"
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
    
    message_text = ev.message.extract_plain_text().strip()
    keywords = message_text.split()
    
    if len(keywords) == 1:
        # 只有一个关键词时，默认卡池名为 default
        name = keywords[0]
        pool_name = 'default'
    elif len(keywords) == 2:
        # 有两个关键词时，正常处理，提取老婆的名字和卡池名
        name, pool_name = keywords
    else:
        await bot.send(
            ev,
            f"请提供老婆名和可选的卡池名(默认default)\n"
            f"卡池名称需'纯英文'且为'小写字母'或下划线'_'\n"
            f"老婆名和卡池名用空格隔开，如:\n"
            f"添加老婆 老婆名 [图片]\n"
            f"添加老婆 老婆名 swimwear [图片]")
        return
    
    # 检测卡池名是否是纯英文且为小写字母或下划线
    if not re.match("^[a-z_]+$", pool_name) or len(pool_name) > 30:
        await bot.send(ev, "卡池名需为纯英文小写字母或下划线'_'，且长度不超过30个字符，请重新输入。")
    # 获得图片信息
    ret = re.search(r"\[CQ:image,file=(.*)?,url=(.*)\]", str(ev.message))
    if not ret:
        # 未获得图片信息
        await bot.send(ev, '请附带二次元老婆图片~')
        return
    # 检查是否同名，同名禁止添加，需要到更新老婆去更新
    async with AsyncSessionFactory() as session:
        async with session.begin():
            character_sv = await CharacterSvFactory(session).create()
            existing_character = await character_sv.get_character_by_name(name)
            if existing_character:
                await bot.send(ev, '出现重名，请使用[更新老婆]命令')
                return
            # 获取下载url
            url = ret.group(2)
            # 下载图片保存到本地并获取文件名
            try:
                image_name = await download_async(url, name, pool_name)
            except Exception as e:
                hoshino.logger.exception(f'下载图片失败:{e}')
                await bot.send(ev, '下载图片失败')
                return
            # 插入数据库
            try:
                character_sv = await CharacterSvFactory(session).create()
                await add_single_character(character_sv, image_name, pool_name)
            except Exception as e:
                hoshino.logger.exception(f'添加新老婆信息失败:{e}')
                await bot.send(ev, '添加新老婆信息失败')
                return
            await bot.send(ev, '信息已增加~')
    # 如果不是超级管理员，增加用户的添加老婆使用次数（管理员可一天增加多次）
    if user_id not in hoshino.config.SUPERUSERS:
        _add_lmt.increase(key)

#———————————————————更新老婆—————————————————————#

# 同名则更新pool_name和image_name、image_path(cqcode)
@sv.on_prefix('更新老婆')
@sv.on_suffix('更新老婆')
async def update_wife(bot, ev: CQEvent):
    # 获取QQ信息
    user_id = ev.user_id
    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id not in hoshino.config.SUPERUSERS:
        return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv < sv.manage_priv:
        # return
    message_text = ev.message.extract_plain_text().strip()
    keywords = message_text.split()
    
    if len(keywords) == 1:
        # 只有一个关键词时，默认卡池名为 原卡池名
        name = keywords[0]
        pool_name = ""
    elif len(keywords) == 2:
        # 有两个关键词时，正常处理，提取老婆的名字和卡池名
        name, pool_name = keywords
    else:
        await bot.send(
            ev,
            f"请提供老婆名和可选的卡池名(默认原卡池名)\n"
            f"卡池名称需'纯英文'且为'小写字母'或下划线'_'\n"
            f"老婆名和卡池名用空格隔开，如:\n"
            f"更新老婆 老婆名 [图片]\n"
            f"更新老婆 老婆名 swimwear [图片]")
        return
    
    # 检测卡池名是否是纯英文且为小写字母或下划线
    if not re.match("^[a-z_]*$", pool_name) or len(pool_name) > 30:
        await bot.send(ev, "卡池名需为纯英文小写字母或下划线'_'，且长度不超过30个字符，请重新输入。")
        return
    # 获得图片信息
    ret = re.search(r"\[CQ:image,file=(.*)?,url=(.*)\]", str(ev.message))
    if not ret:
        # 未获得图片信息
        await bot.send(ev, '请附带二次元老婆图片~')
        return
    # 检查是否同名，不同名让他去添加，同名就更新
    async with AsyncSessionFactory() as session:
        async with session.begin():
            character_sv = await CharacterSvFactory(session).create()
            existing_character = await character_sv.get_character_by_name(name)
            if not existing_character:
                await bot.send(ev, '同名角色不存在，请使用[添加老婆]命令')
                return
            if pool_name == "":
                pool_name = existing_character.pool_name
            # 备份原图片文件
            backup_path, src_path, backup_image_name, backup_pool_name = await backup_character_image(existing_character.image_name, existing_character.pool_name)
            # 下载新图片文件
            url = ret.group(2)
            try:
                new_image_name = await download_async(url, name, pool_name)
            except Exception as e:
                # 恢复原图片文件
                await restore_character_image(backup_path, src_path)
                hoshino.logger.exception(f'下载图片失败: {e}')
                await bot.send(ev, '下载图片失败')
                return
            # 更新信息
            try:
                await update_single_character(character_sv, existing_character, new_image_name, pool_name)
                # 删除备份的原图片
                await delete_image_and_empty_folder(backup_image_name, backup_pool_name)
                await bot.send(ev, '更新信息成功')
            except Exception as e:
                # 删除下载的新图片
                await delete_image_and_empty_folder(new_image_name, pool_name)
                # 恢复原图片文件
                await restore_character_image(backup_path, src_path)
                hoshino.logger.exception(f'更改角色信息数据失败: {e}')
                await bot.send(ev, '更改角色信息数据失败')


# 重命名老婆
@sv.on_prefix('重命名老婆')
@sv.on_suffix('重命名老婆')
async def rename_wife(bot, ev: CQEvent):
    user_id = ev.user_id
    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id not in hoshino.config.SUPERUSERS:
        return

    message_text = ev.message.extract_plain_text().strip()
    keywords = message_text.split()
    
    if len(keywords) != 2:
        await bot.send(
            ev,
            f"请提供当前老婆名和新老婆名，用空格隔开，如:\n"
            f"重命名老婆 当前老婆名 新老婆名")
        return
    
    old_name, new_name = keywords

    async with AsyncSessionFactory() as session:
        async with session.begin():
            character_sv = await CharacterSvFactory(session).create()
            existing_character = await character_sv.get_character_by_name(old_name)
            if not existing_character:
                await bot.send(ev, '当前老婆名不存在，请确认后重新输入')
                return
            
            # 重命名文件
            old_image_name_extension = os.path.splitext(existing_character.image_name)[1]
            new_image_name = f"{new_name}{old_image_name_extension}"
            try:
                await rename_image_file(existing_character.image_name, new_image_name, existing_character.pool_name)
            except (FileNotFoundError, OSError) as e:
                hoshino.logger.exception(f'重命名图片文件失败: {e}')
                await bot.send(ev, '重命名失败')
                return
            
            # 更新数据库信息
            try:
                await update_single_character(character_sv, existing_character, new_image_name, existing_character.pool_name)
                await bot.send(ev, f"成功将老婆名从 {old_name} 更改为 {new_name}")
            except Exception as e:
                # 如果更新数据库失败，恢复文件名
                try:
                    await rename_image_file(new_image_name, existing_character.image_name, existing_character.pool_name)
                except (FileNotFoundError, OSError) as rename_error:
                    hoshino.logger.exception(f'恢复图片文件名失败: {rename_error}')
                    await bot.send(ev, '重命名失败，且恢复原文件名失败')
                    return
                hoshino.logger.exception(f'更新角色信息失败: {e}')
                await bot.send(ev, '更新角色信息失败')
                
#———————————————————删除老婆—————————————————————#

@sv.on_prefix('删除老婆')
@sv.on_suffix('删除老婆')
async def remove_wife(bot, ev: CQEvent):
    # 获取QQ信息
    user_id = ev.user_id
    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if user_id not in hoshino.config.SUPERUSERS:
        return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv < sv.manage_priv:
        # return
    # 获得要删除的名字
    name = ev.message.extract_plain_text().strip()
    async with AsyncSessionFactory() as session:
        async with session.begin():
            character_sv = await CharacterSvFactory(session).create()
            try:
                image_name, pool_name = await character_sv.delete_charactera_by_name(name)
                await delete_image_and_empty_folder(image_name, pool_name)
                await bot.send(ev, f"删除 {name} 成功")
            except Exception as e:
                hoshino.logger.exception(f"删除角色失败：{e}")
                await bot.send(ev, f"未找到 {name}")

#———————————————————离婚老婆—————————————————————#

@sv.on_prefix('离婚')
@sv.on_suffix('离婚')
async def reset_darw_wife(bot, ev: CQEvent):
    # 获取QQ群、群用户QQid
    group_id = ev.group_id
    user_id = ev.user_id
    
    # 命令频率限制
    key = f"{user_id}_{group_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)
    
    # 离婚次数限制
    if not _divorce_lmt.check(key):
        await bot.send(ev, _divorce_max_notice, at_sender=True)
        return
    
    # 此注释的代码是仅限bot超级管理员可以帮别人离婚，有需可启用并将下面判断权限的代码注释掉
    if user_id in hoshino.config.SUPERUSERS:
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv > sv.manage_priv:    
        # 和抽老婆一样，帮别人离婚的
        target_id = None
        # 提取目标用户的QQ号
        for seg in ev.message:
            if seg.type == 'at' and seg.data['qq'] != 'all':
                target_id = int(seg.data['qq'])
                break
        # 没有@任何人，且没有附带其他消息，只有“离婚”命令
        if not target_id and ev.message.extract_plain_text().strip() == "":
            pass
        elif not target_id:
            # 谈论“离婚”不做反应
            return
        else:
            user_id=target_id
    elif ev.message.extract_plain_text().strip() != "":
        # 群友谈论离婚
        return
    
    async with AsyncSessionFactory() as session:
        async with session.begin():
            user_group_sv = await UserGroupSvFactory(session).create()
            # 获得user_group，如果没有会自动添加
            ug = await user_group_sv.add_and_get_user_group(user_id, group_id)
            # 获得ug对应的当前角色信息
            current_ugc_sv = await CurrentSvFactory(session).create()
            character = await current_ugc_sv.get_current_character(ug)
            if character:
                # 清除老婆信息
                await current_ugc_sv.remove_cid_by_user_group(ug)
                stats_sv = await ActionSvFactory(session).create()
                await stats_sv.update_action_count(ug, character, ActionType.DIVORCE)
                
                # 事件记录服务
                event_sv = await EventSvFactory(session).create()
                await event_sv.add_single_event(ug, character, "离婚", "")
                await bot.send(ev, f"当前老婆信息：{character.name}, 解除婚姻成功", at_sender=True)
                if ev.user_id not in hoshino.config.SUPERUSERS:
                    # 不是超级管理员，限制次数
                    _divorce_lmt.increase(key)
            else:
                await bot.send(ev, f"没老婆不能离婚", at_sender=True)

#——————————————————设置日老婆CD——————————————————#

@sv.on_prefix(('设置日老婆CD', '设置日老婆cd',))
async def set_mating_cd(bot, ev: CQEvent):
    # 获取QQ群、群用户QQid
    group_id = ev.group_id
    user_id = ev.user_id
    # 此注释的代码是仅限bot超级管理员可以修改
    if user_id not in hoshino.config.SUPERUSERS:
        return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    # u_priv = priv.get_user_priv(ev)
    # if u_priv < sv.manage_priv:
        # return
    message_text = ev.message.extract_plain_text().strip()
    
    # 判断message_text是否为纯数字
    if not message_text.isdigit():
        await bot.send(ev, "CD时间必须为纯数字。")
        return

    # 将message_text转换为整数，表示新的CD时间
    new_cd_time = int(message_text)

    # 使用cd_manager设置群组CD时间
    cd_manager.set_group_cd(f"{group_id}", new_cd_time)
    await bot.send(ev, f"CD设置为：{new_cd_time}秒")
    
#—————————————————清理不在群的用户————————————————#

@sv.on_fullmatch('清理抽老婆用户')
async def clear_wife_users(bot, ev: CQEvent):
    # 此注释的代码是仅限bot超级管理员使用，有需可启用并将下面判断权限的代码注释掉
    if ev.user_id not in hoshino.config.SUPERUSERS:
        return
    try:
        # 获得所有群
        group_list = await bot.get_group_list(no_cache=True)
        if group_list:
            group_ids = [group['group_id'] for group in group_list]
            async with AsyncSessionFactory() as session:
                async with session.begin():
                    user_group_sv = await UserGroupSvFactory(session).create()
                    try:
                        cleaned_group_ids = await user_group_sv.delete_groups_not_in_list(group_ids)
                        hoshino.logger.info(f"清理后的群ID列表：{cleaned_group_ids}")
                    except Exception as e:
                        hoshino.logger.error(f"清理多余的群失败：{e}")
                        await bot.send(ev, "清理多余的群失败，请检查日志", at_sender=True)
                        return
                    # 收集所有群的所有用户 ID
                    all_user_ids = set()
                    for group_id in cleaned_group_ids:
                        # 获得群成员信息列表
                        member_list = await bot.get_group_member_list(group_id=group_id, no_cache=True)
                        if member_list:
                            user_ids = [member['user_id'] for member in member_list]
                            all_user_ids.update(user_ids)
                        else:
                            hoshino.logger.warning(f"未能获取群{group_id}的成员列表或成员列表为空")
                            await bot.send(ev, f"未能获取群{group_id}的成员列表或成员列表为空", at_sender=True)

                    try:
                        # 删除不在任何群中的用户
                        await user_group_sv.delete_users_not_in_list(list(all_user_ids))
                        hoshino.logger.info("清理所有群中不存在的用户信息成功")
                        await bot.send(ev, "清理所有群中不存在的用户信息成功！", at_sender=True)
                    except Exception as e:
                        hoshino.logger.error(f"清理用户信息失败：{e}")
                        await bot.send(ev, "清理用户信息失败，请检查日志", at_sender=True)
                        return
    except Exception as e:
        hoshino.logger.error(f"清理抽老婆用户操作失败：{e}")
        await bot.send(ev, "清理抽老婆用户操作失败，请检查日志", at_sender=True)

#—————————————————数据统计————————————————#

# 不带老婆名
async def all_wife_archive(bot, ev: CQEvent):
    group_id = ev.group_id
    user_id = ev.user_id
    async with AsyncSessionFactory() as session:
        async with session.begin():
            # 获得ug
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            # 数据统计服务
            statistics_sv = await StatisticsSvFactory(session).create()
            
            # 收集所有统计数据
            messages = ["\n本群统计："]
            
            # 获得本群被抽到最多的老婆
            character_most_drawn, count_most_drawn = await statistics_sv.get_most_frequent_character_in_group(
                user_group=ug,
                event_type="抽老婆"
            )
            if character_most_drawn:
                messages.append(f"- 被抽到最多的角色是：{character_most_drawn.name}，{count_most_drawn}次")
                
            # 被牛最多的老婆
            character_most_ntr, count_most_ntr = await statistics_sv.get_most_frequent_character_in_group(
                user_group=ug, 
                event_type="牛老婆", 
                is_double=True
                )
            if character_most_ntr:
                messages.append(f"- 被牛最多次的角色是：{character_most_ntr.name}，{count_most_ntr}次")
            
            # 被牛到手最多的老婆
            character_most_ntr_success, count_most_ntr_success = await statistics_sv.get_most_frequent_character_in_group(
                user_group=ug, 
                event_type="牛老婆", 
                result="成功", 
                is_double=True
                )
            if character_most_ntr_success:
                messages.append(f"- 被牛到手最多的角色是：{character_most_ntr_success.name}，{count_most_ntr_success}次")
            
            # 被请求交换最多的老婆
            character_most_ntr, count_most_ntr = await statistics_sv.get_most_frequent_character_in_group(
                user_group=ug, 
                event_type="交换老婆", 
                is_double=True
                )
            if character_most_ntr:
                messages.append(f"- 被请求交换最多的老婆：{character_most_ntr.name}，{count_most_ntr}次")
            
            # 被成功交换到手最多的老婆
            character_most_ntr, count_most_ntr = await statistics_sv.get_most_frequent_character_in_group(
                user_group=ug, 
                event_type="交换老婆",
                result="同意",
                is_double=True
                )
            if character_most_ntr:
                messages.append(f"- 被成功交换到手最多的老婆：{character_most_ntr.name}，{count_most_ntr}次")
                
            # 本群好感度最高的角色
            character_highest_mating, count_highest_mating = await statistics_sv.get_top_action_count_character_in_group(user_group=ug, action=ActionType.MATING)
            if character_highest_mating:
                messages.append(f"- 好感度最高的角色是：{character_highest_mating.name}，好感度：{count_highest_mating}")
            
            # 本群离婚最多的用户
            character_most_divorce, count_most_divorce = await statistics_sv.get_top_action_count_character_in_group(user_group=ug, action=ActionType.DIVORCE)
            if character_most_divorce:
                messages.append(f"- 离婚最多的角色是：{character_most_divorce.name}，离婚：{count_most_divorce}次")
            
            await bot.send(ev, "\n".join(messages), at_sender=True)

@sv.on_prefix('老婆档案')
@sv.on_suffix('老婆档案')
async def wife_archive(bot, ev: CQEvent):
    group_id = ev.group_id
    user_id = ev.user_id
    key = f"{user_id}_{group_id}"
    # 查询CD
    if not _archive_lmt.check(key):
        await bot.send(ev, f'等待{format_seconds(_archive_lmt.left_time(key))}后可再次查询')
        return
    _archive_lmt.start_cd(key)
    # 获取角色名
    name = ev.message.extract_plain_text().strip()
    if name == "":
        await all_wife_archive(bot, ev)
        return
    # 带老婆名
    async with AsyncSessionFactory() as session:
        async with session.begin():
            # 解析老婆名,获得角色
            character_sv = await CharacterSvFactory(session).create()
            possible_names = await character_sv.search_character_by_partial_name(name)
            if not possible_names:
                await bot.send(ev, f"未找到相似名称角色")
                return
            elif isinstance(possible_names, Character):
                character = possible_names
            elif len(possible_names) > 1:
                possible_names_str = "\n".join(possible_names)
                await bot.send(ev, f"您可能要找的是：\n{possible_names_str}")
                return
            else:
                character = await character_sv.get_character_by_name(possible_names[0])
            
            # 获得ug
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            # 获得ug_character_stats
            ugc_sv = await UGCharacterSvFactory(session).create()
            ugc_with_stats = await ugc_sv.get_user_group_character_with_stats(ug, character)

            # 数据统计
            statistics_sv = await StatisticsSvFactory(session).create()
            
            member_info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
            nick = member_info.get('card', '') or member_info.get('nickname', '') or str(user_id)
            # 收集所有统计数据
            messages = [f"{nick}个人统计："]
            
            messages.append(f"姓名：{character.name}")
            messages.append(f"卡池：{character.pool_name}")
            messages.append(character.image_path)

            if ugc_with_stats:
                stats: Stats = ugc_with_stats.stats
                messages.append(f"你们相遇的时间是：{ugc_with_stats.acquisition_time.strftime('%Y-%m-%d %H:%M:%S')}")
                messages.append(f"- 你一共抽到她：{stats.draw_count}次")
                messages.append(f"- 你一共牛到她：{stats.acquired_by_ntr_count}次")
                messages.append(f"- 你一共换到她：{stats.acquired_by_ex_count}次")
                messages.append(f"- 你们之间的好感有：{stats.mating_count}")
                messages.append(f"- 你们离婚的次数是：{stats.divorce_count}")
                self_total_draw_count = await statistics_sv.get_total_count_by_type(
                    user_group=ug, 
                    count_type=AcqMethod.DRAW,
                    for_entire_group=False
                )
                draw_percent = (stats.draw_count / self_total_draw_count) * 100 if self_total_draw_count != 0 else 0
                messages.append(f"- 你抽到她的概率是：{draw_percent:.2f}%")
                self_total_ntr_count = await statistics_sv.get_total_count_by_type(
                    user_group=ug, 
                    count_type=AcqMethod.NTR,
                    for_entire_group=False
                )
                ntr_percent = (stats.acquired_by_ntr_count / self_total_ntr_count) * 100 if self_total_ntr_count != 0 else 0
                messages.append(f"- 你牛到她的概率是：{ntr_percent:.2f}%")
                
            total_darw_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=AcqMethod.DRAW, character=character)
            messages.append(f"- 本群一共抽到她：{total_darw_count}次")
            total_ntr_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=AcqMethod.NTR, character=character)
            messages.append(f"- 本群一共牛到她：{total_ntr_count}次")
            total_ex_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=AcqMethod.EXCHANGE, character=character)
            messages.append(f"- 本群一共换到她：{total_ex_count}次")
            total_mating_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=ActionType.MATING, character=character)
            messages.append(f"- 她在本群的总好感度：{total_mating_count}次")
            total_divorce_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type= ActionType.DIVORCE, character=character)
            messages.append(f"- 她在本群离婚：{total_divorce_count}次")
            
            try:
                await bot.send(ev, "\n".join(messages), at_sender=True)
            except Exception as e:
                hoshino.logger.error(f"老婆档案{character.name}图片发送失败:{e}")
                messages.pop(3)
                await bot.send(ev, "\n".join(messages), at_sender=True)

async def all_members_archive(bot, ev: CQEvent):
    group_id = ev.group_id
    user_id = ev.user_id
    async with AsyncSessionFactory() as session:
        async with session.begin():
            # 获得ug
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            # 数据统计服务
            statistics_sv = await StatisticsSvFactory(session).create()
            character_sv = await CharacterSvFactory(session).create()
            total_character_count = await character_sv.count()
            
            messages = ["\n本群统计："]
            
            total_darw_count = await statistics_sv.get_total_count_by_type(
                ug, 
                AcqMethod.DRAW,
                )
            messages.append(f"- 本群总计抽老婆次数：{total_darw_count}次")
            
            total_ntr_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆"
            )
            messages.append(f"- 本群总计牛老婆次数：{total_ntr_count}次")
            
            total_ntr_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆",
                result="成功"
            )
            messages.append(f"- 本群成功牛老婆总次数：{total_ntr_success_count}次")
            
            total_ex_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="交换老婆",
                result="同意"
            )
            messages.append(f"- 本群成功交换老婆总次数：{total_ex_success_count}次")
            
            total_mating_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=ActionType.MATING)
            messages.append(f"- 本群总好感度：{total_mating_count}")
            
            total_divorce_count = await statistics_sv.get_total_count_by_type(user_group=ug, count_type=ActionType.DIVORCE)
            messages.append(f"- 本群离婚总次数：{total_divorce_count}")
                       
            most_darwn_ug_id, most_darwn_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="抽老婆",
                is_double=False
            )
            if most_darwn_ug_id:
                most_darwn_ug = await ug_sv.get_user_group_by_id(most_darwn_ug_id)
                most_darwn_ug_nick = await get_card_by_uid_gid(
                    user_id=most_darwn_ug.user_id,
                    group_id=group_id
                )
                messages.append(f"- 本群抽老婆次数最多的用户是：{most_darwn_ug_nick}, {most_darwn_count}次")
            
            most_darwn_new_ug_id, most_darwn_new_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="抽老婆",
                result="出新",
                is_double=False
            )
            if most_darwn_new_ug_id:
                most_darwn_new_ug = await ug_sv.get_user_group_by_id(most_darwn_new_ug_id)
                most_darwn_new_ug_nick = await get_card_by_uid_gid(
                    user_id=most_darwn_new_ug.user_id,
                    group_id=group_id
                )
                messages.append(f"- 本群获得老婆最多的用户是：{most_darwn_new_ug_nick}, {most_darwn_new_count}/{total_character_count}")
            
            mating_most_target_id, mating_most_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="日老婆",
                is_double=False
            )
            if mating_most_target_id:
                mating_most_target_ug = await ug_sv.get_user_group_by_id(mating_most_target_id)
                mating_most_target_ug_nick = await get_card_by_uid_gid(
                    user_id=mating_most_target_ug.user_id,
                    group_id=group_id
                )
                messages.append(f"- 本群总好感度最高的用户是：{mating_most_target_ug_nick}, {mating_most_count}")
            
            divorce_most_target_id, divorce_most_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="离婚",
                is_double=False
            )
            if divorce_most_target_id:
                divorce_most_target_ug = await ug_sv.get_user_group_by_id(divorce_most_target_id)
                divorce_most_target_ug_nick = await get_card_by_uid_gid(
                    user_id=divorce_most_target_ug.user_id,
                    group_id=group_id
                )
                messages.append(f"- 本群离婚次数最多的用户是：{divorce_most_target_ug_nick}, {divorce_most_count}")
            
            # 个人统计
            messages.append("\n个人统计：")
            
            self_darwn_new_count = await statistics_sv.get_single_event_count(
                user_group=ug,
                event_type="抽老婆",
                result="出新"
            )
            messages.append(f"- 你的老婆解锁数：{self_darwn_new_count}/{total_character_count}")
            
            
            self_darw_count = await statistics_sv.get_total_count_by_type(ug, AcqMethod.DRAW, for_entire_group=False)
            messages.append(f"- 你的抽老婆总次数：{self_darw_count}次")
            
            self_ntr_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆",
                for_entire_group=False
            )
            messages.append(f"- 你的牛老婆总次数：{self_ntr_count}次")
            
            self_ntr_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆",
                result="成功",
                for_entire_group=False
            )
            self_ntr_percent = (self_ntr_success_count / self_ntr_count) * 100 if self_ntr_count != 0 else 0
            messages.append(f"- 你的成功牛老婆总次数：{self_ntr_success_count}次, 成功率:{self_ntr_percent:.2f}%")
            
            self_ex_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="交换老婆",
                result="同意",
                is_user_receiver=True,
                for_entire_group=False
            )
            messages.append(f"- 你成功交换到老婆总次数：{self_ex_success_count}次")
            
            self_mating_count = await statistics_sv.get_total_count_by_type(
                user_group=ug, 
                count_type=ActionType.MATING, 
                for_entire_group=False
                )
            messages.append(f"- 你的角色总好感度：{self_mating_count}")
            
            self_divorce_count = await statistics_sv.get_total_count_by_type(
                user_group=ug, 
                count_type=ActionType.DIVORCE,
                for_entire_group=False
                )
            messages.append(f"- 你的离婚总次数：{self_divorce_count}")
            
            favorite_ntr_target_id, fav_ntr_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="牛老婆"
                )
            if favorite_ntr_target_id:
                favorite_ntr_target = await ug_sv.get_user_group_by_id(favorite_ntr_target_id)
                favorite_ntr_target_nick = await get_card_by_uid_gid(
                    user_id=favorite_ntr_target.user_id,
                    group_id=group_id
                )
                messages.append(f"- 你最喜欢牛的群友是：{favorite_ntr_target_nick}，{fav_ntr_count}次")
            
            succ_ntr_target_id, succ_ntr_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="牛老婆",
                result="成功"
                )
            if succ_ntr_target_id:
                succ_ntr_target = await ug_sv.get_user_group_by_id(succ_ntr_target_id)
                succ_ntr_target_nick = await get_card_by_uid_gid(
                    user_id=succ_ntr_target.user_id,
                    group_id=group_id
                )
                messages.append(f"- 你从{succ_ntr_target_nick}牛到老婆次数最多，{succ_ntr_count}次")

            await bot.send(ev, "\n".join(messages), at_sender=True)


@sv.on_prefix('用户档案')
@sv.on_suffix('用户档案')
async def member_archive(bot, ev: CQEvent):
    group_id = ev.group_id
    user_id = ev.user_id
    key = f"{user_id}_{group_id}"
    # 查询CD
    if not _archive_lmt.check(key):
        await bot.send(ev, f'等待{format_seconds(_archive_lmt.left_time(key))}后可再次查询')
        return
    _archive_lmt.start_cd(key)
    
    target_id = None
    # 提取目标用户的QQ号
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    # 没有@任何人，且没有附带其他消息，只有命令
    if not target_id and ev.message.extract_plain_text().strip() == "":
        # 查自己
        await all_members_archive(bot, ev)
        return
    elif not target_id:
        # 没@任何人，但是有其他消息，无视
        return
    else:
        # @某人，替换user_id
        user_id=target_id

    async with AsyncSessionFactory() as session:
        async with session.begin():
            # 获得ug
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            # 数据统计服务
            statistics_sv = await StatisticsSvFactory(session).create()
            character_sv = await CharacterSvFactory(session).create()
            total_character_count = await character_sv.count()
            
            nick = await get_card_by_uid_gid(
                user_id=ug.user_id,
                group_id=ug.group_id
            )
            messages = [f"\n{nick} 个人统计："]
            
            self_darwn_new_count = await statistics_sv.get_single_event_count(
                user_group=ug,
                event_type="抽老婆",
                result="出新"
            )
            messages.append(f"- {nick} 的老婆解锁数：{self_darwn_new_count}/{total_character_count}")
            
            
            self_darw_count = await statistics_sv.get_total_count_by_type(ug, AcqMethod.DRAW, for_entire_group=False)
            messages.append(f"- {nick} 的抽老婆总次数：{self_darw_count}次")
            
            self_ntr_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆",
                for_entire_group=False
            )
            messages.append(f"- {nick} 的牛老婆总次数：{self_ntr_count}次")
            
            self_ntr_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="牛老婆",
                result="成功",
                for_entire_group=False
            )
            self_ntr_percent = (self_ntr_success_count / self_ntr_count) * 100 if self_ntr_count != 0 else 0
            messages.append(f"- {nick} 的成功牛老婆总次数：{self_ntr_success_count}次, 成功率:{self_ntr_percent:.2f}%")
            
            self_ex_success_count = await statistics_sv.get_double_event_count(
                user_group=ug,
                event_type="交换老婆",
                result="同意",
                is_user_receiver=True,
                for_entire_group=False
            )
            messages.append(f"- {nick} 成功交换到老婆总次数：{self_ex_success_count}次")
            
            self_mating_count = await statistics_sv.get_total_count_by_type(
                user_group=ug, 
                count_type=ActionType.MATING, 
                for_entire_group=False
                )
            messages.append(f"- {nick} 的角色总好感度：{self_mating_count}")
            
            self_divorce_count = await statistics_sv.get_total_count_by_type(
                user_group=ug, 
                count_type=ActionType.DIVORCE,
                for_entire_group=False
                )
            messages.append(f"- {nick} 的离婚总次数：{self_divorce_count}")
            
            favorite_ntr_target_id, fav_ntr_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="牛老婆"
                )
            if favorite_ntr_target_id:
                favorite_ntr_target = await ug_sv.get_user_group_by_id(favorite_ntr_target_id)
                favorite_ntr_target_nick = await get_card_by_uid_gid(
                    user_id=favorite_ntr_target.user_id,
                    group_id=group_id
                )
                messages.append(f"- {nick} 最喜欢牛的群友是：{favorite_ntr_target_nick}，{fav_ntr_count}次")
            
            succ_ntr_target_id, succ_ntr_count = await statistics_sv.get_most_frequent_user_group_id(
                user_group=ug,
                event_type="牛老婆",
                result="成功"
                )
            if succ_ntr_target_id:
                succ_ntr_target = await ug_sv.get_user_group_by_id(succ_ntr_target_id)
                succ_ntr_target_nick = await get_card_by_uid_gid(
                    user_id=succ_ntr_target.user_id,
                    group_id=group_id
                )
                messages.append(f"- {nick} 从{succ_ntr_target_nick}牛到老婆次数最多，{succ_ntr_count}次")

            await bot.send(ev, "\n".join(messages), at_sender=True)

#————————————————————图鉴相关————————————————————#
@sv.on_prefix('老婆图鉴')
@sv.on_suffix('老婆图鉴')
async def atlas(bot, ev: CQEvent):
    # 获取QQ群、群用户QQ信息
    group_id = ev.group_id
    user_id = ev.user_id
    # 命令频率限制
    key = f"{group_id}_{user_id}"
    if not _flmt.check(key):
        await bot.send(ev, f'操作太频繁，请在{int(_flmt.left_time(key))}秒后再试')
        return
    _flmt.start_cd(key)

    target_id = None
    # 提取目标用户的QQ号
    for seg in ev.message:
        if seg.type == 'at' and seg.data['qq'] != 'all':
            target_id = int(seg.data['qq'])
            break
    # 检查消息内容是否为空
    if (target_id is None) and ev.message.extract_plain_text().strip() == "":
        target_id = user_id
    elif target_id is None:
        return

    async with AsyncSessionFactory() as session:
        async with session.begin():
            # 获得ug
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(target_id, group_id)
            nick = await get_card_by_uid_gid(
                user_id=ug.user_id,
                group_id=ug.group_id
            )
            # 数据统计服务
            statistics_sv = await StatisticsSvFactory(session).create()
            character_sv = await CharacterSvFactory(session).create()
            # 获取老婆总数
            total_wives_count = await character_sv.count()
            # 获取抽老婆的ID列表
            user_character_id = await statistics_sv.get_user_character_ids(
                user_group=ug,
                event_type="抽老婆",
                result="出新"
            )
            # 加载当前状态
            ntr_atlas_statuses = load_ntr_atlas_statuses(ntr_atlas_status_file)
            if not ntr_atlas_statuses.get(str(group_id), False):
                messages = [f"{nick} 的图鉴为："]
            else:
                messages = [f"{nick} 的图鉴(含NTR)为："]
                # 获取牛老婆成功的ID列表
                user_NTR_true_character_id = await statistics_sv.get_user_NTR_true_character_id(
                    initiator_ug=ug,
                    event_type="牛老婆",
                    result="成功"
                )
                # 合并老婆列表
                user_character_id += user_NTR_true_character_id
                # 转换成集合以去除重复项
                user_character_id_set = set(user_character_id)
                # 转换回列表
                user_character_id = list(user_character_id_set)
            # 获取老婆的名字列表
            user_character_name = await character_sv.get_character_names_by_ids(user_character_id)
            # 用户解锁的总数
            drawn_wives_count = len(user_character_name)
            # 计算行数
            row_num = len_card // COL_NUM if len_card % COL_NUM != 0 else len_card // COL_NUM - 1
            # 得到背景图片
            base = Image.open(FRAME_DIR_PATH + '/frame.png')
            # 调整图像大小:
            base = base.resize((40 + COL_NUM * 80 + (COL_NUM - 1) * 10, 150 + row_num * 80 + (row_num - 1) * 10),
                               Image.ANTIALIAS)
            # 初始化行索引偏移和行偏移:
            row_index_offset = 0
            row_offset = 0
            # 卡片文件名列表:
            cards_list = card_file_names_all
            for index, FileName in enumerate(cards_list):
                row_index = index // COL_NUM + row_index_offset
                col_index = index % COL_NUM
                # 直接检查FileName是否在cards_num中
                f = get_pic(FileName, False) if (FileName in user_character_name) else get_pic(FileName, True)
                base.paste(f, (
                    30 + col_index * 80 + (col_index - 1) * 10,
                    row_offset + 40 + row_index * 80 + (row_index - 1) * 10
                ))
            row_offset += 30
            buf = BytesIO()
            base = base.convert('RGB')
            base.save(buf, format='JPEG')
            base64_str = f'base64://{base64.b64encode(buf.getvalue()).decode()}'
            messages.append(f"[CQ:image,file={base64_str}]")
            messages.append(f"图鉴完成度: {drawn_wives_count} / {total_wives_count}")
            await bot.send(ev, "\n".join(messages))

#————————————————————功能：切换NTR图鉴开关————————————————————#
# 开启后档案和图鉴的解锁数量将统计NTR所得
@sv.on_fullmatch(("切换NTR图鉴开关状态", "切换ntr图鉴开关状态"))
async def switch_atlas_ntr(bot, ev: CQEvent):
    if not check_manage_priv(ev):
        return
    group_id = str(ev.group_id)
    # 加载当前状态
    ntr_atlas_statuses = load_ntr_atlas_statuses(ntr_atlas_status_file)
    # 切换状态
    ntr_atlas_statuses[group_id] = not ntr_atlas_statuses.get(group_id, False)
    # 保存状态
    save_ntr_atlas_statuses(ntr_atlas_statuses, ntr_atlas_status_file)
    # 发送消息
    await bot.send(ev, '图鉴统计NTR已' + ('开启' if ntr_atlas_statuses[group_id] else '关闭'), at_sender=True)


def check_manage_priv(ev):
    """检查用户是否有管理员权限"""
    u_priv = priv.get_user_priv(ev)
    return u_priv >= sv.manage_priv
