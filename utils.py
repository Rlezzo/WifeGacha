import asyncio, os, mimetypes, aiohttp, aiofiles, json
from datetime import datetime, timedelta
from html import unescape
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from hoshino import R, logger, get_bot
from hoshino.config import RES_DIR
from infrastructure.factories import *
from application.services import CharacterAppService
from domain.entities import AcqMethod, Character
from infrastructure.database.connection import AsyncSessionFactory

img_path = os.path.join(os.path.expanduser(RES_DIR), 'img', 'wife')

async def init_characters():
    # 初始化加载老婆数据
    async with AsyncSessionFactory() as session:
        async with session.begin():
            character_sv = await CharacterSvFactory(session).create()
            if await character_sv.count() != 0:
                # 已经录入过数据就不初始化了
                return
            pool_names = [entry for entry in os.listdir(img_path) if os.path.isdir(os.path.join(img_path, entry))] # 卡池文件夹名称list
            for pool_name in pool_names:
                image_names = os.listdir(f'{img_path}/{pool_name}') #获得res/wife/pool_name下文件list
                for image_name in image_names:
                    await add_single_character(character_sv, image_name, pool_name)
                        
async def add_single_character(character_sv, image_name: str, pool_name: str):
    try:
        name = os.path.splitext(image_name)[0]
        img_cq = str(R.img(f'wife/{pool_name}/{image_name}').cqcode)
        new_character = await character_sv.add_character(
            name=f'{name}',
            pool_name=pool_name,
            image_name=f'{image_name}',
            image_path=img_cq
        )
        if new_character:
            logger.info(f"录入老婆: {new_character.name} 卡池：{new_character.pool_name}")
    except Exception as e:
        raise Exception(f"添加角色时发生错误: {e}")
    
async def update_single_character(character_sv: CharacterAppService, character: Character, image_name: str, pool_name: str):
    try:
        img_cq = str(R.img(f'wife/{pool_name}/{image_name}').cqcode)
        character.name = os.path.splitext(image_name)[0]
        character.pool_name = pool_name
        character.image_name = image_name
        character.image_path = img_cq
        await character_sv.update_character(character)
        logger.info(f"更新老婆: {character.name} 卡池：{character.pool_name}")
    except Exception as e:
        raise Exception(f"更新角色时发生错误: {e}")

# 备份原图片
async def backup_character_image(image_name: str, pool_name: str) -> tuple[str, str]:
    src_path = os.path.join(img_path, pool_name, image_name)
    backup_img_name = f"backup_{image_name}"
    backup_pool_name = pool_name
    backup_path = os.path.join(img_path, pool_name, backup_img_name)
    if os.path.exists(src_path):
        os.rename(src_path, backup_path)
    return backup_path, src_path, backup_img_name, backup_pool_name

# 还原原图片
async def restore_character_image(backup_path: str, original_path: str):
    if os.path.exists(backup_path):
        os.rename(backup_path, original_path)
        
# 删除图片并删除可能为空的文件夹        
async def delete_image_and_empty_folder(image_name: str, pool_name: str):
    file_path = os.path.join(img_path, pool_name, image_name)
    if os.path.exists(file_path):
        await asyncio.to_thread(os.remove, file_path)
        folder_path = os.path.dirname(file_path)
        if not os.listdir(folder_path):
            await asyncio.to_thread(os.rmdir, folder_path)

# 重命名老婆图片
async def rename_image_file(old_image_name: str, new_image_name: str, pool_name: str) -> None:
    src_path = os.path.join(img_path, pool_name, old_image_name)
    new_image_path = os.path.join(img_path, pool_name, new_image_name)

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"找不到原文件: {src_path}")
    try:
        os.rename(src_path, new_image_path)
    except Exception as e:
        raise OSError(f'重命名图片文件失败: {e}')

# 处理交换老婆
async def handle_ex_wife(user_id: int, target_id: int, group_id: int, agree: bool):
    async with AsyncSessionFactory() as session:
        async with session.begin():
            ug_sv = await UserGroupSvFactory(session).create()
            ug = await ug_sv.add_and_get_user_group(user_id, group_id)
            ug_target = await ug_sv.add_and_get_user_group(target_id, group_id)

            current_sv = await CurrentSvFactory(session).create()
            ug_wife = await current_sv.get_current_character(ug)
            ug_target_wife = await current_sv.get_current_character(ug_target)
            
            event_sv = await EventSvFactory(session).create()
            
            if agree:
                # 记录“交换老婆”成功
                await event_sv.add_double_event(ug, ug_target, ug_wife, ug_target_wife, "交换老婆", "同意")
                # 交换current表老婆信息
                await current_sv.add_or_update_current_character(ug, ug_target_wife)
                await current_sv.add_or_update_current_character(ug_target, ug_wife)
                # 交换获得，或者交换次数加一
                ugc_sv = await UGCharacterSvFactory(session).create()
                await ugc_sv.add_or_update_character_by_acquisition_method(ug, ug_target_wife, AcqMethod.EXCHANGE)
                await ugc_sv.add_or_update_character_by_acquisition_method(ug_target, ug_wife, AcqMethod.EXCHANGE)
            else:
                await event_sv.add_double_event(ug, ug_target, ug_wife, ug_target_wife, "交换老婆", "拒绝")
                
async def download_async(url: str, name: str, pool_name: str) -> str:
    url = unescape(url)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            # 检查响应状态码
            if resp.status == 404:
                raise ValueError('文件不存在')
            content = await resp.read()  # 读取响应内容
            # 通过MIME类型获取文件扩展名
            try:
                mime = resp.content_type
                extension = mimetypes.guess_extension(mime)
                if not extension:
                    raise ValueError('无法识别的文件类型')
            except Exception as e:
                raise ValueError(f'不是有效文件类型: {e}')
            
            # 生成文件保存路径
            directory = os.path.join(img_path, pool_name)
            abs_path = os.path.join(directory, f'{name}{extension}')
            
            # 确保目录存在
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                raise IOError(f'目录创建失败: {e}')
            
            # 检查文件内容是否为有效图像
            try:
                image = Image.open(BytesIO(content))
                image.verify()  # 验证图像文件的完整性
            except UnidentifiedImageError:
                raise ValueError('下载的内容不是有效的图像文件')
            
            # 区分 GIF 动图和静态图
            if mime == 'image/gif':
                # 压缩 GIF 动图
                image = Image.open(BytesIO(content))
                image = await resize_gif(image)
                async with aiofiles.open(abs_path, 'wb') as f:
                    output = BytesIO()
                    image.save(output, format=image.format, save_all=True, loop=0)
                    await f.write(output.getvalue())
            else:
                # 压缩静态图
                image = Image.open(BytesIO(content))
                image = await resize_image(image)
                async with aiofiles.open(abs_path, 'wb') as f:
                    output = BytesIO()
                    image.save(output, format=image.format)
                    await f.write(output.getvalue())
            
            return f'{name}{extension}'  # 返回文件名

async def resize_image(image: Image) -> Image:
    max_size = 2 * 1024 * 1024  # 2MB
    width, height = image.size
    ratio = (max_size / len(image.tobytes())) ** 0.5  # 初始缩放比例
    
    while True:
        new_size = (int(width * ratio), int(height * ratio))
        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        resized_image.save(output, format=image.format)
        size = output.tell()
        
        if size <= max_size or ratio <= 0.1:
            break
        
        ratio *= 0.9  # 减小缩放比例
    
    output.seek(0)
    return Image.open(output)

async def resize_gif(image: Image) -> Image:
    max_size = 2 * 1024 * 1024  # 2MB
    width, height = image.size
    ratio = (max_size / len(image.tobytes())) ** 0.5  # 初始缩放比例
    
    frames = []
    while True:
        new_size = (int(width * ratio), int(height * ratio))
        for frame in range(0, image.n_frames):
            image.seek(frame)
            frame_image = image.resize(new_size, Image.Resampling.LANCZOS)
            frames.append(frame_image)
        
        output = BytesIO()
        frames[0].save(output, format=image.format, save_all=True, append_images=frames[1:], loop=0)
        size = output.tell()
        
        if size <= max_size or ratio <= 0.1:
            break
        
        ratio *= 0.9  # 减小缩放比例
        frames = []
    
    output.seek(0)
    return Image.open(output)

async def is_near_midnight() -> bool:
    """判断距离跨日是否小于2分钟"""
    # 获得当前时间
    now = datetime.now()
    # 获取第二天的午夜0点时间
    midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
    # 判断是否距离午夜0点小于2分钟
    return now >= midnight - timedelta(minutes=2) and now < midnight

async def get_card_by_uid_gid(user_id: int, group_id: int) -> str:
    """返回群昵称或QQ昵称或qq号"""
    try:
        member_info = await get_bot().get_group_member_info(user_id=user_id, group_id=group_id)
        return member_info.get('card', '') or member_info.get('nickname', '') or str(user_id)
    except Exception as e:
        logger.error(f'获取群成员信息时发生错误: {e}, group_id: {group_id}, user_id: {user_id}')
        return str(user_id)
    
def format_seconds(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}小时{minutes}分{remaining_seconds}秒"
    elif minutes > 0:
        return f"{minutes}分{remaining_seconds}秒"
    else:
        return f"{remaining_seconds}秒"


#————————————————————切换NTR开关初始化————————————————————#
# 载入NTR图鉴状态
def load_ntr_atlas_statuses(filename):
    file_path = os.path.join(os.path.dirname(__file__), 'config', filename)
    try:
        # 文件存在，读取内容到ntr_atlas_statuses
        with open(file_path, 'r', encoding='utf-8') as f:
            ntr_atlas_statuses = json.load(f)
    except FileNotFoundError:
        ntr_atlas_statuses = {}
    return ntr_atlas_statuses

def save_ntr_atlas_statuses(statuses, filename):
    file_path = os.path.join(os.path.dirname(__file__), 'config', filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(statuses, f, ensure_ascii=False, indent=4)