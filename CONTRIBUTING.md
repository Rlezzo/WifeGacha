# CONTRIBUTING.md

## 贡献指南

以下是我最近进行的一些代码改动及其解释，以便您了解项目的最新状态，并为您的后续贡献提供参考。

### 代码改动

#### 1. 初始化功能的优化

- **改动内容**：在[main.py](main.py)增加了新的`initialize_database`函数，提供另一种初始化选项。你可以注释掉原本的`initialize_database`使用新的`initialize_database`。在bot启动完成后使用`初始化`进行插件的初始化

- **改动原因**：
  - **插件启动时初始化超时**：当你的wife文件中的图片数量比较多/比较大时，初次启动将耗费大量的时间进行图片→CQ码的转化，容易导致bot启动超时。

#### 2. 部分文本的优化
- **sv_help**：将动态显示牛老婆成功率及次数
- **牛老婆**：将提示你牛到了谁的老婆。失败时提示你还剩余多少条命

### 新增功能

#### 1. 图鉴功能

##### 1. 图鉴预加载配置
主要用于加载和缓存图片资源，以便在需要时快速访问，同时记录所有卡片文件的名称（无后缀）以便后续使用。

##### 2. 灰度化处理图片
`get_pic(pic_path, grey)`将根据给定的图片路径`pic_path`和是否灰度化的标志`grey`来返回处理后的图片。
由于图片已经预加载了，所以仅需传入图片名以及否灰度化的标志`grey`即可

##### 2. 查询图鉴
```python
@sv.on_prefix('老婆图鉴')
@sv.on_suffix('老婆图鉴')
async def atlas(bot, ev: CQEvent):
```
通过指令查询老婆图鉴。不进行权限检查。

#### 2. 应用服务功能

##### 1. 获取抽老婆的ID列表
在[statistics_application_service.py](application/services/statistics_application_service.py)中新增`get_user_character_ids`函数，它可以通过传入
```
user_group=ug,
event_type="抽老婆",
result="出新"
```
获取到群组用户`ug`抽到的所有老婆ID
##### 2. 根据ID列表获取老婆名字
在[character_application_service.py](application/services/character_application_service.py)中新增`get_character_names_by_ids`函数，它可以通过传入的老婆ID`id`获取到老婆的名字`character_names`
##### 3. 获得发起者（牛老婆/交换老婆）成功取所得的老婆ID
在[statistics_application_service.py](application/services/statistics_application_service.py)中新增`get_user_initiator_character_ids`函数，它可以通过传入
```
initiator_ug=ug,
event_type="牛老婆",
result="成功"
```
```python
initiator_ug=ug,
event_type="交换老婆",
result="同意"
```
获取到群组用户`ug`牛/交换到手的所有老婆ID
##### 4. 获得接收者（交换老婆）换取所得的老婆ID
在[statistics_application_service.py](application/services/statistics_application_service.py)中新增`get_user_receiver_character_ids`函数，它可以通过传入
```python
receiver_ug=ug,
event_type="交换老婆",
result="同意"
```
获取到群组用户`ug`同意他人交换老婆换取到手的所有老婆ID

##### 5. 提取CQ码中的file、file_name和url
在[utils.py](utils.py)中的`extract_file`函数，它可以通过传入CQ码中的"xxx=xxxx,yyy=yyyy,..."提取出file、file_name和url


#### 3. 切换NTR图鉴开关
`load_ntr_atlas_statuses` 和 `save_ntr_atlas_statuses` 函数接受一个文件名作为参数，这样你就可以为不同的配置或数据使用不同的文件。
在事件处理函数`async def switch_atlas_ntr(bot, ev: CQEvent)`中，我们每次需要访问或修改状态时都会调用 `load_ntr_atlas_statuses` 来获取最新的字典，并在修改后调用 `save_ntr_atlas_statuses` 来保存更改。
请注意，你需要确保 `config` 文件夹存在于你的项目结构中，并且你的程序有足够的权限来读取和写入该文件。如果 `config` 文件夹不存在，你可能需要在你的程序初始化时创建它，或者确保它在部署前就已经存在。