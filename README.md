
# isa\_tool \- ISM 引擎 ISA 文件处理工具

专为 ISM 引擎设计的 ISA 归档文件处理工具，支持解包、打包、单文件替换等核心功能，适配「sisters～夏の最後の日～」STEAM 版本，亦可尝试用于其他 ISM 引擎游戏。



## 项目介绍

ISA 文件是 ISM 引擎专用归档格式，用于打包游戏脚本与素材，采用「目录 \+ 数据区」结构，**无压缩、明文存储**。
`isa_tool.py` 是针对该格式开发的专用工具，解决 ISA 文件的解包、打包、文件替换等核心需求。

## 快速开始

### 运行环境

- Python 3\.x

### 基础命令

|命令|功能|用法格式|
|---|---|---|
|`list`|列出 ISA 文件内容|`python isa_tool.py list <isa文件路径>`|
|`extract`|解包全部文件|`python isa_tool.py extract <isa文件> [-o 输出目录]`|
|`create`|从目录创建 ISA 文件|`python isa_tool.py create <输入目录> [-o 输出文件]`|
|`get`|提取单个文件|`python isa_tool.py get <isa文件> <文件名> [-o 输出文件]`|
|`replace`|替换单个文件|`python isa_tool.py replace <isa文件> <文件名> <新文件路径>`|

### 使用示例

1. **查看 ISA 文件内容**

    ```bash
    python isa_tool.py list script.isa
    ```

2. **解包全部文件到指定目录**

    ```bash
    python isa_tool.py extract script.isa -o extracted
    ```

3. **从解包目录重新打包 ISA**

    ```bash
    python isa_tool.py create extracted -o script_new.isa
    ```

4. **提取单个文件**

    ```bash
    python isa_tool.py get script.isa CHAP1_A.EXT -o CHAP1_A.EXT
    ```

5. **替换 ISA 内单个文件**

    ```bash
    python isa_tool.py replace script.isa CHAP1_A.EXT modified_CHAP1_A.EXT
    ```


## 完整操作流程

### 1\. 备份原文件

修改前务必备份，避免操作失误无法恢复

### 2\. 解包 ISA 文件

将 ISA 内所有文件提取到指定目录：

```bash
python isa_tool.py extract script.isa -o extracted
```

### 3\. 修改文件

进入 `extracted` 目录编辑目标文件，注意不同文件类型的修改规则：

- `.ext` 文本文件：可直接用记事本 / VS Code 等文本编辑器修改；

- `.ism` 脚本文件：编译后的二进制格式，需专用反编译工具处理；

- `.sym` 符号表文件：包含变量名、函数名等调试信息，用于定位错误。

### 4\. 重新打包 / 单文件替换

根据修改规模选择方式：

- **方式 A：批量修改后重新打包**（适合多文件修改）

    ```bash
    python isa_tool.py create extracted -o script_new.isa
    ```

- **方式 B：单文件替换**（适合少量文件修改，效率更高）

    ```bash
    python isa_tool.py replace script.isa 目标文件名 修改后的文件路径
    ```

### 5\. 替换游戏文件

1. 确保游戏已完全关闭；

2. 将新生成的 `script_new.isa` 复制到游戏目录，替换原 ISA 文件。


3. 启动游戏，验证修改是否生效。

## 注意事项

### 回封文件体积说明

- 修改后文件 ≤ 原大小：工具直接原地替换，速度极快；

- 修改后文件 ＞ 原大小：工具会重新布局整个 ISA 文件，耗时略长（属正常现象）。

### 文件名限制

- 文件名最长支持 48 个 ASCII 字符；

- 仅支持 ASCII 编码，**不兼容中文 / 非 ASCII 字符**。

### 兼容性说明

- 核心适配：「sisters～夏の最後の日～」STEAM 版本；

- 其他游戏：其他基于 ISM 引擎的游戏可能兼容，但未做全面测试；

- 错误提示：若出现 `Invalid archive signature`，说明文件非标准 ISA 格式 / 文件已损坏。
- 

## 常见问题 \(FAQ\)

### Q: 提示「Invalid archive signature」是什么意思？

A: 目标文件并非标准 ISA 归档格式，或文件已损坏 / 被篡改，确认文件路径和文件完整性。

### Q: 能否向 ISA 文件中添加新文件？

A: 工具当前版本仅支持「替换已有文件」，暂不支持新增文件。

### Q: 有没有办法让游戏直接读取外部文件，无需反复打包？

A: ISM 引擎无「外部文件优先加载」的原生机制；可通过 DLL 注入劫持文件读取函数实现，但开发复杂度高。普通用户推荐「修改后重新打包」的方案，稳定且易操作。


### 归档插件接口

ISM 引擎通过插件系统管理归档，核心接口如下（可用于高级定制 / 二次开发）：

- `ISMPLUGIN_archive_Initialize` \- 插件初始化

- `ISMPLUGIN_archive_Register` \- 注册归档

- `ISMPLUGIN_archive_Open` \- 打开归档文件

- `ISMPLUGIN_archive_Read` \- 读取归档内文件

- `ISMPLUGIN_archive_Close` \- 关闭归档

- `ISMPLUGIN_archive_SetFileFunctions` \- 设置文件操作函数

**小tips**：理论可通过 Hook 上述接口实现「外部文件优先加载」，但需编写 DLL 注入程序，适合有逆向开发基础的用户

