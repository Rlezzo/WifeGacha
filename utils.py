import asyncio, os, mimetypes, httpx, aiofiles, json, ssl
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 配置 SSL 上下文
    ctx = ssl.create_default_context()
    ctx.set_ciphers('ALL')
    
    # 设置超时和异步客户端
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(verify=ctx, headers=headers, timeout=timeout) as client:
        try:
            response = await client.get(url)
            if response.status_code == 404:
                raise ValueError('文件不存在')
            
            content = response.content  # 直接获取二进制内容
            mime = response.headers.get('content-type', '').split(';')[0].strip()
            
            # 获取文件扩展名
            extension = mimetypes.guess_extension(mime)
            if not extension:
                raise ValueError('无法识别的文件类型')
            
            # 创建保存目录
            directory = os.path.join(img_path, pool_name)
            os.makedirs(directory, exist_ok=True)
            abs_path = os.path.join(directory, f'{name}{extension}')
            
            # 验证图像有效性，使用 run_in_executor 确保不阻塞事件循环
            try:
                image = await asyncio.to_thread(Image.open, BytesIO(content))
                await asyncio.to_thread(lambda img: img.verify(), image)
            except UnidentifiedImageError:
                raise ValueError('下载的内容不是有效的图像文件')
            
            # 重新打开图像进行处理（因为 verify 会关闭图像）
            image = await asyncio.to_thread(Image.open, BytesIO(content))
            
            # 处理 GIF 或静态图
            is_gif = mime == 'image/gif' and getattr(image, "n_frames", 1) > 1
            
            if is_gif:
                resized_image = await asyncio.to_thread(resize_gif, image)
            else:
                resized_image = await asyncio.to_thread(resize_image, image)
            
            # 异步保存文件
            async with aiofiles.open(abs_path, 'wb') as f:
                output = BytesIO()
                
                if is_gif:
                    await asyncio.to_thread(
                        lambda: resized_image.save(
                            output, 
                            format="GIF", 
                            save_all=True, 
                            loop=0,
                            optimize=True
                        )
                    )
                else:
                    # 为不同格式选择最佳保存参数
                    save_kwargs = {}
                    if image.format == "JPEG":
                        save_kwargs["quality"] = 85
                        save_kwargs["optimize"] = True
                    elif image.format == "PNG":
                        save_kwargs["optimize"] = True
                    
                    await asyncio.to_thread(
                        lambda: resized_image.save(output, format=image.format, **save_kwargs)
                    )
                
                await f.write(output.getvalue())
            
            return f'{name}{extension}'
        except httpx.HTTPError as e:
            raise IOError(f'下载失败: {str(e)}')


def resize_image(image: Image.Image) -> Image.Image:
    """压缩静态图像到指定大小以下"""
    max_size = 2 * 1024 * 1024  # 2MB
    
    # 获取当前大小
    output = BytesIO()
    save_kwargs = {}
    if image.format == "JPEG":
        save_kwargs["quality"] = 85
        save_kwargs["optimize"] = True
    elif image.format == "PNG":
        save_kwargs["optimize"] = True
    
    image.save(output, format=image.format, **save_kwargs)
    current_size = output.tell()
    
    # 如果已经小于等于最大尺寸，直接返回
    if current_size <= max_size:
        return image
    
    # 计算初始缩放比例
    width, height = image.size
    ratio = (max_size / current_size) ** 0.5
    
    # 尝试先通过调整质量来减小文件大小（仅适用于JPEG）
    if image.format == "JPEG":
        quality = 95
        while quality >= 65 and current_size > max_size:
            output = BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            current_size = output.tell()
            if current_size <= max_size:
                output.seek(0)
                return Image.open(output)
            quality -= 5
    
    # 如果调整质量不足，则调整尺寸
    while True:
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 确保尺寸不为零
        if new_width < 1: new_width = 1
        if new_height < 1: new_height = 1
        
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output = BytesIO()
        resized.save(output, format=image.format, **save_kwargs)
        current_size = output.tell()
        
        if current_size <= max_size or ratio <= 0.1:
            output.seek(0)
            return Image.open(output)
        
        ratio *= 0.8  # 更激进的缩小，避免太多循环


def resize_gif(image: Image.Image) -> Image.Image:
    """压缩GIF动图到指定大小以下"""
    max_size = 2 * 1024 * 1024  # 2MB
    
    # 获取原始GIF大小
    output = BytesIO()
    image.save(output, format="GIF", save_all=True, optimize=True)
    original_size = output.tell()
    
    # 如果已经小于等于最大尺寸，直接返回
    if original_size <= max_size:
        return image
    
    width, height = image.size
    
    # 首先尝试优化而不调整尺寸
    frames = []
    durations = []
    disposals = []
    
    # 提取所有帧和信息
    try:
        for frame in range(image.n_frames):
            image.seek(frame)
            # 保存每一帧的持续时间和处理方式
            durations.append(image.info.get('duration', 100))
            disposals.append(image.info.get('disposal', 2))
            frames.append(image.copy())
    except (AttributeError, EOFError):
        # 如果出现读取问题，回退到简单处理
        return _simple_resize_gif(image, max_size)
    
    # 先尝试只优化，不调整尺寸
    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=durations,
        disposal=disposals,
        loop=0
    )
    
    if output.tell() <= max_size:
        output.seek(0)
        return Image.open(output)
    
    # 如果仅优化不够，尝试降低颜色数量
    for colors in [256, 192, 128, 64]:
        new_frames = []
        for frame in frames:
            # 转换为指定颜色数的调色板
            if frame.mode != "P":
                frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=colors)
            new_frames.append(frame)
        
        output = BytesIO()
        new_frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=new_frames[1:],
            optimize=True,
            duration=durations,
            disposal=disposals,
            loop=0
        )
        
        if output.tell() <= max_size:
            output.seek(0)
            return Image.open(output)
    
    # 如果减少颜色数量不够，调整尺寸
    ratio = 0.9
    while ratio > 0.1:
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 确保尺寸不为零
        if new_width < 1: new_width = 1
        if new_height < 1: new_height = 1
        
        new_frames = []
        for frame in frames:
            resized_frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
            if resized_frame.mode != "P":
                resized_frame = resized_frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
            new_frames.append(resized_frame)
        
        output = BytesIO()
        try:
            new_frames[0].save(
                output,
                format="GIF",
                save_all=True,
                append_images=new_frames[1:],
                optimize=True,
                duration=durations,
                disposal=disposals,
                loop=0
            )
            
            if output.tell() <= max_size:
                output.seek(0)
                return Image.open(output)
        except Exception:
            # 如果保存出错，可能是颜色模式问题，尝试简单调整
            pass
        
        ratio *= 0.8
    
    # 如果所有方法都失败，回退到简单处理
    return _simple_resize_gif(image, max_size)


def _simple_resize_gif(image: Image.Image, max_size: int) -> Image.Image:
    """简化版GIF压缩，用于处理复杂情况"""
    width, height = image.size
    ratio = 0.9
    
    while ratio > 0.1:
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 确保尺寸不为零
        if new_width < 1: new_width = 1
        if new_height < 1: new_height = 1
        
        # 创建一个新的GIF
        frames = []
        for frame in range(image.n_frames):
            image.seek(frame)
            frame_img = image.copy().resize((new_width, new_height), Image.Resampling.LANCZOS)
            if frame_img.mode != "P":
                frame_img = frame_img.convert("P", palette=Image.Palette.ADAPTIVE)
            frames.append(frame_img)
        
        # 保存并检查大小
        output = BytesIO()
        try:
            frames[0].save(
                output,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=100,
                loop=0
            )
            
            if output.tell() <= max_size:
                output.seek(0)
                return Image.open(output)
        except Exception:
            # 如果保存失败，继续尝试更小的尺寸
            pass
        
        ratio *= 0.8
    
    # 如果所有方法都失败，返回最后的结果，即使可能超过大小限制
    output.seek(0)
    try:
        return Image.open(output)
    except Exception:
        # 如果连打开都失败，返回原图
        return image

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

#————————————————————根据CQ中的"xxx=xxxx,yyy=yyyy,..."提取出file、file_name和url————————————————————#
async def extract_file(cq_code_str: str) -> (str, str, str):
    # 解析所有CQ码参数
    cq_split = cq_code_str.split(',')

    # 拿到file参数 | 如果是单文件名：原始CQ | 如果是带路径的文件名：XQA本地已保存的图片，需要获取到单文件名
    cq_image_file_raw = next(filter(lambda x: x.startswith('file='), cq_split), '')
    cq_file_data = cq_image_file_raw.replace('file=', '')
    cq_image_file = cq_file_data.split('\\')[-1].split('/')[-1] if 'file:///' in cq_file_data else cq_file_data

    # 文件名 | Go-cq是没有这些参数的，可以直接用file参数 | 如果有才做特殊兼容处理：优先级：file_unique > filename > file_id
    cq_image_file_name_raw = (next(filter(lambda x: x.startswith('file_unique='), cq_split), '')
                           .replace('file_unique=', ''))
    cq_image_file_name_raw = (next(filter(lambda x: x.startswith('filename='), cq_split), '')
                           .replace('filename=', '')) if not cq_image_file_name_raw else cq_image_file_name_raw
    cq_image_file_name_raw = (next(filter(lambda x: x.startswith('file_id='), cq_split), '')
                           .replace('file_id=', '')) if not cq_image_file_name_raw else cq_image_file_name_raw
    # 如果三个都没有 | 那就直接用file参数，比如Go-cq
    cq_image_file_name = cq_image_file_name_raw if cq_image_file_name_raw else cq_image_file
    # 补齐文件拓展名
    cq_image_file_name = cq_image_file_name if '.' in cq_image_file_name[-10:] else cq_image_file_name + '.image'

    # 拿到URL | GO-CQ是没有这个参数的 | NapCat有
    cq_image_url = (next(filter(lambda x: x.startswith('url='), cq_split), '').replace('url=', ''))

    return cq_image_file, cq_image_file_name, cq_image_url
