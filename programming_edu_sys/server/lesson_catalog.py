"""Learning-center lesson catalog backed by authoritative references."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from programming_education_system.models.question_schema import normalize_lesson


LESSONS: List[Dict[str, Any]] = [
    # ========== 第一章：安装环境与学习准备 ==========
    {
        "id": "what-is-python",
        "language": "python",
        "title": "Python 是什么，适合做什么",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方文档 What is Python?",
            "url": "https://docs.python.org/3/faq/general.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "Python 是一门简单易学、功能强大的编程语言。"
            "它的设计哲学强调代码的可读性和简洁性，让你可以用更少的代码做更多的事情。"
            "无论是数据分析、人工智能、网站开发还是自动化办公，Python 都能胜任。"
        ),
        "knowledge_points": [
            {
                "title": "1. Python 是一门解释型编程语言",
                "explanation": (
                    "编程语言主要分为编译型和解释型两种。"
                    "编译型语言（如 C、Java）需要先把代码转换成机器语言才能运行。"
                    "而 Python 是解释型语言，代码写好后可以直接运行，解释器会逐行翻译成机器指令。"
                    "这意味着你可以快速测试代码，看到结果，非常适合学习和原型开发。"
                ),
                "example": (
                    "# 写好后直接运行，不需要编译\n"
                    "print('Hello, World!')\n"
                    "# 输出: Hello, World!"
                ),
            },
            {
                "title": "2. Python 的语法简洁易读",
                "explanation": (
                    "Python 的设计哲学是'优雅胜于丑陋，明确胜于隐晦'。"
                    "它使用缩进来表示代码块，而不是大括号，这让代码看起来像伪代码一样清晰。"
                    "同样的功能，Python 的代码量通常只有 Java 或 C++ 的 1/3 到 1/5。"
                    "这种简洁性让初学者能更快上手，也让团队协作更高效。"
                ),
                "example": (
                    "# 计算 1 到 10 的和\n"
                    "total = 0\n"
                    "for i in range(1, 11):\n"
                    "    total += i\n"
                    "print(total)  # 输出: 55"
                ),
            },
            {
                "title": "3. Python 的应用领域非常广泛",
                "explanation": (
                    "Python 不是一门局限于某个领域的语言。"
                    "在数据科学领域，有 NumPy、Pandas、Matplotlib 等强大工具。"
                    "在人工智能领域，TensorFlow、PyTorch 都是基于 Python 的。"
                    "在 Web 开发领域，Django、Flask 框架让建站变得简单。"
                    "在自动化办公领域，Python 可以处理 Excel、PDF、邮件等。"
                    "学习 Python，就是打开了一扇通往多个技术领域的大门。"
                ),
                "example": (
                    "# 用 pandas 读取 Excel 文件（示例）\n"
                    "# import pandas as pd\n"
                    "# data = pd.read_excel('data.xlsx')\n"
                    "# print(data.head())"
                ),
            },
            {
                "title": "4. Python 拥有庞大的社区和丰富的资源",
                "explanation": (
                    "Python 诞生于 1991 年，经过 30 多年的发展，已经形成了全球最大的编程社区之一。"
                    "无论你遇到什么问题，几乎都能在 Stack Overflow、GitHub 或中文社区找到答案。"
                    "PyPI（Python Package Index）上有超过 40 万个第三方库，涵盖各种功能。"
                    "这些库大多是开源免费的，你可以直接安装使用，不用重复造轮子。"
                ),
                "example": (
                    "# 安装第三方库（在终端中运行）\n"
                    "# pip install requests\n"
                    "\n"
                    "# 使用 requests 库发送网络请求\n"
                    "import requests\n"
                    "response = requests.get('https://api.github.com')\n"
                    "print(response.status_code)"
                ),
            },
            {
                "title": "5. 为什么初学者应该选择 Python",
                "explanation": (
                    "对于编程新手来说，Python 是最佳的入门语言。"
                    "首先，它的语法接近自然语言，你可以快速理解代码在做什么。"
                    "其次，它能让你专注于编程逻辑，而不是纠结于复杂的语法细节。"
                    "最后，学会 Python 后，你可以很快进入实际项目，获得成就感。"
                    "无论是想转行程序员，还是想提升工作效率，Python 都是理想的选择。"
                ),
                "example": (
                    "# 简单的猜数字游戏\n"
                    "import random\n"
                    "number = random.randint(1, 100)\n"
                    "guess = int(input('猜一个 1-100 的数字: '))\n"
                    "if guess == number:\n"
                    "    print('恭喜你，猜对了！')\n"
                    "else:\n"
                    "    print(f'很遗憾，正确答案是 {number}')"
                ),
            },
        ],
        "exercise": {
            "id": "what-is-python-ex-01",
            "title": "写出你的第一个 Python 程序",
            "description": "在交互式解释器中，尝试输入以下代码并观察结果：打印你的名字、计算 123 + 456、使用 type() 函数查看 'Hello' 的类型。",
            "starter_code": "# 在这里输入你的代码\n# 示例：print('你的名字')",
            "test_cases": [
                {"input": "", "expected_output": "", "description": "在解释器中交互式完成即可"}
            ],
        },
    },
    {
        "id": "install-python-windows",
        "language": "python",
        "title": "Windows 安装 Python",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方文档 Windows 安装指南",
            "url": "https://docs.python.org/3/using/windows.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "在 Windows 上安装 Python 非常简单，只需要从官网下载安装包，运行安装程序，"
            "记得勾选'Add Python to PATH'选项，然后验证安装是否成功即可。"
        ),
        "knowledge_points": [
            {
                "title": "1. 从官网下载 Python 安装包",
                "explanation": (
                    "访问 Python 官方网站 python.org，点击 Downloads 菜单，网站会自动推荐适合你系统的版本。"
                    "通常建议下载最新的稳定版本（如 Python 3.11 或 3.12）。"
                    "下载的文件是一个 .exe 可执行程序，大小约 20-30MB。"
                    "确保从官网下载，避免使用来路不明的安装包，以保证安全性。"
                ),
                "example": (
                    "# 官网地址\n"
                    "https://www.python.org/downloads/\n"
                    "\n"
                    "# 点击 Download Python 3.x.x 按钮即可下载"
                ),
            },
            {
                "title": "2. 运行安装程序并勾选重要选项",
                "explanation": (
                    "下载完成后，双击运行安装程序。"
                    "最关键的一步是：勾选'Add Python.exe to PATH'（将 Python 添加到环境变量）。"
                    "这个选项让你在命令行中任何位置都能直接使用 python 命令。"
                    "如果忘记勾选，后续需要手动配置，会比较麻烦。"
                    "建议选择'Install Now'进行默认安装，或者选择'Customize installation'自定义安装路径。"
                ),
                "example": (
                    "# 安装时务必勾选:\n"
                    "☑ Add Python.exe to PATH\n"
                    "\n"
                    "# 推荐选择:\n"
                    "☑ Use admin privileges when installing py.exe"
                ),
            },
            {
                "title": "3. 验证 Python 是否安装成功",
                "explanation": (
                    "安装完成后，需要验证 Python 是否正确安装。"
                    "打开命令提示符（CMD）或 PowerShell，输入 python --version。"
                    "如果显示版本号（如 Python 3.11.4），说明安装成功。"
                    "也可以输入 python 进入交互式解释器，看到 >>> 提示符表示可以开始写代码了。"
                    "输入 exit() 或按 Ctrl+Z 然后回车可以退出解释器。"
                ),
                "example": (
                    "C:\\> python --version\n"
                    "Python 3.11.4\n"
                    "\n"
                    "C:\\> python\n"
                    "Python 3.11.4 (tags/v3.11.4:d2340ef, Jun  7 2023, 05:45:37)\n"
                    ">>> print('Hello, Python!')\n"
                    "Hello, Python!\n"
                    ">>> exit()"
                ),
            },
            {
                "title": "4. 安装 pip 包管理工具",
                "explanation": (
                    "pip 是 Python 的包管理工具，用来安装第三方库。"
                    "最新版本的 Python 安装程序已经默认包含了 pip。"
                    "可以通过 pip --version 命令检查 pip 是否已安装。"
                    "pip 让你可以一键安装各种强大的扩展库，如 numpy、pandas、requests 等。"
                    "这是 Python 生态系统如此丰富的重要原因之一。"
                ),
                "example": (
                    "C:\\> pip --version\n"
                    "pip 23.0.1 from ...\\site-packages\\pip (python 3.11)\n"
                    "\n"
                    "# 使用 pip 安装第三方库\n"
                    "C:\\> pip install requests"
                ),
            },
            {
                "title": "5. 常见问题排查",
                "explanation": (
                    "如果输入 python 提示'不是内部或外部命令'，说明 PATH 配置有问题。"
                    "可以重新运行安装程序，选择 Modify，然后勾选 Add to PATH。"
                    "或者手动将 Python 安装目录（如 C:\\Python311）添加到系统环境变量 PATH 中。"
                    "如果安装过程中遇到权限问题，尝试右键以管理员身份运行安装程序。"
                    "Windows 7 用户可能需要先安装 Service Pack 1 和 KB2533623 更新。"
                ),
                "example": (
                    "# 手动添加 PATH 的步骤:\n"
                    "1. 右键'此电脑' -> 属性 -> 高级系统设置\n"
                    "2. 环境变量 -> 系统变量中找到 Path\n"
                    "3. 编辑 -> 新建 -> 添加 Python 安装路径\n"
                    "4. 如: C:\\Users\\你的用户名\\AppData\\Local\\Programs\\Python\\Python311"
                ),
            },
        ],
        "exercise": {
            "id": "install-python-windows-ex-01",
            "title": "安装并验证 Python",
            "description": "按照课程步骤，在 Windows 上完成 Python 的安装，并在命令行中验证 python --version 能正确显示版本号。",
            "starter_code": "# 在命令行中输入:\n# python --version",
            "test_cases": [
                {"input": "", "expected_output": "Python 3.x.x", "description": "显示 Python 版本号即算成功"}
            ],
        },
    },
    {
        "id": "install-python-macos-linux",
        "language": "python",
        "title": "macOS / Linux 环境说明",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方文档 Unix 安装指南",
            "url": "https://docs.python.org/3/using/unix.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "macOS 和大多数 Linux 发行版都预装了 Python。"
            "macOS 通常预装 Python 2.7，建议安装 Python 3.x 以获得更好的体验。"
            "Linux 用户可以使用包管理器快速安装或更新 Python。"
        ),
        "knowledge_points": [
            {
                "title": "1. macOS 自带的 Python",
                "explanation": (
                    "macOS 系统通常预装了 Python 2.7，位于 /usr/bin/python。"
                    "但 Python 2 已经停止维护，不建议用于新项目。"
                    "macOS 也预装了 Python 3，命令是 python3 而不是 python。"
                    "建议通过 Homebrew 安装最新版本的 Python 3，这样管理起来更方便。"
                ),
                "example": (
                    "$ python --version  # 通常是 Python 2.7.x\n"
                    "$ python3 --version  # 系统自带的 Python 3\n"
                    "Python 3.9.6"
                ),
            },
            {
                "title": "2. 使用 Homebrew 安装 Python（推荐）",
                "explanation": (
                    "Homebrew 是 macOS 最流行的包管理器，类似 Linux 的 apt 或 yum。"
                    "首先安装 Homebrew：访问 brew.sh，复制安装命令到终端运行。"
                    "然后使用 brew install python3 安装最新版 Python。"
                    "安装完成后，python3 和 pip3 命令就可以使用了。"
                    "Homebrew 安装的 Python 通常比系统自带的更新。"
                ),
                "example": (
                    "# 安装 Homebrew\n"
                    "$ /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n"
                    "\n"
                    "# 使用 Homebrew 安装 Python\n"
                    "$ brew install python\n"
                    "\n"
                    "# 验证安装\n"
                    "$ python3 --version"
                ),
            },
            {
                "title": "3. Linux 系统安装 Python",
                "explanation": (
                    "大多数 Linux 发行版都预装了 Python 3。"
                    "Ubuntu/Debian 使用 apt 包管理器：sudo apt update && sudo apt install python3 python3-pip。"
                    "CentOS/RHEL/Fedora 使用 yum 或 dnf：sudo dnf install python3 python3-pip。"
                    "Arch Linux 使用 pacman：sudo pacman -S python python-pip。"
                    "安装完成后，使用 python3 命令调用 Python，pip3 调用包管理器。"
                ),
                "example": (
                    "# Ubuntu/Debian\n"
                    "$ sudo apt update\n"
                    "$ sudo apt install python3 python3-pip\n"
                    "\n"
                    "# CentOS/RHEL/Fedora\n"
                    "$ sudo dnf install python3 python3-pip\n"
                    "\n"
                    "# 验证安装\n"
                    "$ python3 --version\n"
                    "$ pip3 --version"
                ),
            },
            {
                "title": "4. 创建 python 命令的别名",
                "explanation": (
                    "在 macOS 和 Linux 上，Python 3 的命令是 python3 而不是 python。"
                    "如果你习惯直接输入 python，可以创建一个别名。"
                    "编辑 shell 配置文件（如 ~/.bashrc、~/.zshrc），添加 alias python=python3。"
                    "然后运行 source ~/.bashrc（或 ~/.zshrc）使配置生效。"
                    "同样可以为 pip 创建别名：alias pip=pip3。"
                ),
                "example": (
                    "# 编辑 zsh 配置文件（macOS 默认使用 zsh）\n"
                    "$ echo \"alias python=python3\" >> ~/.zshrc\n"
                    "$ echo \"alias pip=pip3\" >> ~/.zshrc\n"
                    "$ source ~/.zshrc\n"
                    "\n"
                    "# 现在可以直接使用 python 命令了\n"
                    "$ python --version"
                ),
            },
            {
                "title": "5. 虚拟环境简介",
                "explanation": (
                    "在 macOS 和 Linux 上，使用 pip 安装包时可能需要 sudo 权限。"
                    "更好的做法是使用虚拟环境（virtual environment），避免污染系统 Python。"
                    "创建虚拟环境：python3 -m venv myenv。"
                    "激活虚拟环境：source myenv/bin/activate（Linux/macOS）。"
                    "激活后，命令提示符前会显示环境名，此时 pip 安装的包都在这个环境中。"
                    "退出虚拟环境：deactivate。"
                ),
                "example": (
                    "# 创建虚拟环境\n"
                    "$ python3 -m venv myproject\n"
                    "\n"
                    "# 激活虚拟环境\n"
                    "$ source myproject/bin/activate\n"
                    "(myproject) $ pip install requests\n"
                    "\n"
                    "# 退出虚拟环境\n"
                    "(myproject) $ deactivate"
                ),
            },
        ],
        "exercise": {
            "id": "install-python-macos-linux-ex-01",
            "title": "检查系统 Python 版本",
            "description": "打开终端，分别运行 python --version 和 python3 --version，观察输出结果，确认系统是否已安装 Python 3。",
            "starter_code": "# 在终端中输入:\n# python3 --version",
            "test_cases": [
                {"input": "", "expected_output": "Python 3.x.x", "description": "显示 Python 3 版本号"}
            ],
        },
    },
    {
        "id": "terminal-basics",
        "language": "python",
        "title": "终端与命令行最小必备",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方文档 Command line and environment",
            "url": "https://docs.python.org/3/using/cmdline.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "终端（命令行）是程序员的基本工具。"
            "学会打开终端、切换目录、运行 Python 程序，是开始编程之旅的第一步。"
        ),
        "knowledge_points": [
            {
                "title": "1. 如何打开终端",
                "explanation": (
                    "Windows：按 Win+R，输入 cmd 回车打开命令提示符；或输入 powershell 打开 PowerShell。"
                    "macOS：按 Cmd+空格，输入 terminal 回车打开终端。"
                    "Linux：按 Ctrl+Alt+T 打开终端，或在应用菜单中搜索 Terminal。"
                    "VS Code：按 Ctrl+`（反引号）打开集成终端。"
                    "建议将终端固定在任务栏或 Dock，方便快速打开。"
                ),
                "example": (
                    "# Windows 快捷键\n"
                    "Win + R -> cmd -> Enter\n"
                    "\n"
                    "# macOS 快捷键\n"
                    "Cmd + Space -> terminal -> Enter\n"
                    "\n"
                    "# Linux 快捷键\n"
                    "Ctrl + Alt + T"
                ),
            },
            {
                "title": "2. 常用目录操作命令",
                "explanation": (
                    "pwd（Print Working Directory）：显示当前所在目录。"
                    "ls（List，Windows 用 dir）：列出当前目录的文件和文件夹。"
                    "cd（Change Directory）：切换目录，如 cd Documents 进入 Documents 文件夹。"
                    "cd ..：返回上一级目录。"
                    "cd ~：返回用户主目录（Windows 是 cd %USERPROFILE%）。"
                    "mkdir（Make Directory）：创建新文件夹。"
                ),
                "example": (
                    "$ pwd\n"
                    "/home/username\n"
                    "$ ls\n"
                    "Documents  Downloads  Desktop\n"
                    "$ cd Documents\n"
                    "$ pwd\n"
                    "/home/username/Documents\n"
                    "$ cd ..\n"
                    "$ mkdir myproject"
                ),
            },
            {
                "title": "3. 运行 Python 程序",
                "explanation": (
                    "在终端中输入 python（或 python3）进入交互式解释器，可以直接执行 Python 代码。"
                    "输入 python 文件名.py 可以运行 Python 脚本文件。"
                    "运行脚本前，确保终端的当前目录在脚本所在位置，或使用完整路径。"
                    "按 Ctrl+C 可以强制终止正在运行的程序。"
                    "使用方向键上/下可以查看之前输入过的命令。"
                ),
                "example": (
                    "$ python\n"
                    ">>> print('Hello')\n"
                    "Hello\n"
                    ">>> exit()\n"
                    "$\n"
                    "$ python hello.py\n"
                    "Hello, World!"
                ),
            },
            {
                "title": "4. 路径的概念",
                "explanation": (
                    "绝对路径：从根目录开始的完整路径，如 /home/user/file.txt 或 C:\\Users\\user\\file.txt。"
                    "相对路径：相对于当前目录的路径，如 ./file.txt 表示当前目录下的 file.txt。"
                    ".. 表示上级目录，. 表示当前目录。"
                    "Windows 使用反斜杠 \\ 作为路径分隔符，macOS/Linux 使用正斜杠 /。"
                    "在 Python 代码中，建议始终使用正斜杠 /，Python 会自动处理跨平台问题。"
                ),
                "example": (
                    "# 绝对路径\n"
                    "C:\\Users\\Alice\\Documents\\file.txt  # Windows\n"
                    "/home/alice/documents/file.txt       # macOS/Linux\n"
                    "\n"
                    "# 相对路径\n"
                    "./file.txt      # 当前目录\n"
                    "../file.txt     # 上级目录\n"
                    "folder/file.txt # 子目录"
                ),
            },
            {
                "title": "5. 终端使用小技巧",
                "explanation": (
                    "Tab 键自动补全：输入文件名或命令的前几个字母，按 Tab 自动补全。"
                    "Ctrl+C：终止当前运行的程序。"
                    "Ctrl+L（或输入 clear）：清屏。"
                    "Ctrl+A：光标移到行首，Ctrl+E：光标移到行尾。"
                    "Ctrl+U：删除光标前的所有内容。"
                    "输入 history 查看命令历史（Windows 是按 F7）。"
                ),
                "example": (
                    "$ pyt  # 按 Tab 键\n"
                    "$ python  # 自动补全\n"
                    "\n"
                    "$ cd Doc  # 按 Tab 键\n"
                    "$ cd Documents/  # 自动补全"
                ),
            },
        ],
        "exercise": {
            "id": "terminal-basics-ex-01",
            "title": "终端基础操作",
            "description": "打开终端，使用 pwd 查看当前目录，使用 mkdir 创建一个名为 python_learning 的文件夹，然后使用 cd 进入该文件夹，最后使用 python 进入交互式解释器并打印 'Hello, Terminal!'。",
            "starter_code": "# 在终端中依次执行:\n# mkdir python_learning\n# cd python_learning\n# python\n# >>> print('Hello, Terminal!')",
            "test_cases": [
                {"input": "", "expected_output": "Hello, Terminal!", "description": "成功创建文件夹并在终端中运行 Python"}
            ],
        },
    },
    {
        "id": "vscode-python-extension",
        "language": "python",
        "title": "VS Code 与 Python 插件配置",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "VS Code Python 官方文档",
            "url": "https://code.visualstudio.com/docs/python/python-tutorial",
            "authority": "Microsoft",
        },
        "summary": (
            "VS Code 是目前最流行的代码编辑器之一，配合 Python 插件可以提供强大的代码提示、调试和运行功能。"
            "学会配置好开发环境，能让你的编程效率事半功倍。"
        ),
        "knowledge_points": [
            {
                "title": "1. 下载并安装 VS Code",
                "explanation": (
                    "访问 code.visualstudio.com 下载适合你系统的安装包。"
                    "Windows 用户下载 .exe 安装程序，macOS 用户下载 .dmg，Linux 用户下载 .deb 或 .rpm。"
                    "安装过程很简单，保持默认选项即可。"
                    "安装完成后，建议将 VS Code 添加到系统 PATH，这样可以在终端中使用 code 命令打开文件。"
                    "VS Code 是免费开源的软件，由微软维护，更新非常频繁。"
                ),
                "example": (
                    "# 官网下载地址\n"
                    "https://code.visualstudio.com/\n"
                    "\n"
                    "# 安装后验证（在终端中）\n"
                    "$ code --version\n"
                    "1.85.0"
                ),
            },
            {
                "title": "2. 安装 Python 扩展插件",
                "explanation": (
                    "打开 VS Code，点击左侧活动栏的 Extensions（扩展）图标，或按 Ctrl+Shift+X。"
                    "在搜索框中输入 'Python'，找到由 Microsoft 发布的官方 Python 扩展。"
                    "点击 Install 按钮安装。这个扩展提供了代码高亮、智能提示、调试等功能。"
                    "同时会自动安装 Pylance（提供更强大的类型检查和代码分析）和 Jupyter 支持。"
                    "安装完成后，右下角可能会提示选择 Python 解释器。"
                ),
                "example": (
                    "# 安装 Python 扩展后，VS Code 会提供:\n"
                    "- 代码自动补全\n"
                    "- 语法错误检查\n"
                    "- 代码格式化\n"
                    "- 调试支持\n"
                    "- 智能提示"
                ),
            },
            {
                "title": "3. 选择 Python 解释器",
                "explanation": (
                    "安装 Python 扩展后，需要告诉 VS Code 使用哪个 Python 版本。"
                    "按 Ctrl+Shift+P 打开命令面板，输入 'Python: Select Interpreter' 并选择。"
                    "或者点击右下角的状态栏中的 Python 版本号进行选择。"
                    "选择你安装的 Python 3.x 版本，路径通常包含 'python.exe' 或 'python3'。"
                    "选择正确的解释器后，VS Code 就能提供准确的代码提示和错误检查了。"
                ),
                "example": (
                    "# 选择解释器的步骤:\n"
                    "1. Ctrl+Shift+P 打开命令面板\n"
                    "2. 输入 'Python: Select Interpreter'\n"
                    "3. 选择你的 Python 3.x 路径\n"
                    "\n"
                    "# 或者点击右下角状态栏的 Python 版本"
                ),
            },
            {
                "title": "4. 创建和运行 Python 文件",
                "explanation": (
                    "在 VS Code 中，点击 File -> New File 创建新文件，保存为 .py 扩展名。"
                    "编写代码后，可以通过多种方式运行："
                    "点击右上角的运行按钮（三角形图标）；"
                    "右键编辑器选择 'Run Python File in Terminal'；"
                    "按 F5 启动调试模式运行。"
                    "运行结果会显示在底部的集成终端中。"
                    "如果代码有错误，VS Code 会在问题面板中高亮显示。"
                ),
                "example": (
                    "# 创建 hello.py 文件\n"
                    "print('Hello from VS Code!')\n"
                    "\n"
                    "# 运行方式:\n"
                    "# 1. 点击右上角三角形按钮\n"
                    "# 2. 右键 -> Run Python File in Terminal\n"
                    "# 3. 按 F5 调试运行"
                ),
            },
            {
                "title": "5. 配置代码格式化和 Linting",
                "explanation": (
                    "好的代码风格能让程序更易读、更易维护。"
                    "VS Code 可以配置自动格式化，推荐使用 Black 或 autopep8 格式化工具。"
                    "安装 Black：pip install black，然后在 VS Code 设置中配置 'Python Formatting Provider' 为 Black。"
                    "设置 'Editor: Format On Save' 为 true，这样保存文件时会自动格式化。"
                    "还可以启用 Pylint 或 Flake8 进行代码质量检查，帮助你发现潜在问题。"
                ),
                "example": (
                    "# 安装 Black 格式化工具\n"
                    "$ pip install black\n"
                    "\n"
                    "# VS Code 设置 (settings.json)\n"
                    "{\n"
                    "    \"python.formatting.provider\": \"black\",\n"
                    "    \"editor.formatOnSave\": true\n"
                    "}"
                ),
            },
        ],
        "exercise": {
            "id": "vscode-python-extension-ex-01",
            "title": "配置你的 VS Code 开发环境",
            "description": "完成 VS Code 和 Python 扩展的安装，创建一个新的 Python 文件，编写代码打印 'Hello, VS Code!'，并成功运行看到输出结果。",
            "starter_code": "# 在 VS Code 中创建新文件，输入以下代码:\nprint('Hello, VS Code!')",
            "test_cases": [
                {"input": "", "expected_output": "Hello, VS Code!", "description": "成功在 VS Code 中运行 Python 程序"}
            ],
        },
    },
    {
        "id": "first-python-file",
        "language": "python",
        "title": "第一个 .py 文件",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 2. Using the Python Interpreter",
            "url": "https://docs.python.org/3/tutorial/interpreter.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "从交互式解释器过渡到真正的 Python 文件，是编程学习的重要一步。"
            "学会创建、保存和运行 .py 文件，你就迈出了成为程序员的第一步。"
        ),
        "knowledge_points": [
            {
                "title": "1. 什么是 .py 文件",
                "explanation": (
                    ".py 是 Python 源代码文件的标准扩展名。"
                    "与交互式解释器不同，.py 文件可以保存代码，方便反复运行和修改。"
                    "你可以用任何文本编辑器创建 .py 文件，但推荐使用 VS Code 等专业编辑器。"
                    "文件名应该有意义，比如 hello.py、calculator.py，不要用中文或特殊字符。"
                    "一个 .py 文件通常称为一个 Python 脚本或模块。"
                ),
                "example": (
                    "# 合法的 Python 文件名:\n"
                    "hello.py\n"
                    "calculator.py\n"
                    "data_analysis.py\n"
                    "\n"
                    "# 不推荐的文件名:\n"
                    "我的程序.py  # 避免中文\n"
                    "hello world.py  # 避免空格\n"
                    "123.py  # 避免数字开头"
                ),
            },
            {
                "title": "2. 创建你的第一个 Python 文件",
                "explanation": (
                    "打开 VS Code，点击 File -> New File 创建新文件。"
                    "输入以下代码：print('Hello, World!')。"
                    "按 Ctrl+S 保存文件，选择保存位置，文件名输入 hello.py。"
                    "注意文件扩展名必须是 .py，这样 VS Code 才会识别为 Python 文件。"
                    "保存后，VS Code 会自动启用 Python 语法高亮和代码提示。"
                ),
                "example": (
                    "# hello.py\n"
                    "print('Hello, World!')\n"
                    "\n"
                    "# 也可以多行输出\n"
                    "print('这是第一行')\n"
                    "print('这是第二行')\n"
                    "print('Python 编程，从这里开始！')"
                ),
            },
            {
                "title": "3. 运行 Python 文件的多种方式",
                "explanation": (
                    "方式一：在 VS Code 中点击右上角的运行按钮，或右键选择 'Run Python File in Terminal'。"
                    "方式二：打开终端，切换到文件所在目录，输入 python hello.py 运行。"
                    "方式三：在终端中输入 python 文件的完整路径，如 python C:\\Users\\Name\\hello.py。"
                    "无论哪种方式，都应该看到输出结果显示在终端中。"
                    "如果看到错误信息，仔细检查代码拼写和缩进。"
                ),
                "example": (
                    "# 方式1: VS Code 中运行\n"
                    "# 点击右上角三角形按钮\n"
                    "\n"
                    "# 方式2: 终端中运行（先切换到文件目录）\n"
                    "$ cd /path/to/your/file\n"
                    "$ python hello.py\n"
                    "Hello, World!\n"
                    "\n"
                    "# 方式3: 使用完整路径\n"
                    "$ python C:\\Users\\Name\\Documents\\hello.py"
                ),
            },
            {
                "title": "4. 修改、保存、再运行的循环",
                "explanation": (
                    "编程是一个不断试错和改进的过程。"
                    "修改代码 -> 保存文件（Ctrl+S）-> 运行程序 -> 观察结果 -> 继续修改。"
                    "这个循环是编程学习的基本节奏，也是程序员日常工作的真实写照。"
                    "不要怕出错，每个错误都是学习的机会。"
                    "养成频繁保存的习惯，避免意外丢失代码。"
                ),
                "example": (
                    "# 第一次运行\n"
                    "print('Hello')\n"
                    "\n"
                    "# 修改后再次运行\n"
                    "name = 'Python'\n"
                    "print(f'Hello, {name}!')\n"
                    "\n"
                    "# 继续改进\n"
                    "name = input('请输入你的名字: ')\n"
                    "print(f'你好, {name}! 欢迎学习 Python!')"
                ),
            },
            {
                "title": "5. 添加注释让代码更易读",
                "explanation": (
                    "注释是写给人类看的说明文字，Python 会忽略它们。"
                    "单行注释用 # 开头，# 后面的内容都是注释。"
                    "好的注释能解释代码为什么这样写，而不是重复代码做了什么。"
                    "注释也能临时禁用某行代码，方便调试。"
                    "养成写注释的习惯，对你自己和阅读你代码的人都有帮助。"
                ),
                "example": (
                    "# 这是单行注释\n"
                    "print('Hello')  # 这也是注释\n"
                    "\n"
                    "# 下面的代码计算两数之和\n"
                    "a = 10  # 第一个数\n"
                    "b = 20  # 第二个数\n"
                    "sum = a + b  # 计算和\n"
                    "print(sum)  # 输出结果: 30\n"
                    "\n"
                    "# print('这行被注释掉了，不会执行')"
                ),
            },
        ],
        "exercise": {
            "id": "first-python-file-ex-01",
            "title": "创建并运行你的第一个 Python 文件",
            "description": "使用 VS Code 创建一个名为 hello.py 的文件，编写程序打印你的姓名和一句自我介绍，保存后在终端中成功运行。",
            "starter_code": "# hello.py\n# 在这里写下你的代码\nprint('你好，我是...')",
            "test_cases": [
                {"input": "", "expected_output": "包含自我介绍内容", "description": "成功创建并运行第一个 Python 文件"}
            ],
        },
    },
    {
        "id": "indentation-rules",
        "language": "python",
        "title": "缩进规则与代码块",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4. More Control Flow Tools / 菜鸟教程 Python3 基础语法",
            "url": "https://docs.python.org/3/tutorial/controlflow.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "很多语言用大括号来区分代码块，而 Python 更直接，它用缩进来表示一段代码属于谁。"
            "也就是说，缩进在 Python 里不只是排版好看，而是实打实的语法规则。"
            "因此，学会看缩进、写缩进，其实就是在学会看懂 Python 程序的结构。"
            "这件事看起来细小，但它会影响你后面所有的 `if`、循环和函数。"
        ),
        "knowledge_points": [
            {
                "title": "1. Python 用缩进表示代码块",
                "explanation": (
                    "在 Python 里，一段代码是不是属于某个 `if`、`for` 或函数，不靠大括号判断，而是靠缩进判断。"
                    "换句话说，谁向右缩进了一层，谁就属于上面的那一层结构。"
                    "因此，缩进不是额外装饰，而是程序结构的一部分。"
                    "也正因为如此，写 Python 时你看到的“层级感”，往往就是程序真正的执行层级。"
                ),
                "example": (
                    "if 3 > 1:\n"
                    "    print('yes')\n"
                    "print('done')"
                ),
            },
            {
                "title": "2. 同一个代码块里的缩进要保持一致",
                "explanation": (
                    "如果一段代码本来属于同一个块，那么它们的缩进应该整齐一致。"
                    "否则，Python 可能会直接报错，或者把你的代码理解成完全不同的结构。"
                    "因此，学缩进时不只是知道“要缩进”，还要知道“同一层必须对齐”。"
                    "初学阶段把这个习惯练好，后面会省掉很多莫名其妙的错误。"
                ),
                "example": (
                    "if 5 > 2:\n"
                    "    print('第一行')\n"
                    "    print('第二行')"
                ),
            },
            {
                "title": "3. 常见约定是用 4 个空格缩进",
                "explanation": (
                    "虽然技术上你可能会看到不同写法，但在 Python 社区里，最常见、最推荐的做法是使用 4 个空格缩进。"
                    "这样做的好处很直接：大家的代码风格更统一，读起来也更舒服。"
                    "因此，初学时就尽量把 4 个空格当成默认习惯。"
                    "另外，也最好避免空格和 Tab 混用，否则很容易出现看起来对齐、实际却出错的情况。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    message = f'Hello, {name}!'\n"
                    "    return message"
                ),
            },
            {
                "title": "4. 缩进能帮助你看出程序的层次关系",
                "explanation": (
                    "写代码时，缩进的作用不只是“让 Python 不报错”，它其实还在帮你看懂程序结构。"
                    "比如某一行是在函数里，还是在 `if` 里面，或者是不是循环的一部分，你通常一眼就能从缩进看出来。"
                    "也就是说，缩进既是给机器看的，也是给人看的。"
                    "当你慢慢开始读别人的代码时，这种层次感会越来越重要。"
                ),
                "example": (
                    "for i in range(2):\n"
                    "    if i == 0:\n"
                    "        print('zero')\n"
                    "    print('loop')"
                ),
            },
            {
                "title": "5. 遇到缩进报错时，先看“这一行到底属于谁”",
                "explanation": (
                    "初学者看到缩进报错时很容易慌，其实这类问题通常可以靠一个思路去排查："
                    "这行代码到底应该属于哪一层？它现在是不是和同层代码对齐了？"
                    "因此，与其死盯着报错英文，不如先回头看结构。"
                    "只要把“这一行属于谁”想清楚，很多缩进问题都会明显容易处理。"
                ),
                "example": (
                    "def say_hi():\n"
                    "    print('Hi')\n"
                    "print('outside')"
                ),
            },
        ],
        "exercise": {
            "id": "indentation-rules-ex-01",
            "title": "写一个正确缩进的判断函数",
            "expected_function": "check_positive",
            "description": (
                "请写一个函数 `check_positive(n)`。"
                "如果 `n` 大于 0，就返回字符串 `正数`；否则返回 `非正数`。"
                "这道题本身不难，重点是练习在 `if` 和函数里把缩进写正确。"
            ),
            "requirements": [
                "函数名必须是 `check_positive`。",
                "函数接收一个参数 `n`。",
                "`n > 0` 时返回 `正数`。",
                "否则返回 `非正数`。",
            ],
            "examples": [
                {"input": "check_positive(3)", "output": "正数"},
                {"input": "check_positive(0)", "output": "非正数"},
            ],
            "hints": [
                "先写函数头：`def check_positive(n):`。",
                "再在函数内部写 `if`，注意缩进层级。",
                "函数体和 `if` 代码块的缩进不是同一层。",
            ],
            "starter_code": (
                "def check_positive(n):\n"
                "    # TODO: 根据 n 的值返回 正数 或 非正数\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def check_positive(n):\n"
                "    if n > 0:\n"
                "        return '正数'\n"
                "    return '非正数'\n"
            ),
            "hidden_tests": [
                {"call": "check_positive(3)", "expected": "正数"},
                {"call": "check_positive(0)", "expected": "非正数"},
                {"call": "check_positive(-2)", "expected": "非正数"},
            ],
        },
    },
    {
        "id": "variables-assignment",
        "language": "python",
        "title": "变量与赋值",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3. An Informal Introduction to Python / 菜鸟教程 Python3 变量类型",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "变量几乎是写程序时最常见的东西。"
            "不过，变量并不神秘，它本质上只是让你给一个值起名字，好让后面继续使用。"
            "因此，学变量时最重要的，不是死背定义，而是逐渐习惯“先得到结果，再把结果交给一个名字”。"
            "一旦这个感觉顺了，后面的表达式、函数和数据结构都会更容易理解。"
        ),
        "knowledge_points": [
            {
                "title": "1. 变量是在给一个值起名字",
                "explanation": (
                    "当程序里某个值后面还要继续用时，你通常不会想每次都重新写一遍。"
                    "这时就可以把它交给一个变量。"
                    "也就是说，变量最大的作用，就是让结果有了一个可以反复引用的名字。"
                    "因此，变量并不是额外负担，反而是在帮你把代码写得更有条理。"
                ),
                "example": (
                    "name = 'Alice'\n"
                    "score = 95\n"
                    "print(name)\n"
                    "print(score)"
                ),
            },
            {
                "title": "2. `=` 表示赋值，而不是数学证明",
                "explanation": (
                    "在数学里，等号通常是在表达左右相等。"
                    "但在 Python 里，`=` 更像一个“交给”的动作。"
                    "比如 `total = 5` 的意思不是讨论 total 和 5 是否相等，而是把值 5 交给变量 `total`。"
                    "因此，学编程时需要慢慢把这个符号从数学语境切换到程序语境里。"
                ),
                "example": (
                    "total = 5\n"
                    "print(total)"
                ),
            },
            {
                "title": "3. 变量的值可以被更新",
                "explanation": (
                    "变量不是一次写死就永远不变。"
                    "恰恰相反，它常常会在程序运行过程中不断更新。"
                    "因此，当你看到同一个变量名反复出现时，不要只盯着名字，而要留意它当前装的值是不是已经变了。"
                    "这也是初学循环和累计时非常关键的一种观察方式。"
                ),
                "example": (
                    "count = 1\n"
                    "count = count + 1\n"
                    "print(count)"
                ),
            },
            {
                "title": "4. 变量名应该尽量表达含义",
                "explanation": (
                    "短变量名在特别简单的场景里当然能用，但随着代码变多，可读性会迅速下降。"
                    "因此，更推荐使用能表达用途的名字，比如 `user_name`、`total_score`、`item_count`。"
                    "这样做的好处很直接：你以后重看代码时，不需要反复猜每个变量到底代表什么。"
                    "也就是说，好命名其实是在给未来的自己减负。"
                ),
                "example": (
                    "user_name = 'Alice'\n"
                    "item_count = 3\n"
                    "print(user_name)\n"
                    "print(item_count)"
                ),
            },
            {
                "title": "5. 学变量时，要同时留意“值”和“名字”的关系",
                "explanation": (
                    "有时候初学者会把注意力全放在变量名上，结果忘了真正重要的是变量现在存着什么值。"
                    "但另一方面，如果完全不关心名字，代码又会变得很难读。"
                    "因此，学变量其实是在练两件事：一方面要清楚值的变化，另一方面也要让名字表达清楚含义。"
                    "把这两点一起抓住，变量就不会再显得抽象。"
                ),
                "example": (
                    "price = 12\n"
                    "count = 2\n"
                    "total_price = price * count\n"
                    "print(total_price)"
                ),
            },
        ],
        "exercise": {
            "id": "variables-assignment-ex-01",
            "title": "计算总价",
            "expected_function": "total_price",
            "description": (
                "请写一个函数 `total_price(price, count)`，"
                "返回单价 `price` 和数量 `count` 对应的总价。"
                "这道题重点是把计算结果通过变量或表达式清楚地返回出来。"
            ),
            "requirements": [
                "函数名必须是 `total_price`。",
                "函数接收两个参数：`price` 和 `count`。",
                "返回值必须是 `price * count`。",
                "不要只在函数里打印结果。",
            ],
            "examples": [
                {"input": "total_price(10, 3)", "output": "30"},
                {"input": "total_price(7, 2)", "output": "14"},
            ],
            "hints": [
                "可以直接返回 `price * count`。",
                "也可以先把结果放进变量，再返回变量。",
            ],
            "starter_code": (
                "def total_price(price, count):\n"
                "    # TODO: 返回总价\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def total_price(price, count):\n"
                "    return price * count\n"
            ),
            "hidden_tests": [
                {"call": "total_price(10, 3)", "expected": 30},
                {"call": "total_price(7, 2)", "expected": 14},
                {"call": "total_price(5, 0)", "expected": 0},
            ],
        },
    },
    {
        "id": "operators",
        "language": "python",
        "title": "运算符基础",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3.1 Numbers / 菜鸟教程 Python3 运算符",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "写程序时，很多逻辑都离不开运算符。"
            "有的运算符负责算出新数字，有的负责比较大小，还有的负责把多个条件连起来。"
            "因此，运算符并不是零散符号，而是程序表达“怎么计算”和“怎么判断”的基础工具。"
            "把这些工具先用顺，后面的条件、循环和函数题都会更流畅。"
        ),
        "knowledge_points": [
            {
                "title": "1. 算术运算符负责做最基础的计算",
                "explanation": (
                    "像 `+`、`-`、`*`、`/` 这些算术运算符，本质上是在告诉程序怎样组合数字。"
                    "它们看起来和数学里很像，因此入门时通常比较容易上手。"
                    "不过，编程里更重要的是：你要慢慢习惯把这些计算写进表达式里，而不是只在脑子里算。"
                    "因此，学算术运算符也是在学会把“计算过程”交给程序。"
                ),
                "example": (
                    "print(2 + 3)\n"
                    "print(8 - 2)\n"
                    "print(4 * 5)\n"
                    "print(9 / 3)"
                ),
            },
            {
                "title": "2. 比较运算符会得到 `True` 或 `False`",
                "explanation": (
                    "像 `>`、`<`、`>=`、`==` 这样的比较运算符，作用不是算出新的数字，而是判断条件是否成立。"
                    "因此，它们的结果通常是布尔值，也就是 `True` 或 `False`。"
                    "也正因为如此，比较运算符在 `if` 和 `while` 里会特别常见。"
                    "换句话说，它们是在为后面的分支判断提供依据。"
                ),
                "example": (
                    "print(5 > 3)\n"
                    "print(2 == 2)\n"
                    "print(4 < 1)"
                ),
            },
            {
                "title": "3. 逻辑运算符能把多个条件连接起来",
                "explanation": (
                    "有时候一个条件不够，你需要同时判断好几件事。"
                    "这时就会用到 `and`、`or`、`not` 这样的逻辑运算符。"
                    "`and` 更像“并且”，`or` 更像“或者”，`not` 则是在把真假反过来。"
                    "因此，它们的作用不是新增知识点，而是让条件表达得更完整。"
                ),
                "example": (
                    "age = 18\n"
                    "has_ticket = True\n"
                    "print(age >= 18 and has_ticket)\n"
                    "print(age < 18 or has_ticket)"
                ),
            },
            {
                "title": "4. 运算优先级会影响最终结果",
                "explanation": (
                    "程序不会随便乱算，它也有自己的优先顺序。"
                    "比如乘除通常会先于加减，这一点和数学里是类似的。"
                    "不过，越是表达式变长时，越建议你适当加上括号。"
                    "因为括号不仅能帮助程序按你期待的顺序计算，也能帮助读代码的人更快理解你的意图。"
                ),
                "example": (
                    "print(2 + 3 * 4)\n"
                    "print((2 + 3) * 4)"
                ),
            },
            {
                "title": "5. 学运算符时，不要只记符号，要记“它在表达什么”",
                "explanation": (
                    "很多初学者会把运算符当成要背下来的符号表。"
                    "但更有效的做法，是把它们理解成语言里的连接词。"
                    "比如 `+` 是在合并数字，`>` 是在做比较，`and` 是在连接两个条件。"
                    "因此，你越是能把它们和实际意义联系起来，写条件和表达式时就越自然。"
                ),
                "example": (
                    "score = 85\n"
                    "print(score >= 60 and score <= 100)"
                ),
            },
        ],
        "exercise": {
            "id": "operators-ex-01",
            "title": "判断是否在区间内",
            "expected_function": "in_range",
            "description": (
                "请写一个函数 `in_range(n)`。"
                "如果 `n` 在 1 到 10 之间（包含 1 和 10），就返回 `True`，否则返回 `False`。"
                "这道题重点是练习比较运算符和逻辑运算符。"
            ),
            "requirements": [
                "函数名必须是 `in_range`。",
                "函数接收一个参数 `n`。",
                "`1 <= n <= 10` 时返回 `True`。",
                "否则返回 `False`。",
            ],
            "examples": [
                {"input": "in_range(5)", "output": "True"},
                {"input": "in_range(11)", "output": "False"},
            ],
            "hints": [
                "可以组合两个比较条件。",
                "也可以直接写成链式比较。",
            ],
            "starter_code": (
                "def in_range(n):\n"
                "    # TODO: 判断 n 是否在 1 到 10 之间\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def in_range(n):\n"
                "    return 1 <= n <= 10\n"
            ),
            "hidden_tests": [
                {"call": "in_range(1)", "expected": True},
                {"call": "in_range(10)", "expected": True},
                {"call": "in_range(11)", "expected": False},
            ],
        },
    },
    {
        "id": "type-conversion",
        "language": "python",
        "title": "类型转换",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3.1 Numbers / 菜鸟教程 Python3 数据类型转换",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "程序里不同类型的数据，并不总能直接混在一起使用。"
            "因此，学会把一种类型转换成另一种类型，是非常实用的一项基本功。"
            "尤其是在接收输入、处理数字和拼接字符串时，类型转换几乎一定会碰到。"
            "所以，这一节的重点不只是记住 `int()`、`str()`、`float()`，更是理解“为什么这里要转”。"
        ),
        "knowledge_points": [
            {
                "title": "1. 类型转换是在改变数据被解释的方式",
                "explanation": (
                    "同样看起来像数字的内容，程序未必会把它当成数字。"
                    "比如 `'12'` 这个字符串虽然长得像 12，但它本质上还是文本。"
                    "因此，类型转换的作用，就是告诉 Python：请把这个值按另一种类型来理解。"
                    "也正因为如此，转换通常发生在“我想换一种方式使用它”的时候。"
                ),
                "example": (
                    "text_num = '12'\n"
                    "real_num = int(text_num)\n"
                    "print(real_num + 3)"
                ),
            },
            {
                "title": "2. `int()` 常用来把内容转成整数",
                "explanation": (
                    "`int()` 很常见，因为很多时候你拿到的是字符串，但后面想做的是整数计算。"
                    "这在接收输入、读取文件内容或处理表单数据时都特别常见。"
                    "因此，看到 `int()` 时，不妨先问自己：这里是不是本来是文本，但我接下来想把它当数字用？"
                    "这个思路会帮助你更自然地理解它出现的原因。"
                ),
                "example": (
                    "age_text = '18'\n"
                    "age = int(age_text)\n"
                    "print(age + 1)"
                ),
            },
            {
                "title": "3. `str()` 常用来把值变成字符串",
                "explanation": (
                    "当你想把数字、布尔值或者其他对象放进文本里展示时，`str()` 就会很有用。"
                    "它的作用是把值变成字符串形式。"
                    "因此，它常常出现在拼接输出、打印信息或者生成提示文本的时候。"
                    "换句话说，`str()` 是在帮你把“值”变成“可以直接展示的文字”。"
                ),
                "example": (
                    "score = 95\n"
                    "message = '分数是 ' + str(score)\n"
                    "print(message)"
                ),
            },
            {
                "title": "4. `float()` 适合处理带小数的数字",
                "explanation": (
                    "有些数字不是整数，而是带小数的，比如价格、温度、平均值。"
                    "这时就会用到 `float()`。"
                    "它的作用，是把内容转换成浮点数，也就是小数形式的数字。"
                    "因此，当你面对的值可能有小数部分时，`float()` 往往比 `int()` 更合适。"
                ),
                "example": (
                    "price_text = '12.5'\n"
                    "price = float(price_text)\n"
                    "print(price + 0.5)"
                ),
            },
            {
                "title": "5. 学类型转换时，重点是观察“当前类型”和“目标类型”",
                "explanation": (
                    "很多类型转换问题，本质上都能拆成两个问题：它现在是什么类型？我想让它变成什么类型？"
                    "只要这两步清楚了，选用 `int()`、`str()` 还是 `float()` 通常就不难。"
                    "因此，别把类型转换只当成函数记忆题，更重要的是培养“先判断类型，再决定转换”的思维。"
                    "这个习惯会在后面的输入处理和数据清洗中非常有用。"
                ),
                "example": (
                    "num = '7'\n"
                    "print(type(num))\n"
                    "num = int(num)\n"
                    "print(type(num))"
                ),
            },
        ],
        "exercise": {
            "id": "type-conversion-ex-01",
            "title": "把字符串数字相加",
            "expected_function": "add_text_numbers",
            "description": (
                "请写一个函数 `add_text_numbers(a, b)`，"
                "其中 `a` 和 `b` 都是字符串形式的数字，比如 `'3'`、`'15'`。"
                "请把它们转换成整数后相加，并返回结果。"
            ),
            "requirements": [
                "函数名必须是 `add_text_numbers`。",
                "函数接收两个参数：`a` 和 `b`。",
                "需要先做类型转换，再相加。",
                "返回值必须是整数结果。",
            ],
            "examples": [
                {"input": "add_text_numbers('3', '4')", "output": "7"},
                {"input": "add_text_numbers('10', '5')", "output": "15"},
            ],
            "hints": [
                "可以分别用 `int(a)` 和 `int(b)`。",
                "不要直接写 `a + b`，那样会变成字符串拼接。",
            ],
            "starter_code": (
                "def add_text_numbers(a, b):\n"
                "    # TODO: 把字符串数字转换后相加\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def add_text_numbers(a, b):\n"
                "    return int(a) + int(b)\n"
            ),
            "hidden_tests": [
                {"call": "add_text_numbers('3', '4')", "expected": 7},
                {"call": "add_text_numbers('10', '5')", "expected": 15},
                {"call": "add_text_numbers('0', '8')", "expected": 8},
            ],
        },
    },
    {
        "id": "string-methods",
        "language": "python",
        "title": "常用字符串方法",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 5. Data Structures / 字符串方法文档 / 菜鸟教程 Python3 字符串",
            "url": "https://docs.python.org/3/library/stdtypes.html#string-methods",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "学完字符串基础以后，下一步自然会遇到一个问题：如果文本不是刚好长成我想要的样子，该怎么处理？"
            "这时，字符串方法就派上用场了。"
            "它们可以帮助你去空格、拆分文本、替换内容、统一大小写。"
            "因此，这一节本质上是在训练你把“原始文本”加工成“可用文本”。"
        ),
        "knowledge_points": [
            {
                "title": "1. 字符串方法是在对字符串做常见处理",
                "explanation": (
                    "字符串方法可以先理解成“字符串自带的一些常用工具”。"
                    "比如你想去掉首尾空格、把一句话拆成列表，或者把某个词替换掉，都可以借助这些方法。"
                    "因此，它们的作用不是让语法变复杂，而是在帮你处理真实文本。"
                    "也正因为现实数据往往没那么整齐，所以这些方法会特别常用。"
                ),
                "example": (
                    "text = ' hello '\n"
                    "print(text.strip())"
                ),
            },
            {
                "title": "2. `strip()` 常用来去掉首尾空格",
                "explanation": (
                    "很多时候，文本内容真正有用的部分没问题，但前后多了空格或换行。"
                    "这时，`strip()` 就很方便。"
                    "它会把字符串首尾多余的空白去掉，但中间的内容保留下来。"
                    "因此，在处理用户输入或文件内容时，`strip()` 往往是第一步常见操作。"
                ),
                "example": (
                    "name = '  Alice  '\n"
                    "print(name.strip())"
                ),
            },
            {
                "title": "3. `split()` 可以把一句话拆成多个部分",
                "explanation": (
                    "当你拿到的是一整段字符串，但后面需要分开处理其中的部分时，`split()` 很有用。"
                    "比如把一串用空格隔开的单词拆开，或者把逗号分隔的数据切成列表。"
                    "因此，`split()` 的核心作用可以理解成：把一整段文本按某个分隔符拆开。"
                    "这也是从“字符串处理”走向“列表处理”的一个常见入口。"
                ),
                "example": (
                    "text = 'apple banana orange'\n"
                    "words = text.split()\n"
                    "print(words)"
                ),
            },
            {
                "title": "4. `replace()`、`lower()`、`upper()` 常用来统一文本格式",
                "explanation": (
                    "现实中的文本经常不够整齐。"
                    "有时候你想把某个词替换掉，有时候想统一成小写或大写，这时就会用到这些方法。"
                    "因此，这些方法的共同目标其实很一致：让文本变得更适合比较、展示或继续处理。"
                    "也就是说，它们是在帮你给字符串“整理格式”。"
                ),
                "example": (
                    "text = 'Hello Python'\n"
                    "print(text.replace('Python', 'World'))\n"
                    "print(text.lower())\n"
                    "print(text.upper())"
                ),
            },
            {
                "title": "5. 学字符串方法时，要先想“我到底想把文本变成什么样”",
                "explanation": (
                    "很多初学者一看到字符串方法，就想一口气把名字全记下来。"
                    "但更实用的思路通常是反过来：我现在手里这段文本是什么样？我希望它最后变成什么样？"
                    "只要目标清楚了，你往往就更容易判断该用 `strip()`、`split()` 还是 `replace()`。"
                    "因此，方法记忆固然重要，但“先明确处理目标”会更关键。"
                ),
                "example": (
                    "text = '  apple,banana  '\n"
                    "clean = text.strip().replace(',', ' ')\n"
                    "print(clean)"
                ),
            },
        ],
        "exercise": {
            "id": "string-methods-ex-01",
            "title": "去掉首尾空格并转成小写",
            "expected_function": "clean_text",
            "description": (
                "请写一个函数 `clean_text(text)`，"
                "先去掉字符串首尾的空格，再把结果转换成小写后返回。"
                "比如传入 `'  HeLLo  '`，应返回 `'hello'`。"
            ),
            "requirements": [
                "函数名必须是 `clean_text`。",
                "函数接收一个参数 `text`。",
                "需要先去掉首尾空格。",
                "然后把结果转换成小写并返回。",
            ],
            "examples": [
                {"input": "clean_text('  HeLLo  ')", "output": "hello"},
                {"input": "clean_text('  PYTHON')", "output": "python"},
            ],
            "hints": [
                "可以先用 `strip()`。",
                "再在结果上继续调用 `lower()`。",
            ],
            "starter_code": (
                "def clean_text(text):\n"
                "    # TODO: 去掉首尾空格并转成小写\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def clean_text(text):\n"
                "    return text.strip().lower()\n"
            ),
            "hidden_tests": [
                {"call": "clean_text('  HeLLo  ')", "expected": "hello"},
                {"call": "clean_text('  PYTHON')", "expected": "python"},
                {"call": "clean_text('OpenAI  ')", "expected": "openai"},
            ],
        },
    },
    {
        "id": "dict-basics",
        "language": "python",
        "title": "字典基础",
        "topic": "data_structures",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 5.5 Dictionaries / 菜鸟教程 Python3 字典",
            "url": "https://docs.python.org/3/tutorial/datastructures.html#dictionaries",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "如果列表更像按顺序排好的一排数据，那么字典更像一个“标签 -> 内容”的对应表。"
            "它特别适合表示那些“根据名字找值”的场景，比如学生信息、商品属性、配置项等等。"
            "因此，学字典的关键，不只是记住大括号怎么写，而是先建立“键和值配对出现”的感觉。"
            "一旦这个感觉顺了，很多现实数据都会突然变得更好组织。"
        ),
        "knowledge_points": [
            {
                "title": "1. 字典保存的是“键 -> 值”的对应关系",
                "explanation": (
                    "列表更适合按位置取值，而字典更适合按名字找值。"
                    "也就是说，字典里的每一项都像一个配对：一个键，对应一个值。"
                    "因此，当你面对的不是“第几个元素”，而是“某个标签对应什么内容”时，字典通常更合适。"
                    "这也是它和列表最核心的区别之一。"
                ),
                "example": (
                    "student = {'name': 'Alice', 'score': 95}\n"
                    "print(student)"
                ),
            },
            {
                "title": "2. 通过键可以读取对应的值",
                "explanation": (
                    "字典最常见的操作，就是根据键去拿值。"
                    "比如你知道学生信息里有 `'name'` 这个键，就可以通过它找到名字。"
                    "因此，和列表里的索引不同，字典读取时更像是在问：这个标签对应的内容是什么？"
                    "换句话说，字典把“查找方式”从位置变成了名称。"
                ),
                "example": (
                    "student = {'name': 'Alice', 'score': 95}\n"
                    "print(student['name'])\n"
                    "print(student['score'])"
                ),
            },
            {
                "title": "3. 字典里的值可以修改，也可以新增键值对",
                "explanation": (
                    "字典并不是固定死的。"
                    "如果某个键已经存在，你可以修改它对应的值；如果某个键还不存在，也可以直接新增。"
                    "因此，字典特别适合表示那些会逐步补充、逐步更新的信息。"
                    "比如你先记录名字，后面再补年龄和城市，这种过程就很自然。"
                ),
                "example": (
                    "student = {'name': 'Alice'}\n"
                    "student['score'] = 95\n"
                    "student['name'] = 'Bob'\n"
                    "print(student)"
                ),
            },
            {
                "title": "4. `get()` 能让读取更稳一些",
                "explanation": (
                    "如果你直接用 `student['age']` 去拿一个不存在的键，程序可能会报错。"
                    "而 `get()` 提供了一种更稳的写法。"
                    "你可以把它理解成：先试着拿这个键，如果没有，就先给我一个默认值。"
                    "因此，在处理不确定是否存在的键时，`get()` 往往会更方便。"
                ),
                "example": (
                    "student = {'name': 'Alice'}\n"
                    "print(student.get('name'))\n"
                    "print(student.get('age', 0))"
                ),
            },
            {
                "title": "5. 学字典时，重点是想清楚“什么该做键，什么该做值”",
                "explanation": (
                    "初学字典时，语法本身通常不算太难，真正值得多想的是结构。"
                    "比如在学生信息里，`name`、`score`、`city` 这些通常适合做键；而具体的名字、分数和城市则适合做值。"
                    "因此，学字典不只是学一种新容器，更是在练习怎样组织数据。"
                    "一旦你越来越习惯用“标签 -> 内容”的方式去思考，很多信息都会变得更好管理。"
                ),
                "example": (
                    "book = {'title': 'Python 入门', 'price': 39}\n"
                    "print(book['title'])"
                ),
            },
        ],
        "exercise": {
            "id": "dict-basics-ex-01",
            "title": "读取字典中的姓名",
            "expected_function": "get_name",
            "description": (
                "请写一个函数 `get_name(student)`，"
                "其中 `student` 是一个字典，里面一定包含键 `'name'`。"
                "请返回这个字典里 `'name'` 对应的值。"
            ),
            "requirements": [
                "函数名必须是 `get_name`。",
                "函数接收一个参数 `student`。",
                "返回字典中键 `'name'` 对应的值。",
                "不要只打印结果，要返回结果。",
            ],
            "examples": [
                {"input": "get_name({'name': 'Alice', 'score': 95})", "output": "Alice"},
                {"input": "get_name({'name': 'Bob'})", "output": "Bob"},
            ],
            "hints": [
                "可以通过键来取值。",
                "题目已经保证 `'name'` 一定存在。",
            ],
            "starter_code": (
                "def get_name(student):\n"
                "    # TODO: 返回 student 中 'name' 对应的值\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def get_name(student):\n"
                "    return student['name']\n"
            ),
            "hidden_tests": [
                {"call": "get_name({'name': 'Alice', 'score': 95})", "expected": "Alice"},
                {"call": "get_name({'name': 'Bob'})", "expected": "Bob"},
                {"call": "get_name({'name': '小明', 'city': '上海'})", "expected": "小明"},
            ],
        },
    },
    {
        "id": "python-interpreter",
        "language": "python",
        "title": "解释器与交互模式",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 2. Using the Python Interpreter",
            "url": "https://docs.python.org/3/tutorial/interpreter.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "很多初学者一上来会觉得编程像在念咒，其实第一步没有那么玄。"
            "与其一开始就逼自己写很长的程序，不如先认识 Python 解释器。"
            "你可以把它理解成一个会立刻回应你的练习对象：你输入一小段代码，它马上给你结果。"
            "也正因为这种反馈几乎是即时的，所以它特别适合入门阶段拿来建立手感。"
            "等你先在交互模式里把“输入一行、看一眼结果、再改一改”的节奏走顺了，"
            "后面再去写脚本文件、函数和更完整的程序，心里会踏实很多。"
        ),
        "knowledge_points": [
            {
                "title": "1. 解释器像一个会立刻回应你的练习本",
                "explanation": (
                    "Python 解释器最适合做的第一件事，不是写大项目，而是先建立“我写一句，它回一句”的直觉。"
                    "换句话说，它更像一个随时待命的小练习场，而不是一次就要交卷的大考场。"
                    "比如你不确定 `2 + 3 * 4` 会先算什么，直接试一下，比自己硬猜轻松得多。"
                    "而且你会马上看到结果，这一点很关键，因为它会帮你把抽象语法和真实输出连起来。"
                    "所以在入门阶段，先习惯这种小步试验的节奏，通常比一上来追求完整作品更重要。"
                ),
                "example": (
                    ">>> 2 + 3\n"
                    "5\n"
                    ">>> 2 + 3 * 4\n"
                    "14"
                ),
            },
            {
                "title": "2. 看到 `>>>`，就说明 Python 在等你输入",
                "explanation": (
                    "交互模式里最显眼的标志就是提示符 `>>>`。"
                    "它的意思很简单：Python 已经准备好了，你现在可以输入一条语句或表达式。"
                    "也就是说，当你看到这个符号时，不用紧张，它不是报错，而是在邀请你继续输入。"
                    "进一步说，如果你看到 `...`，通常表示上一行还没有结束，比如你刚写了 `if` 或函数定义，"
                    "Python 还在等你把后面的代码块补完整。"
                    "所以，学会区分 `>>>` 和 `...`，其实就是在学会看懂解释器现在处于什么状态。"
                ),
                "example": (
                    ">>> print('hello')\n"
                    "hello\n"
                    ">>> if 3 > 1:\n"
                    "...     print('yes')\n"
                    "yes"
                ),
            },
            {
                "title": "3. 交互模式适合试想法，不适合长期保存",
                "explanation": (
                    "刚开始学的时候，交互模式特别适合拿来试小片段：算一算、改一改、看看字符串怎么拼。"
                    "也正因为它足够轻便，所以你几乎不用担心写错，试错成本很低。"
                    "不过另一方面，它也有个天然缺点：你这次输入的内容，通常不会自动变成一份方便以后复习的正式程序。"
                    "所以更准确地说，它像草稿纸，适合先验证想法；而真正要保存成果、整理结构时，还是要回到 `.py` 文件里。"
                ),
                "example": (
                    ">>> name = 'Alice'\n"
                    ">>> 'Hello, ' + name\n"
                    "'Hello, Alice!'"
                ),
            },
            {
                "title": "4. 报错不是“你不行”，而是 Python 在指出位置",
                "explanation": (
                    "初学时最容易被报错吓住，但其实报错信息往往是在告诉你：哪一行附近出了问题。"
                    "换个角度看，报错不是在说“你不适合学编程”，而是在说“这一小步需要再调一下”。"
                    "尤其在交互模式里，试错成本很低，改一下再敲一次就行。"
                    "所以，与其害怕报错，不如把它当成一种即时反馈。"
                    "当你慢慢习惯先看位置、再看原因、最后再修改时，调试能力其实就已经在悄悄增长了。"
                ),
                "example": (
                    ">>> print('hello'\n"
                    "SyntaxError: '(' was never closed"
                ),
            },
            {
                "title": "5. 学解释器，不是为了炫技，而是为了先把手热起来",
                "explanation": (
                    "很多基础概念，比如数字计算、字符串拼接、布尔判断，都很适合先在解释器里摸一遍。"
                    "因为这些内容本身不长，所以最适合拿来建立“代码会怎么响应我”的第一感觉。"
                    "你不需要一开始就写很长的程序，反而越是基础阶段，越值得把动作拆小。"
                    "先把“输入代码 -> 看到结果 -> 修改再试”这条链路走顺，后面学脚本、函数和项目时会轻松很多。"
                    "也就是说，解释器这一关看起来简单，其实是在帮你铺后面的路。"
                ),
                "example": (
                    ">>> 10 > 3\n"
                    "True\n"
                    ">>> 'Py' + 'thon'\n"
                    "'Python'"
                ),
            },
        ],
        "exercise": {
            "id": "python-interpreter-ex-01",
            "title": "写一个返回问候语的小函数",
            "expected_function": "say_hello",
            "description": (
                "交互模式里我们已经试过字符串和 `print` 了。"
                "现在把这个小想法整理成一个函数：请写一个叫 `say_hello` 的函数，"
                "它接收一个名字 `name`，然后返回字符串 `Hi, 名字!`。"
                "比如传入 `Tom`，应该返回 `Hi, Tom!`。"
            ),
            "requirements": [
                "函数名必须是 `say_hello`。",
                "函数必须接收一个参数 `name`。",
                "返回值必须是字符串，而不是只在屏幕上打印。",
                "传入 `Tom` 时应返回 `Hi, Tom!`。",
            ],
            "examples": [
                {"input": "say_hello('Tom')", "output": "Hi, Tom!"},
                {"input": "say_hello('Python')", "output": "Hi, Python!"},
            ],
            "hints": [
                "先把函数头写出来：`def say_hello(name):`。",
                "题目要的是“返回结果”，所以请用 `return`。",
                "可以写成：`return f\"Hi, {name}!\"`。",
            ],
            "starter_code": (
                "def say_hello(name):\n"
                "    # TODO: 返回形如 Hi, Tom! 的字符串\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def say_hello(name):\n"
                "    return f\"Hi, {name}!\"\n"
            ),
            "hidden_tests": [
                {"call": "say_hello('Tom')", "expected": "Hi, Tom!"},
                {"call": "say_hello('Alice')", "expected": "Hi, Alice!"},
                {"call": "say_hello('Python')", "expected": "Hi, Python!"},
            ],
        },
    },
    {
        "id": "python-script-basics",
        "language": "python",
        "title": "脚本文件与第一段程序",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 2.1 / 菜鸟教程 Python3 基础语法",
            "url": "https://docs.python.org/3/tutorial/interpreter.html#invoking-the-interpreter",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "如果说交互模式像草稿纸，那么 `.py` 脚本文件更像正式作业本。"
            "在这里，你不再只是试两三句代码，而是开始把一段完整的想法保存下来，反复运行、修改、整理。"
            "也正因为代码被放进了文件里，所以它第一次有了“可以回看、可以复用、可以慢慢变整齐”的感觉。"
            "这一节最重要的不是知识点有多难，而是你开始真正把代码“写成一个文件”。"
        ),
        "knowledge_points": [
            {
                "title": "1. `.py` 文件就是 Python 程序最常见的载体",
                "explanation": (
                    "当代码开始不止一两行时，把它写进 `.py` 文件会更自然。"
                    "因为一旦内容多起来，交互模式虽然方便，却不太适合整理结构。"
                    "而写进文件之后，你可以保存、复查、分享，也可以下次继续改。"
                    "所以很多人真正从“试着玩代码”走向“开始写程序”，就是从会新建一个 `.py` 文件开始的。"
                ),
                "example": (
                    "# hello.py\n"
                    "print('Hello, Python!')"
                ),
            },
            {
                "title": "2. 脚本运行时，代码通常会按从上到下的顺序执行",
                "explanation": (
                    "刚开始学习时，可以先把 Python 程序理解成“从上往下读”的。"
                    "也就是说，第一行先做什么，第二行再做什么，结果会一步步累积起来。"
                    "正因为执行顺序通常是明确的，所以变量往往要先赋值，再在后面使用。"
                    "如果顺序写反了，程序就会找不到你还没准备好的内容。"
                ),
                "example": (
                    "name = 'Alice'\n"
                    "message = 'Hello, ' + name\n"
                    "print(message)"
                ),
            },
            {
                "title": "3. `print` 是把结果展示出来，不是把知识点变复杂",
                "explanation": (
                    "`print` 对初学者特别重要，因为它是你和程序之间最直接的沟通方式。"
                    "一方面，你可以用它展示最终答案；另一方面，你也可以在调试时看看某个变量里到底装了什么。"
                    "所以它既是输出工具，也是观察工具。"
                    "很多“我以为它是这样，结果不是”的瞬间，都是靠 `print` 看清楚的。"
                ),
                "example": (
                    "count = 3\n"
                    "print(count)\n"
                    "print('当前数量是', count)"
                ),
            },
            {
                "title": "4. 注释是在给未来的自己留台阶",
                "explanation": (
                    "注释不是给机器看的，而是给人看的。"
                    "也就是说，程序能不能运行，通常不靠注释决定；但你能不能快速看懂自己的代码，注释却很有帮助。"
                    "当你过几天再打开代码时，一句短注释常常能帮你迅速想起这段代码想干什么。"
                    "因此，在初学阶段养成写简短注释的习惯，会让你后面复盘时轻松很多。"
                ),
                "example": (
                    "# 记录用户名字\n"
                    "name = 'Alice'\n"
                    "# 输出问候语\n"
                    "print('Hello, ' + name)"
                ),
            },
            {
                "title": "5. 从脚本开始，你就在练习“组织代码”",
                "explanation": (
                    "哪怕只是三五行代码，只要它被放进文件里，你其实已经在做一件很重要的事："
                    "把一个临时想法，变成一个可以保存、运行、修改的作品。"
                    "而这件事看似普通，其实是在训练你组织代码的能力。"
                    "也正因为有了文件、顺序和结构，后面学函数、模块和项目结构时，你才不会觉得它们是突然冒出来的新东西。"
                ),
                "example": (
                    "title = 'Python 入门'\n"
                    "print(title)\n"
                    "print('开始第一段脚本练习')"
                ),
            },
        ],
        "exercise": {
            "id": "python-script-basics-ex-01",
            "title": "返回课程标题",
            "expected_function": "course_title",
            "description": (
                "请写一个叫 `course_title` 的函数，不需要参数，"
                "直接返回字符串 `Python 入门`。"
                "这道题的重点不是难度，而是让你熟悉“把结果写进一个正式函数里”。"
            ),
            "requirements": [
                "函数名必须是 `course_title`。",
                "这个函数不需要参数。",
                "必须返回字符串 `Python 入门`。",
                "不要只用 `print` 输出结果。",
            ],
            "examples": [
                {"input": "course_title()", "output": "Python 入门"},
            ],
            "hints": [
                "没有参数的函数可以写成：`def course_title():`。",
                "题目要的是返回值，所以请用 `return`。",
            ],
            "starter_code": (
                "def course_title():\n"
                "    # TODO: 返回字符串 Python 入门\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def course_title():\n"
                "    return 'Python 入门'\n"
            ),
            "hidden_tests": [
                {"call": "course_title()", "expected": "Python 入门"},
            ],
        },
    },
    {
        "id": "numbers-and-variables",
        "language": "python",
        "title": "数字、变量与表达式",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3. An Informal Introduction to Python",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "学编程的一开始，最常见的材料就是数字和变量。"
            "数字负责表示数量，变量负责把这些结果临时记下来；而表达式则是在这个过程中不断产生新结果。"
            "所以，这一节虽然看起来基础，却几乎是后面所有内容的地基。"
            "判断、循环、函数，甚至更复杂的程序组织，本质上都离不开这些最基本的动作。"
        ),
        "knowledge_points": [
            {
                "title": "1. 数字在程序里不只是“写出来”，还会参与计算",
                "explanation": (
                    "Python 可以像计算器一样处理加减乘除。"
                    "这件事看起来简单，但它很重要，因为你会慢慢意识到：程序不是只会显示文字，"
                    "它还可以根据规则算出新结果。"
                    "换句话说，代码不只是“写给人看”的，它还真的会参与运算。"
                    "而这正是编程最有力量的地方之一。"
                ),
                "example": (
                    "print(2 + 3)\n"
                    "print(10 - 4)\n"
                    "print(6 * 3)\n"
                    "print(8 / 2)"
                ),
            },
            {
                "title": "2. 变量像一个有名字的便签，用来记住结果",
                "explanation": (
                    "变量可以理解成“给一个结果起名字”。"
                    "比如你先算出总分，再把它命名为 `score`，后面就不用把原来的计算重写一遍。"
                    "这样一来，代码就不只是有结果，还开始有了更清楚的结构。"
                    "初学时把变量想成“贴了标签的结果”，通常会比想成抽象容器更顺手。"
                ),
                "example": (
                    "score = 95\n"
                    "age = 18\n"
                    "print(score)\n"
                    "print(age)"
                ),
            },
            {
                "title": "3. 赋值不是数学里的等号，而是“把右边交给左边”",
                "explanation": (
                    "在 Python 里，`=` 更像是一种交接动作。"
                    "比如 `total = 2 + 3` 的意思不是在证明左边等于右边，"
                    "而是先算出右边的结果 5，再把这个结果交给变量 `total`。"
                    "也正因为如此，编程里的赋值和数学里的等号并不是一回事。"
                    "这个理解特别关键，不然后面一看到变量更新就容易迷糊。"
                ),
                "example": (
                    "total = 2 + 3\n"
                    "print(total)  # 5"
                ),
            },
            {
                "title": "4. 表达式会产生结果，变量可以把它接住",
                "explanation": (
                    "像 `3 * 4 + 1` 这样的写法，叫表达式。"
                    "它的价值不在于长得复杂，而在于它最终会算出一个结果。"
                    "因此，表达式其实就是程序里“产生新值”的一种常见方式。"
                    "你可以直接打印它，也可以先交给变量保存，再在别处继续使用。"
                ),
                "example": (
                    "result = 3 * 4 + 1\n"
                    "print(result)"
                ),
            },
            {
                "title": "5. 变量名要尽量表达意思，代码才不容易糊成一团",
                "explanation": (
                    "一开始很多人喜欢随手写 `a`、`b`、`x`，短期内好像没问题。"
                    "但是，只要代码稍微多一点，你就会忘记它们分别表示什么。"
                    "所以从基础阶段起，尽量写像 `total_score`、`user_age` 这种更有含义的名字，"
                    "会让你未来轻松很多。"
                    "更进一步说，这不是形式问题，而是在帮你和未来的自己降低理解成本。"
                ),
                "example": (
                    "item_price = 12\n"
                    "item_count = 3\n"
                    "total_price = item_price * item_count\n"
                    "print(total_price)"
                ),
            },
        ],
        "exercise": {
            "id": "numbers-and-variables-ex-01",
            "title": "计算长方形面积",
            "expected_function": "rectangle_area",
            "description": (
                "请写一个函数 `rectangle_area(width, height)`，"
                "接收长方形的宽和高，返回它的面积。"
                "比如宽是 3，高是 4，就应该返回 12。"
            ),
            "requirements": [
                "函数名必须是 `rectangle_area`。",
                "函数要接收两个参数：`width` 和 `height`。",
                "返回值必须是宽乘高的结果。",
                "不要只在函数里打印答案。",
            ],
            "examples": [
                {"input": "rectangle_area(3, 4)", "output": "12"},
                {"input": "rectangle_area(5, 2)", "output": "10"},
            ],
            "hints": [
                "面积可以直接写成 `width * height`。",
                "记得把结果用 `return` 返回出去。",
            ],
            "starter_code": (
                "def rectangle_area(width, height):\n"
                "    # TODO: 返回长方形面积\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def rectangle_area(width, height):\n"
                "    return width * height\n"
            ),
            "hidden_tests": [
                {"call": "rectangle_area(3, 4)", "expected": 12},
                {"call": "rectangle_area(5, 2)", "expected": 10},
                {"call": "rectangle_area(7, 1)", "expected": 7},
            ],
        },
    },
    {
        "id": "strings-basics",
        "language": "python",
        "title": "字符串基础",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3.1.2 Strings / 菜鸟教程 Python3 字符串",
            "url": "https://docs.python.org/3/tutorial/introduction.html#strings",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "字符串就是程序里的文本。"
            "用户名、问候语、提示信息、文件名，很多你看得见的内容本质上都是字符串。"
            "不过，字符串并不是“只能原样摆着不动”的文字；相反，它也是一种可以被拼接、截取、格式化的数据。"
            "所以，这一节最重要的不是死记方法，而是先建立“字符串也是可以操作的”这种感觉。"
        ),
        "knowledge_points": [
            {
                "title": "1. 字符串就是被引号包起来的文本",
                "explanation": (
                    "在 Python 里，只要一段内容被单引号或双引号包起来，它通常就是字符串。"
                    "这一步看似简单，但非常关键，因为 Python 要靠这个区分："
                    "你写的是变量名，还是一段普通文本。"
                    "也就是说，引号不只是外壳，它其实是在告诉 Python：这里面是文本内容。"
                ),
                "example": (
                    "name = 'Alice'\n"
                    "message = \"Hello\"\n"
                    "print(name)\n"
                    "print(message)"
                ),
            },
            {
                "title": "2. 字符串可以拼接，像把两段话接在一起",
                "explanation": (
                    "用 `+` 可以把两个字符串连起来。"
                    "这在初学阶段特别常见，比如把问候语和用户名拼成一句完整的话。"
                    "不过也正因为程序很老实，所以拼接时要留意空格和标点，它不会自动替你补。"
                    "因此，字符串拼接看起来只是连一连，实际上也在训练你对结果细节的敏感度。"
                ),
                "example": (
                    "first = 'Hello'\n"
                    "name = 'Alice'\n"
                    "message = first + ', ' + name + '!'\n"
                    "print(message)"
                ),
            },
            {
                "title": "3. 索引像在文本里按位置取字符",
                "explanation": (
                    "Python 里字符串里的第一个字符位置是 0，不是 1。"
                    "这点一开始很容易不习惯，但用几次就会慢慢顺下来。"
                    "比如 `'Python'[0]` 取到的是 `P`，`'Python'[1]` 取到的是 `y`。"
                    "而一旦你习惯了这种从 0 开始的编号方式，后面学列表、切片和循环时都会更顺。"
                ),
                "example": (
                    "word = 'Python'\n"
                    "print(word[0])\n"
                    "print(word[1])"
                ),
            },
            {
                "title": "4. 切片是在一整段文本里截一小段出来",
                "explanation": (
                    "如果索引是取一个字符，那切片就是取一段。"
                    "比如 `word[0:3]` 会从位置 0 开始，取到位置 3 之前。"
                    "也就是说，它更像是在一整段文本里截出一个小片段。"
                    "初学时可以先记住一个朴素规则：前面包含，后面不包含。"
                ),
                "example": (
                    "word = 'Python'\n"
                    "print(word[0:2])\n"
                    "print(word[2:6])"
                ),
            },
            {
                "title": "5. f-string 是更自然地把变量放进句子里",
                "explanation": (
                    "当你需要把变量嵌进字符串时，f-string 往往比手工拼接更清楚。"
                    "因为它读起来更像人在写一句完整的话，所以可读性通常会更好。"
                    "也正因为这样，它会成为你后面写提示信息、报错说明、问候语时经常用到的工具。"
                ),
                "example": (
                    "name = 'Alice'\n"
                    "age = 18\n"
                    "print(f'{name} is {age} years old.')"
                ),
            },
        ],
        "exercise": {
            "id": "strings-basics-ex-01",
            "title": "生成自我介绍",
            "expected_function": "introduce",
            "description": (
                "请写一个函数 `introduce(name, city)`，"
                "返回一句自我介绍：`我是名字，我来自城市。`"
                "比如传入 `小明` 和 `上海`，应返回 `我是小明，我来自上海。`"
            ),
            "requirements": [
                "函数名必须是 `introduce`。",
                "函数要接收两个参数：`name` 和 `city`。",
                "返回值必须是完整字符串，而不是打印。",
                "标点要和题目要求一致。",
            ],
            "examples": [
                {"input": "introduce('小明', '上海')", "output": "我是小明，我来自上海。"},
                {"input": "introduce('Alice', 'Beijing')", "output": "我是Alice，我来自Beijing。"},
            ],
            "hints": [
                "可以考虑使用 f-string。",
                "注意题目要求的是中文逗号和句号。",
            ],
            "starter_code": (
                "def introduce(name, city):\n"
                "    # TODO: 返回一句自我介绍\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def introduce(name, city):\n"
                "    return f\"我是{name}，我来自{city}。\"\n"
            ),
            "hidden_tests": [
                {"call": "introduce('小明', '上海')", "expected": "我是小明，我来自上海。"},
                {"call": "introduce('Alice', 'Beijing')", "expected": "我是Alice，我来自Beijing。"},
                {"call": "introduce('Tom', '杭州')", "expected": "我是Tom，我来自杭州。"},
            ],
        },
    },
    {
        "id": "lists-basics",
        "language": "python",
        "title": "列表基础",
        "topic": "data_structures",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 3.1.3 Lists / 菜鸟教程 Python3 列表",
            "url": "https://docs.python.org/3/tutorial/introduction.html#lists",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "如果说字符串是一段文本，那么列表更像一排可以按顺序摆放的数据。"
            "你可以把多个数字、名字或别的内容装进同一个列表里，而不是给每个值都单独起一个变量名。"
            "也正因为列表能把“多个相关数据”组织到一起，所以后面的循环、统计和筛选题，都会频繁用到它。"
        ),
        "knowledge_points": [
            {
                "title": "1. 列表适合把多个值按顺序放在一起",
                "explanation": (
                    "当你只有一个名字时，一个变量就够了。"
                    "但如果你要保存一组名字、一组分数或一组商品，列表会更合适。"
                    "因为这时候你面对的已经不是“一个值”，而是一组彼此相关的数据。"
                    "列表最大的价值，就是把多份同类数据组织成一个整体。"
                ),
                "example": (
                    "names = ['Alice', 'Bob', 'Cindy']\n"
                    "scores = [95, 88, 76]\n"
                    "print(names)\n"
                    "print(scores)"
                ),
            },
            {
                "title": "2. 列表同样可以按索引取元素",
                "explanation": (
                    "列表和字符串一样，也从 0 开始编号。"
                    "所以 `names[0]` 取到的是第一个元素，不是第二个。"
                    "这个规则一开始容易搞错，但它会贯穿很多 Python 容器。"
                    "因此，越早把这个编号习惯练熟，后面学别的容器时越省力。"
                ),
                "example": (
                    "names = ['Alice', 'Bob', 'Cindy']\n"
                    "print(names[0])\n"
                    "print(names[2])"
                ),
            },
            {
                "title": "3. 列表是可变的，可以改、可以加",
                "explanation": (
                    "列表很实用的一点是它可以修改。"
                    "你既可以替换某个位置上的元素，也可以在末尾继续追加新元素。"
                    "换句话说，列表不是一张写死的表，而是一组会变化的数据。"
                    "这也正是为什么它特别适合用来表示成绩单、任务清单之类会不断更新的内容。"
                ),
                "example": (
                    "numbers = [1, 2, 3]\n"
                    "numbers[1] = 20\n"
                    "numbers.append(4)\n"
                    "print(numbers)"
                ),
            },
            {
                "title": "4. `append` 很常见，它是在列表末尾加一个新元素",
                "explanation": (
                    "初学阶段你会很常见到 `append`。"
                    "它的意思不复杂：把一个新元素加到列表最后面。"
                    "不过，它的重要性并不只是“多记住一个方法”，而是你会开始接触“先准备一个列表，再一点点把结果收集起来”这种编程思路。"
                    "很多“收集结果”的程序，都是这样做的。"
                ),
                "example": (
                    "tasks = []\n"
                    "tasks.append('写作业')\n"
                    "tasks.append('复习 Python')\n"
                    "print(tasks)"
                ),
            },
            {
                "title": "5. 学列表时，先把“顺序”和“变化”这两个感觉抓住",
                "explanation": (
                    "一开始不必急着背太多方法。"
                    "先记住两件事就够了：列表里的元素有顺序；列表的内容还可以变化。"
                    "只要这两个感觉抓住了，你就能理解为什么它适合被遍历、适合被修改，也适合被统计。"
                    "因此，后面学遍历、筛选和统计时，就不会觉得像突然跳到新世界。"
                ),
                "example": (
                    "fruits = ['apple', 'banana']\n"
                    "fruits.append('orange')\n"
                    "print(fruits[0])\n"
                    "print(fruits)"
                ),
            },
        ],
        "exercise": {
            "id": "lists-basics-ex-01",
            "title": "返回列表第一个元素",
            "expected_function": "first_item",
            "description": (
                "请写一个函数 `first_item(items)`，"
                "接收一个非空列表，返回这个列表的第一个元素。"
                "比如传入 `[10, 20, 30]`，应该返回 `10`。"
            ),
            "requirements": [
                "函数名必须是 `first_item`。",
                "函数要接收一个参数 `items`。",
                "返回值必须是列表的第一个元素。",
                "可以假设传入的列表不是空列表。",
            ],
            "examples": [
                {"input": "first_item([10, 20, 30])", "output": "10"},
                {"input": "first_item(['a', 'b'])", "output": "a"},
            ],
            "hints": [
                "第一个元素的索引是 `0`。",
                "可以直接返回 `items[0]`。",
            ],
            "starter_code": (
                "def first_item(items):\n"
                "    # TODO: 返回列表第一个元素\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def first_item(items):\n"
                "    return items[0]\n"
            ),
            "hidden_tests": [
                {"call": "first_item([10, 20, 30])", "expected": 10},
                {"call": "first_item(['a', 'b'])", "expected": "a"},
                {"call": "first_item([True, False])", "expected": True},
            ],
        },
    },
    {
        "id": "if-statements",
        "language": "python",
        "title": "if 条件判断",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4.1 if Statements",
            "url": "https://docs.python.org/3/tutorial/controlflow.html#if-statements",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "从这一节开始，程序不再只是乖乖从上到下走。"
            "它开始学会“看情况做决定”：条件满足时走这条路，不满足时走另一条路。"
            "也就是说，程序第一次真正表现出一点“会判断”的样子。"
            "而这一步非常关键，因为真实问题几乎总是带着条件和分支。"
        ),
        "knowledge_points": [
            {
                "title": "1. `if` 的本质是：条件成立才执行后面的代码",
                "explanation": (
                    "`if` 可以理解成“如果……那么……”。"
                    "当条件结果是 `True` 时，缩进里的代码才会执行。"
                    "反过来说，如果条件不成立，这一块代码就会被跳过。"
                    "所以，这个结构看起来简单，却是程序具备“判断能力”的起点。"
                ),
                "example": (
                    "age = 18\n"
                    "if age >= 18:\n"
                    "    print('你已经成年了')"
                ),
            },
            {
                "title": "2. 条件表达式会先算出 `True` 或 `False`",
                "explanation": (
                    "像 `score >= 60`、`name == 'Alice'` 这样的写法，本质上是在提问：这件事对不对？"
                    "Python 会先得到布尔结果，再决定 `if` 里的代码要不要运行。"
                    "所以判断题里，真正的核心常常不是后面的 `return` 或 `print`，而是前面的条件有没有写准。"
                    "先把条件想清楚，后面的分支通常就顺了。"
                ),
                "example": (
                    "score = 75\n"
                    "print(score >= 60)\n"
                    "print(score < 60)"
                ),
            },
            {
                "title": "3. `else` 表示另一种情况",
                "explanation": (
                    "很多时候问题不是“满足就做”，而是“满足做 A，不满足做 B”。"
                    "这时就需要 `else`。"
                    "它像是在补上一句：如果前面的条件不成立，那就走这里。"
                    "因此，`if` 和 `else` 放在一起时，程序的两条主要路径就更完整了。"
                ),
                "example": (
                    "score = 58\n"
                    "if score >= 60:\n"
                    "    print('及格')\n"
                    "else:\n"
                    "    print('还需要再练习')"
                ),
            },
            {
                "title": "4. 缩进不是装饰，它决定哪段代码属于判断块",
                "explanation": (
                    "Python 不用大括号，而是用缩进表示一段代码是不是属于 `if`。"
                    "这意味着缩进一错，程序逻辑就可能跟你以为的完全不同。"
                    "也就是说，缩进在 Python 里不是排版装饰，而是语法的一部分。"
                    "所以学 `if` 时，除了条件本身，缩进也是必须一起练的基本功。"
                ),
                "example": (
                    "temperature = 30\n"
                    "if temperature > 28:\n"
                    "    print('今天有点热')\n"
                    "print('记得喝水')"
                ),
            },
            {
                "title": "5. 做判断题时，先把题目翻译成“什么情况下成立”",
                "explanation": (
                    "很多初学者不是不会写 `if`，而是不知道该判断什么。"
                    "一个实用办法是先用人话说清楚：什么情况下算通过？什么情况下算偶数？"
                    "当这句人话清楚了，代码里的条件通常也就更容易写出来。"
                    "因此，写判断题时先别急着敲代码，先把判定标准说清楚，反而更快。"
                ),
                "example": (
                    "number = 8\n"
                    "if number % 2 == 0:\n"
                    "    print('偶数')"
                ),
            },
        ],
        "exercise": {
            "id": "if-statements-ex-01",
            "title": "判断是否及格",
            "expected_function": "is_pass",
            "description": (
                "请写一个函数 `is_pass(score)`。"
                "如果分数大于等于 60，就返回字符串 `及格`；"
                "否则返回字符串 `不及格`。"
            ),
            "requirements": [
                "函数名必须是 `is_pass`。",
                "函数接收一个参数 `score`。",
                "分数大于等于 60 返回 `及格`。",
                "否则返回 `不及格`。",
            ],
            "examples": [
                {"input": "is_pass(80)", "output": "及格"},
                {"input": "is_pass(59)", "output": "不及格"},
            ],
            "hints": [
                "先判断 `score >= 60` 是否成立。",
                "题目要的是返回字符串，不是打印。",
            ],
            "starter_code": (
                "def is_pass(score):\n"
                "    # TODO: 根据分数返回 及格 或 不及格\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def is_pass(score):\n"
                "    if score >= 60:\n"
                "        return '及格'\n"
                "    return '不及格'\n"
            ),
            "hidden_tests": [
                {"call": "is_pass(80)", "expected": "及格"},
                {"call": "is_pass(60)", "expected": "及格"},
                {"call": "is_pass(59)", "expected": "不及格"},
            ],
        },
    },
    {
        "id": "for-range-loops",
        "language": "python",
        "title": "for 循环与 range",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4.2 for Statements / 4.3 The range() Function",
            "url": "https://docs.python.org/3/tutorial/controlflow.html#the-range-function",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "循环的意义，不是把代码写复杂，而是帮你处理“重复的事情”。"
            "当你发现同样的动作要做很多次时，`for` 往往就是更自然的工具。"
            "而 `range` 则是在告诉 Python：这次循环一共做多少轮。"
            "所以，这一节真正要练的，不只是语法，而是把“重复步骤”看成一种可以交给程序自动完成的事情。"
        ),
        "knowledge_points": [
            {
                "title": "1. `for` 适合按顺序处理一组内容",
                "explanation": (
                    "如果你要一个个看列表里的元素，`for` 会比手动写很多次 `print` 自然得多。"
                    "它的感觉很像：把这一组数据挨个拿出来，每次处理一个。"
                    "也正因为每一轮只处理一个元素，所以你不用一次把所有步骤都想得很复杂。"
                    "理解这一点后，循环就不再像语法机关，而是一个省力工具。"
                ),
                "example": (
                    "names = ['Alice', 'Bob', 'Cindy']\n"
                    "for name in names:\n"
                    "    print(name)"
                ),
            },
            {
                "title": "2. `range(n)` 会生成从 0 开始到 n 之前的数",
                "explanation": (
                    "`range(5)` 并不是 1 到 5，而是 0、1、2、3、4。"
                    "这件事一开始很容易绕，但多试几次就会发现它和 Python 从 0 开始编号的习惯是统一的。"
                    "也就是说，`range(n)` 更像是在说：给我一串从 0 开始、总共 n 个数。"
                    "所以它很常拿来表示“做 n 次”。"
                ),
                "example": (
                    "for i in range(5):\n"
                    "    print(i)"
                ),
            },
            {
                "title": "3. 循环变量会在每一轮拿到当前值",
                "explanation": (
                    "在 `for i in range(5)` 里，`i` 就是循环变量。"
                    "每一轮循环，`i` 都会变成当前这轮对应的值。"
                    "因此，你可以利用它做计数、计算，或者拼出不同的输出。"
                    "很多看起来会变化的结果，其实就是借助循环变量一点点生成出来的。"
                ),
                "example": (
                    "for i in range(3):\n"
                    "    print(f'这是第 {i} 轮')"
                ),
            },
            {
                "title": "4. 循环最常见的用途之一是“累计”和“重复生成”",
                "explanation": (
                    "比如你想把 1 到 5 加起来，或者想生成 5 次问候语，"
                    "本质上都是把一件动作重复地做。"
                    "而循环最有价值的地方就在这里：它允许你在每一轮都更新一点结果。"
                    "很多基础算法题，其实就是在练这种“每轮更新一点结果”的感觉。"
                ),
                "example": (
                    "total = 0\n"
                    "for i in range(1, 6):\n"
                    "    total += i\n"
                    "print(total)"
                ),
            },
            {
                "title": "5. 做循环题时，先想清楚：每一轮到底要做什么",
                "explanation": (
                    "初学循环时最容易慌，是因为一眼看过去感觉它会转很多圈。"
                    "这时候别急着想全局，先问自己：第 1 轮做什么？第 2 轮做什么？"
                    "当你把注意力放回“单独一轮会发生什么”时，循环往往会清楚很多。"
                    "如果每一轮的动作是清楚的，整个循环通常就不难写。"
                ),
                "example": (
                    "for i in range(1, 4):\n"
                    "    print(i * 2)"
                ),
            },
        ],
        "exercise": {
            "id": "for-range-loops-ex-01",
            "title": "计算 1 到 n 的总和",
            "expected_function": "sum_to_n",
            "description": (
                "请写一个函数 `sum_to_n(n)`，"
                "返回从 1 加到 `n` 的结果。"
                "比如传入 4，应该返回 `1 + 2 + 3 + 4 = 10`。"
            ),
            "requirements": [
                "函数名必须是 `sum_to_n`。",
                "函数接收一个参数 `n`。",
                "使用循环完成计算。",
                "返回从 1 加到 n 的总和。",
            ],
            "examples": [
                {"input": "sum_to_n(4)", "output": "10"},
                {"input": "sum_to_n(1)", "output": "1"},
            ],
            "hints": [
                "可以先准备一个变量 `total = 0`。",
                "再用 `for` 循环把每个数字加进去。",
                "注意 `range(1, n + 1)` 才能包含 n 本身。",
            ],
            "starter_code": (
                "def sum_to_n(n):\n"
                "    # TODO: 返回 1 到 n 的总和\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def sum_to_n(n):\n"
                "    total = 0\n"
                "    for i in range(1, n + 1):\n"
                "        total += i\n"
                "    return total\n"
            ),
            "hidden_tests": [
                {"call": "sum_to_n(1)", "expected": 1},
                {"call": "sum_to_n(4)", "expected": 10},
                {"call": "sum_to_n(5)", "expected": 15},
            ],
        },
    },
    {
        "id": "while-break-continue",
        "language": "python",
        "title": "while、break 与 continue",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4. More Control Flow Tools",
            "url": "https://docs.python.org/3/tutorial/controlflow.html",
            "authority": "Python Software Foundation / 菜鸟教程",
        },
        "summary": (
            "如果说 `for` 循环更像“把一组东西按顺序看一遍”，那么 `while` 更像“只要条件还成立，就继续做”。"
            "因此，`while` 特别适合那些“什么时候结束，要看过程本身”的场景。"
            "而 `break` 和 `continue`，则是在循环里进一步加入“提前停下”和“跳过这一轮”的能力。"
            "也正因为有了它们，循环不只是重复执行，还开始变得更灵活。"
        ),
        "knowledge_points": [
            {
                "title": "1. `while` 的核心是：条件成立，就继续循环",
                "explanation": (
                    "`while` 可以理解成“只要……就一直……”。"
                    "和 `for` 提前知道要循环多少次不同，`while` 更关注的是条件本身。"
                    "也就是说，只要条件还是 `True`，循环就会继续；而一旦条件变成 `False`，循环才会停下来。"
                    "因此，它特别适合拿来处理“做到某个条件满足为止”这类问题。"
                ),
                "example": (
                    "count = 1\n"
                    "while count <= 3:\n"
                    "    print(count)\n"
                    "    count += 1"
                ),
            },
            {
                "title": "2. 写 `while` 时，一定要想清楚条件什么时候会变化",
                "explanation": (
                    "很多初学者第一次写 `while`，最容易卡住的地方不是语法，而是忘了让条件发生变化。"
                    "比如你写了 `while count <= 3:`，却没有在循环里更新 `count`，程序就可能一直转下去。"
                    "所以，写 `while` 时最好同时想两件事：现在为什么会继续？等会儿又凭什么停下？"
                    "换句话说，循环条件和变量更新，通常要成对考虑。"
                ),
                "example": (
                    "count = 1\n"
                    "while count <= 3:\n"
                    "    print('当前是', count)\n"
                    "    count += 1"
                ),
            },
            {
                "title": "3. `break` 是提前结束整个循环",
                "explanation": (
                    "有时候你虽然写的是一个循环，但真正想要的并不是把所有轮次都跑完。"
                    "比如你在找列表里的第一个符合条件的元素，一旦找到了，其实就没必要继续往后看。"
                    "这时就可以用 `break` 提前跳出整个循环。"
                    "因此，`break` 的感觉更像是：任务已经完成了，现在可以直接停下。"
                ),
                "example": (
                    "num = 1\n"
                    "while num <= 5:\n"
                    "    if num == 3:\n"
                    "        break\n"
                    "    print(num)\n"
                    "    num += 1"
                ),
            },
            {
                "title": "4. `continue` 是跳过当前这一轮，直接进入下一轮",
                "explanation": (
                    "和 `break` 不同，`continue` 不是结束整个循环，而是跳过“这一轮剩下的代码”。"
                    "也就是说，这一轮不做了，但下一轮还会继续。"
                    "因此，它很适合那些“遇到某种情况就先略过”的场景，比如跳过偶数、跳过空字符串、跳过无效输入。"
                    "不过也要小心，`continue` 前后变量该更新的地方还是要更新，否则也可能写出死循环。"
                ),
                "example": (
                    "num = 0\n"
                    "while num < 5:\n"
                    "    num += 1\n"
                    "    if num == 3:\n"
                    "        continue\n"
                    "    print(num)"
                ),
            },
            {
                "title": "5. 学 `while` 时，先用“每一轮会发生什么”来理解",
                "explanation": (
                    "一看到循环，很多人会被“它会转很多圈”吓住。"
                    "但更有效的办法，往往是把注意力放回单独一轮：这一轮先检查什么？这一轮更新了什么？这一轮什么时候跳过、什么时候停止？"
                    "当单轮逻辑清楚了，整段 `while` 往往也就不乱了。"
                    "所以，别急着一眼看完整个循环，先把每一轮捋顺，通常更稳。"
                ),
                "example": (
                    "i = 1\n"
                    "while i <= 3:\n"
                    "    print('这一轮是', i)\n"
                    "    i += 1"
                ),
            },
        ],
        "exercise": {
            "id": "while-break-continue-ex-01",
            "title": "找到第一个大于 10 的数",
            "expected_function": "first_greater_than_ten",
            "description": (
                "请写一个函数 `first_greater_than_ten(nums)`，接收一个整数列表，"
                "返回列表中第一个大于 10 的数字。"
                "如果列表里没有大于 10 的数字，就返回 `-1`。"
                "这道题的重点是练习“从前往后找，找到就可以结束”的思路。"
            ),
            "requirements": [
                "函数名必须是 `first_greater_than_ten`。",
                "函数接收一个参数 `nums`。",
                "找到第一个大于 10 的数时，返回这个数。",
                "如果不存在这样的数，返回 `-1`。",
            ],
            "examples": [
                {"input": "first_greater_than_ten([3, 8, 12, 5])", "output": "12"},
                {"input": "first_greater_than_ten([1, 2, 3])", "output": "-1"},
            ],
            "hints": [
                "可以从列表开头开始，一个个检查。",
                "一旦找到符合条件的值，就可以直接 `return`。",
                "如果走完整个列表都没找到，最后返回 `-1`。",
            ],
            "starter_code": (
                "def first_greater_than_ten(nums):\n"
                "    # TODO: 返回第一个大于 10 的数字；如果没有则返回 -1\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def first_greater_than_ten(nums):\n"
                "    i = 0\n"
                "    while i < len(nums):\n"
                "        if nums[i] > 10:\n"
                "            return nums[i]\n"
                "        i += 1\n"
                "    return -1\n"
            ),
            "hidden_tests": [
                {"call": "first_greater_than_ten([3, 8, 12, 5])", "expected": 12},
                {"call": "first_greater_than_ten([11, 2, 30])", "expected": 11},
                {"call": "first_greater_than_ten([1, 2, 3])", "expected": -1},
            ],
        },
    },
    {
        "id": "match-statements",
        "language": "python",
        "title": "match 模式匹配入门",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4.7 match Statements",
            "url": "https://docs.python.org/3/tutorial/controlflow.html#match-statements",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "`match` 可以先粗略地理解成一种更整齐的“多分支判断”。"
            "不过，它并不只是把很多个 `if` 堆在一起，而是通过 `case` 去匹配不同模式。"
            "因此，当你面对的是“同一个值有好几种明确情况”的问题时，`match` 常常会写得更清楚。"
            "当然，这一节先不追求花哨，只先掌握最基础、最常见的用法。"
        ),
        "knowledge_points": [
            {
                "title": "1. `match` 适合处理“同一个对象有多种固定情况”",
                "explanation": (
                    "如果你要判断一个状态码、一个菜单选项，或者一个星期几的编号分别代表什么，"
                    "那么你面对的往往是“同一个输入，可能落在多个固定分支里”。"
                    "这时，`match` 会比一长串 `if ... elif ...` 看起来更整齐。"
                    "也就是说，它特别适合那种“选一种情况来处理”的场景。"
                ),
                "example": (
                    "def http_error(status):\n"
                    "    match status:\n"
                    "        case 404:\n"
                    "            return 'Not found'\n"
                    "        case 500:\n"
                    "            return 'Server error'"
                ),
            },
            {
                "title": "2. `case` 就是在列出不同匹配情况",
                "explanation": (
                    "写 `match` 时，后面跟的是要检查的值；而每个 `case` 则是在列出一种可能匹配到的情况。"
                    "一旦某个 `case` 匹配成功，对应代码就会执行。"
                    "进一步说，`match` 并不是把所有分支都跑一遍，而是只会进入第一个匹配成功的分支。"
                    "因此，分支的顺序也值得留意。"
                ),
                "example": (
                    "day = 2\n"
                    "match day:\n"
                    "    case 1:\n"
                    "        print('周一')\n"
                    "    case 2:\n"
                    "        print('周二')"
                ),
            },
            {
                "title": "3. `_` 常常用来表示“其他情况”",
                "explanation": (
                    "在很多判断里，你很难把所有情况都列完。"
                    "因此，`match` 里经常会放一个 `case _:`，用来兜底处理前面没有匹配到的情况。"
                    "可以把它理解成“如果以上都不是，那就走这里”。"
                    "也正因为这个兜底分支很通用，所以它通常会写在最后。"
                ),
                "example": (
                    "match status:\n"
                    "    case 200:\n"
                    "        print('成功')\n"
                    "    case _:\n"
                    "        print('其他状态')"
                ),
            },
            {
                "title": "4. `match` 不是一定比 `if` 高级，而是有时更顺手",
                "explanation": (
                    "初学者很容易误以为：学了新语法，就应该处处都用。"
                    "其实不一定。"
                    "如果只是简单判断一个条件，`if` 往往更直接；而如果是同一个值对应好几种明确情况，`match` 会更整齐。"
                    "所以，关键不是追求新，而是看哪种写法更适合当前问题。"
                ),
                "example": (
                    "command = 'start'\n"
                    "match command:\n"
                    "    case 'start':\n"
                    "        print('启动')\n"
                    "    case 'stop':\n"
                    "        print('停止')"
                ),
            },
            {
                "title": "5. 刚开始学 `match`，先掌握字面量匹配和兜底就够了",
                "explanation": (
                    "Python 的 `match` 其实还支持更丰富的模式匹配。"
                    "不过，入门阶段没必要一上来就把所有花样都背下来。"
                    "先把最实用的两件事练熟：用 `case` 匹配固定值，以及用 `_` 处理其他情况。"
                    "这样一来，你已经能解决很多基础分支题了，后面再慢慢往复杂模式扩展会更自然。"
                ),
                "example": (
                    "match level:\n"
                    "    case 'easy':\n"
                    "        print('简单模式')\n"
                    "    case _:\n"
                    "        print('默认模式')"
                ),
            },
        ],
        "exercise": {
            "id": "match-statements-ex-01",
            "title": "根据数字返回星期",
            "expected_function": "weekday_name",
            "description": (
                "请写一个函数 `weekday_name(day)`。"
                "如果传入 1，返回 `周一`；传入 2，返回 `周二`；传入 3，返回 `周三`。"
                "如果传入的不是 1、2、3 之一，就返回 `未知`。"
            ),
            "requirements": [
                "函数名必须是 `weekday_name`。",
                "函数接收一个参数 `day`。",
                "1 返回 `周一`，2 返回 `周二`，3 返回 `周三`。",
                "其他情况返回 `未知`。",
            ],
            "examples": [
                {"input": "weekday_name(1)", "output": "周一"},
                {"input": "weekday_name(4)", "output": "未知"},
            ],
            "hints": [
                "可以使用 `match day:` 开始。",
                "记得用 `case _:` 处理其他情况。",
            ],
            "starter_code": (
                "def weekday_name(day):\n"
                "    # TODO: 根据 day 返回对应的星期名称\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def weekday_name(day):\n"
                "    match day:\n"
                "        case 1:\n"
                "            return '周一'\n"
                "        case 2:\n"
                "            return '周二'\n"
                "        case 3:\n"
                "            return '周三'\n"
                "        case _:\n"
                "            return '未知'\n"
            ),
            "hidden_tests": [
                {"call": "weekday_name(1)", "expected": "周一"},
                {"call": "weekday_name(2)", "expected": "周二"},
                {"call": "weekday_name(5)", "expected": "未知"},
            ],
        },
    },
    {
        "id": "function-arguments",
        "language": "python",
        "title": "参数默认值与关键字参数",
        "topic": "python_basics",
        "difficulty": "intermediate",
        "source": {
            "title": "Python 官方教程 4.9.1 / 4.9.2 More on Defining Functions",
            "url": "https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "学完函数基础以后，下一步自然会遇到一个问题：函数能不能写得更灵活一点？"
            "答案是可以。"
            "默认参数让你在很多场景下不用每次都把所有值写全；而关键字参数则让函数调用更清楚。"
            "因此，这一节本质上是在帮你从“会定义函数”，走向“会把函数设计得更顺手”。"
        ),
        "knowledge_points": [
            {
                "title": "1. 默认参数值让函数在省略某些参数时也能工作",
                "explanation": (
                    "有些函数虽然能接收多个参数，但其中一部分值在多数情况下其实是固定的。"
                    "这时，把它们写成默认参数会很方便。"
                    "也就是说，调用函数时你可以只传最关键的参数，其他参数就先使用默认值。"
                    "因此，默认参数的意义不只是少打几个字，更是在表达“这个值通常就这样”。"
                ),
                "example": (
                    "def greet(name, prefix='Hello'):\n"
                    "    return f'{prefix}, {name}!'\n\n"
                    "print(greet('Alice'))\n"
                    "print(greet('Bob', 'Hi'))"
                ),
            },
            {
                "title": "2. 有默认值，不代表参数就不重要",
                "explanation": (
                    "很多初学者看到默认参数后，会误以为它只是“可有可无”。"
                    "其实更准确地说，它是在告诉别人：如果你不特别说明，我就按这个常用值来处理。"
                    "因此，默认值依然是函数设计的一部分。"
                    "你给什么默认值，往往也在表达这个函数最常见的使用方式。"
                ),
                "example": (
                    "def power(base, exponent=2):\n"
                    "    return base ** exponent\n\n"
                    "print(power(3))\n"
                    "print(power(3, 3))"
                ),
            },
            {
                "title": "3. 关键字参数能让调用时更清楚“这个值是给谁的”",
                "explanation": (
                    "当函数参数多起来时，只靠位置去传值，读起来就容易混。"
                    "这时，关键字参数会更清楚，因为你会明确写出参数名。"
                    "例如 `greet(name='Alice', prefix='Hi')`，别人一眼就知道哪个值对应哪个参数。"
                    "因此，关键字参数的最大价值，往往是提高可读性。"
                ),
                "example": (
                    "def greet(name, prefix='Hello'):\n"
                    "    return f'{prefix}, {name}!'\n\n"
                    "print(greet(name='Alice'))\n"
                    "print(greet(name='Bob', prefix='Hi'))"
                ),
            },
            {
                "title": "4. 位置参数和关键字参数可以一起用，但顺序有规则",
                "explanation": (
                    "Python 允许你在一次调用里混合使用位置参数和关键字参数。"
                    "不过要注意，位置参数通常要写在前面，关键字参数写在后面。"
                    "进一步说，同一个参数也不能被赋值两次，否则程序就会报错。"
                    "所以这一部分虽然不难，但很值得在调用时多看一眼写法是否清楚。"
                ),
                "example": (
                    "def describe(name, city='上海'):\n"
                    "    return f'{name} 来自 {city}'\n\n"
                    "print(describe('小明'))\n"
                    "print(describe('小红', city='杭州'))"
                ),
            },
            {
                "title": "5. 学参数进阶时，重点是体会“函数接口”这件事",
                "explanation": (
                    "函数不只是把代码包起来，它其实也在对外暴露一种使用方式。"
                    "调用者要传什么，哪些值常用，哪些值可以省略，哪些值写成关键字更清楚，这些都属于函数接口的一部分。"
                    "因此，这一节并不只是多学两个语法点，而是在开始接触“怎样让函数更好用”这个更成熟的问题。"
                ),
                "example": (
                    "def make_message(name, prefix='Hello', suffix='!'):\n"
                    "    return f'{prefix}, {name}{suffix}'\n\n"
                    "print(make_message('Alice'))"
                ),
            },
        ],
        "exercise": {
            "id": "function-arguments-ex-01",
            "title": "带默认参数的问候函数",
            "expected_function": "welcome",
            "description": (
                "请写一个函数 `welcome(name, prefix='Hello')`，"
                "返回形如 `Hello, Alice!` 的字符串。"
                "如果传入了新的 `prefix`，就用新的前缀。"
            ),
            "requirements": [
                "函数名必须是 `welcome`。",
                "第一个参数是 `name`。",
                "第二个参数是 `prefix`，默认值为 `Hello`。",
                "返回值必须是完整字符串。",
            ],
            "examples": [
                {"input": "welcome('Alice')", "output": "Hello, Alice!"},
                {"input": "welcome('Bob', 'Hi')", "output": "Hi, Bob!"},
            ],
            "hints": [
                "函数头可以写成 `def welcome(name, prefix='Hello'):`。",
                "可以用 f-string 返回结果。",
            ],
            "starter_code": (
                "def welcome(name, prefix='Hello'):\n"
                "    # TODO: 返回带前缀的欢迎语\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def welcome(name, prefix='Hello'):\n"
                "    return f\"{prefix}, {name}!\"\n"
            ),
            "hidden_tests": [
                {"call": "welcome('Alice')", "expected": "Hello, Alice!"},
                {"call": "welcome('Bob', 'Hi')", "expected": "Hi, Bob!"},
                {"call": "welcome('Python', 'Welcome')", "expected": "Welcome, Python!"},
            ],
        },
    },
    {
        "id": "lambda-docstring-annotations",
        "language": "python",
        "title": "lambda、文档字符串与类型标注",
        "topic": "python_basics",
        "difficulty": "intermediate",
        "source": {
            "title": "Python 官方教程 4.8 / 4.9 / 4.10 / 4.11",
            "url": "https://docs.python.org/3/tutorial/controlflow.html",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "学到这里，你已经知道函数能做什么；接下来更值得思考的是，怎样让函数更简洁、也更容易被别人读懂。"
            "`lambda` 会让你接触“很短的小函数”；文档字符串会提醒你“代码要能解释自己”；"
            "而类型标注则是在帮助你把参数和返回值的意图写得更清楚。"
            "因此，这一节虽然带一点工程味，但其实依然是在服务于“让代码更好理解”。"
        ),
        "knowledge_points": [
            {
                "title": "1. `lambda` 适合写很短、很轻的小函数",
                "explanation": (
                    "`lambda` 可以先理解成“用一行写的小函数”。"
                    "它并不是为了取代普通函数，而是适合那些逻辑非常短、名字也不一定非要单独起一个的场景。"
                    "因此，学 `lambda` 时最重要的不是把所有函数都改写成它，而是知道：当逻辑真的很短时，还有这种更紧凑的表达方式。"
                ),
                "example": (
                    "double = lambda x: x * 2\n"
                    "print(double(5))"
                ),
            },
            {
                "title": "2. 如果逻辑开始变复杂，普通 `def` 往往更清楚",
                "explanation": (
                    "很多初学者学到 `lambda` 后，会忍不住到处都想用。"
                    "不过，`lambda` 的优势恰恰在于“短”。"
                    "一旦逻辑变复杂、需要多步处理，普通函数通常会更容易读，也更容易改。"
                    "所以，`lambda` 并不代表更高级，它只是更适合某些特别轻的小场景。"
                ),
                "example": (
                    "def double(x):\n"
                    "    return x * 2\n\n"
                    "print(double(5))"
                ),
            },
            {
                "title": "3. 文档字符串是在函数开头写给人看的说明",
                "explanation": (
                    "文档字符串，通常就是函数体开头那一段三引号字符串。"
                    "它的作用很朴素：告诉别人这个函数是干什么的、参数是什么、会返回什么。"
                    "也正因为如此，它特别适合那些你希望以后还能快速看懂、或者别人也可能会调用的函数。"
                    "换句话说，文档字符串是在帮代码自己开口说话。"
                ),
                "example": (
                    "def add(a, b):\n"
                    "    \"\"\"返回两个数字的和。\"\"\"\n"
                    "    return a + b"
                ),
            },
            {
                "title": "4. 类型标注是在表达“我希望这里接收什么、返回什么”",
                "explanation": (
                    "类型标注不会自动改变程序的运行结果，但它会让函数接口更清楚。"
                    "例如 `def add(a: int, b: int) -> int:`，就是在告诉读代码的人："
                    "我期待这里接收整数，并返回整数。"
                    "因此，类型标注的价值主要在于沟通和可读性，而不是把 Python 变成另一门语言。"
                ),
                "example": (
                    "def add(a: int, b: int) -> int:\n"
                    "    return a + b"
                ),
            },
            {
                "title": "5. 这一节的重点，是让函数“更容易被理解”",
                "explanation": (
                    "把这几个点放在一起看，你会发现它们都在服务同一个目标：让代码更好理解。"
                    "`lambda` 帮你在短场景里更简洁；文档字符串帮你把用途说明白；类型标注帮你把接口写清楚。"
                    "因此，别把它们当成零散知识点，它们其实都在训练你写出更友好的函数。"
                ),
                "example": (
                    "def greet(name: str) -> str:\n"
                    "    \"\"\"返回一条问候语。\"\"\"\n"
                    "    return f'Hello, {name}!'"
                ),
            },
        ],
        "exercise": {
            "id": "lambda-docstring-annotations-ex-01",
            "title": "写一个带类型标注的平方函数",
            "expected_function": "square",
            "description": (
                "请写一个函数 `square(n: int) -> int`，返回 `n` 的平方。"
                "另外，请给这个函数加上一句简短文档字符串，说明它的作用。"
            ),
            "requirements": [
                "函数名必须是 `square`。",
                "函数接收一个参数 `n`。",
                "返回值必须是 `n * n`。",
                "请为函数写一句文档字符串。",
            ],
            "examples": [
                {"input": "square(3)", "output": "9"},
                {"input": "square(5)", "output": "25"},
            ],
            "hints": [
                "函数头可以写成 `def square(n: int) -> int:`。",
                "文档字符串通常写在函数体开头。",
                "返回平方可以直接写成 `return n * n`。",
            ],
            "starter_code": (
                "def square(n: int) -> int:\n"
                "    \"\"\"TODO: 补充这个函数的说明。\"\"\"\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def square(n: int) -> int:\n"
                "    \"\"\"返回整数 n 的平方。\"\"\"\n"
                "    return n * n\n"
            ),
            "hidden_tests": [
                {"call": "square(3)", "expected": 9},
                {"call": "square(5)", "expected": 25},
                {"call": "square(0)", "expected": 0},
            ],
        },
    },
    {
        "id": "python-functions-basics",
        "language": "python",
        "title": "函数定义基础",
        "topic": "python_basics",
        "difficulty": "beginner",
        "source": {
            "title": "Python 官方教程 4.8 Defining Functions",
            "url": "https://docs.python.org/3.12/tutorial/controlflow.html#defining-functions",
            "authority": "Python Software Foundation",
        },
        "summary": (
            "这一节先解决一个最常见的问题：同一段逻辑以后还要用很多次，怎么办？"
            "Python 里的函数就是为这件事准备的。"
            "我们把一段代码整理成一个有名字的小步骤，以后需要时只调用这个名字，"
            "代码会更短，也更容易检查和修改。"
        ),
        "knowledge_points": [
            {
                "title": "1. 先知道为什么需要函数",
                "explanation": (
                    "先不用急着背语法。可以先把函数想成一个“可重复使用的小步骤”。"
                    "比如生成问候语这件事，本质上每次都差不多：拿到一个名字，拼成一句话。"
                    "如果每次都重新写一遍，代码会越来越散；"
                    "把它放进函数里，就像给这件事贴了一个清楚的标签。"
                ),
                "example": (
                    "# 这是一次性的写法：能用，但下次还得再写一遍\n"
                    "name = 'Alice'\n"
                    "message = f\"Hello, {name}!\"\n"
                    "print(message)"
                ),
            },
            {
                "title": "2. 用 def 给这段逻辑起名字",
                "explanation": (
                    "在 Python 里，定义函数从 `def` 开始。"
                    "`greet` 是函数名，表示这个函数负责“问候”；"
                    "括号里的 `name` 是它需要的材料；"
                    "冒号后面换行并缩进，缩进里面的代码就是这个函数真正要做的事。"
                    "你可以把这一行读成：定义一个叫 greet 的函数，它需要一个 name。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    # 根据传进来的 name 生成一句问候语\n"
                    "    return f\"Hello, {name}!\""
                ),
            },
            {
                "title": "3. 参数让函数可以处理不同情况",
                "explanation": (
                    "如果函数里把名字写死成 Alice，那它只能问候 Alice。"
                    "参数的作用，就是把这个固定值变成一个可以变化的位置。"
                    "调用函数时传入 Alice，`name` 就临时代表 Alice；"
                    "传入 Bob，`name` 就临时代表 Bob。"
                    "同一个函数因此可以服务很多不同输入。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    return f\"Hello, {name}!\"\n\n"
                    "# 同一个函数，换一个参数，就得到不同结果\n"
                    "greet('Alice')  # Hello, Alice!\n"
                    "greet('Bob')    # Hello, Bob!"
                ),
            },
            {
                "title": "4. return 表示“把结果交出去”",
                "explanation": (
                    "`return` 不是为了把内容显示在屏幕上，"
                    "而是把函数算出的结果交回给调用它的地方。"
                    "这样外面的代码才能继续保存这个结果、比较这个结果，或者把它传给下一步使用。"
                    "所以题目里写“返回”，通常就要用 `return`；"
                    "只用 `print` 只是让人看见了结果，程序本身并没有拿到它。"
                ),
                "example": (
                    "def double(n):\n"
                    "    return n * 2\n\n"
                    "# double(5) 的结果被交给 result，后面还能继续使用\n"
                    "result = double(5)\n"
                    "print(result)  # 10"
                ),
            },
            {
                "title": "5. 做题时按这个顺序检查",
                "explanation": (
                    "刚开始写函数，出错很正常，不用慌。"
                    "可以按一个固定顺序检查：函数名是不是题目要求的名字，"
                    "参数有没有写，函数体有没有缩进，最后有没有用 `return` 返回结果。"
                    "这几个点对了，大多数基础函数题就已经走在正确方向上了。"
                ),
                "example": (
                    "def greet(name):\n"
                    "    print(f\"Hello, {name}!\")\n\n"
                    "# 这段代码能在屏幕上显示内容\n"
                    "# 但函数没有 return，所以返回值其实是 None\n"
                    "# 如果题目要求“返回字符串”，这里就应该改成 return"
                ),
            },
        ],
        "exercise": {
            "id": "python-functions-basics-ex-01",
            "title": "实现一个问候函数",
            "expected_function": "greet",
            "description": (
                "现在把上面的思路合起来用一次。"
                "请写一个叫 `greet` 的函数，它接收一个名字 `name`，"
                "然后把问候语作为结果返回。"
                "比如传入 `Alice`，函数应该返回 `Hello, Alice!`。"
            ),
            "requirements": [
                "函数名必须是 `greet`。",
                "函数必须接收一个参数 `name`。",
                "返回值必须是字符串，而不是使用 `print` 输出。",
                "传入 `Alice` 时应返回 `Hello, Alice!`。",
            ],
            "examples": [
                {"input": "greet('Alice')", "output": "Hello, Alice!"},
                {"input": "greet('Bob')", "output": "Hello, Bob!"},
            ],
            "hints": [
                "第一步先写函数头：`def greet(name):`。",
                "第二步在函数体里缩进一层，写出要返回的问候语。",
                "题目要的是“返回结果”，所以这里应该用 `return`，不要只写 `print`。",
                "如果你会 f-string，可以写成：`return f\"Hello, {name}!\"`。",
            ],
            "starter_code": (
                "def greet(name):\n"
                "    # TODO: 返回形如 Hello, Alice! 的字符串\n"
                "    pass\n"
            ),
            "reference_answer": (
                "def greet(name):\n"
                "    return f\"Hello, {name}!\"\n"
            ),
            "hidden_tests": [
                {"call": "greet('Alice')", "expected": "Hello, Alice!"},
                {"call": "greet('Python')", "expected": "Hello, Python!"},
                {"call": "greet('张三')", "expected": "Hello, 张三!"},
            ],
        },
    }
]


CURRICULUM_CHAPTERS: List[Dict[str, Any]] = [
    {
        "id": "getting-started",
        "order": 1,
        "title": "第一章：Python 起步",
        "description": "先建立运行 Python 程序的基本感觉，知道代码在哪里写、怎样运行、怎样看到结果。",
        "source": {
            "title": "Python 官方教程 2. Using the Python Interpreter",
            "url": "https://docs.python.org/3/tutorial/interpreter.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "python-interpreter",
                "title": "解释器与交互模式",
                "summary": "认识 Python 解释器、命令行运行和交互式尝试代码。",
                "status": "planned",
                "estimated_minutes": 12,
            },
            {
                "id": "python-script-basics",
                "title": "脚本文件与第一段程序",
                "summary": "从一行 print 开始，理解 .py 文件、执行入口和基本输出。",
                "status": "planned",
                "estimated_minutes": 15,
            },
        ],
    },
    {
        "id": "basic-types",
        "order": 2,
        "title": "第二章：基础语法与内置类型",
        "description": "把变量、数字、字符串、列表这些最常用材料先用顺手。",
        "source": {
            "title": "Python 官方教程 3. An Informal Introduction to Python",
            "url": "https://docs.python.org/3/tutorial/introduction.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "numbers-and-variables",
                "title": "数字、变量与表达式",
                "summary": "理解赋值、算术表达式和简单计算。",
                "status": "planned",
                "estimated_minutes": 18,
            },
            {
                "id": "strings-basics",
                "title": "字符串基础",
                "summary": "学习字符串字面量、拼接、索引、切片和格式化的最小用法。",
                "status": "planned",
                "estimated_minutes": 25,
            },
            {
                "id": "lists-basics",
                "title": "列表基础",
                "summary": "认识列表、索引、切片、追加元素和遍历前的准备。",
                "status": "planned",
                "estimated_minutes": 25,
            },
        ],
    },
    {
        "id": "control-flow",
        "order": 3,
        "title": "第三章：控制流程",
        "description": "让程序不再只从上到下机械执行，而是能判断、重复、分支。",
        "source": {
            "title": "Python 官方教程 4. More Control Flow Tools",
            "url": "https://docs.python.org/3/tutorial/controlflow.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "if-statements",
                "title": "if 条件判断",
                "summary": "根据条件选择不同代码路径，建立分支思维。",
                "status": "planned",
                "estimated_minutes": 20,
            },
            {
                "id": "for-range-loops",
                "title": "for 循环与 range",
                "summary": "学习重复处理一组数据，以及用 range 生成循环次数。",
                "status": "planned",
                "estimated_minutes": 25,
            },
            {
                "id": "while-break-continue",
                "title": "while、break 与 continue",
                "summary": "处理条件循环、中途停止和跳过本轮循环。",
                "status": "planned",
                "estimated_minutes": 25,
            },
            {
                "id": "match-statements",
                "title": "match 模式匹配入门",
                "summary": "认识 Python 较新的结构化分支写法，先掌握最常见场景。",
                "status": "planned",
                "estimated_minutes": 20,
            },
        ],
    },
    {
        "id": "functions",
        "order": 4,
        "title": "第四章：函数",
        "description": "把一段逻辑封装成可以重复调用的小工具，是从写代码到组织代码的关键一步。",
        "source": {
            "title": "Python 官方教程 4.8 Defining Functions",
            "url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "python-functions-basics",
                "lesson_id": "python-functions-basics",
                "title": "函数定义基础",
                "summary": "学习 def、参数、缩进、return，并完成一个基础函数题。",
                "status": "ready",
                "estimated_minutes": 30,
            },
            {
                "id": "function-arguments",
                "title": "参数默认值与关键字参数",
                "summary": "理解默认参数、关键字参数和调用函数时的参数匹配。",
                "status": "planned",
                "estimated_minutes": 35,
            },
            {
                "id": "lambda-docstring-annotations",
                "title": "lambda、文档字符串与类型标注",
                "summary": "先认识函数周边的常用写法，为读懂真实项目代码做准备。",
                "status": "planned",
                "estimated_minutes": 30,
            },
        ],
    },
    {
        "id": "data-structures",
        "order": 5,
        "title": "第五章：数据结构",
        "description": "系统整理列表、元组、集合、字典，以及在循环中使用它们的方式。",
        "source": {
            "title": "Python 官方教程 5. Data Structures",
            "url": "https://docs.python.org/3/tutorial/datastructures.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "list-methods",
                "title": "列表方法与栈/队列思想",
                "summary": "掌握 append、pop、sort 等常用方法，并理解列表能模拟哪些结构。",
                "status": "planned",
                "estimated_minutes": 35,
            },
            {
                "id": "tuples-sets-dicts",
                "title": "元组、集合与字典",
                "summary": "区分几种容器的特点，知道什么时候该用哪一种。",
                "status": "planned",
                "estimated_minutes": 40,
            },
            {
                "id": "looping-techniques",
                "title": "数据遍历技巧",
                "summary": "学习 enumerate、zip、items 等更清爽的循环写法。",
                "status": "planned",
                "estimated_minutes": 30,
            },
            {
                "id": "comprehensions",
                "title": "列表推导式与生成式思维",
                "summary": "用更简洁的方式从已有数据构造新数据。",
                "status": "planned",
                "estimated_minutes": 30,
            },
        ],
    },
    {
        "id": "modules-io-exceptions",
        "order": 6,
        "title": "第六章：模块、输入输出与异常",
        "description": "开始把代码放进多个文件，读取外部数据，并处理程序可能出错的情况。",
        "source": {
            "title": "Python 官方教程 6-8 Modules, Input and Output, Errors and Exceptions",
            "url": "https://docs.python.org/3/tutorial/modules.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "modules-imports",
                "title": "模块与 import",
                "summary": "理解模块、导入、命名空间和脚本复用。",
                "status": "planned",
                "estimated_minutes": 35,
            },
            {
                "id": "packages-basics",
                "title": "包结构基础",
                "summary": "认识包、目录结构和 __init__.py 的基本作用。",
                "status": "planned",
                "estimated_minutes": 30,
            },
            {
                "id": "formatting-files-json",
                "title": "格式化输出、文件与 JSON",
                "summary": "学习 f-string、文件读写和 JSON 数据保存。",
                "status": "planned",
                "estimated_minutes": 45,
            },
            {
                "id": "exceptions-basics",
                "title": "异常处理基础",
                "summary": "理解 try/except、raise、finally，以及为什么不能吞掉所有错误。",
                "status": "planned",
                "estimated_minutes": 40,
            },
        ],
    },
    {
        "id": "oop",
        "order": 7,
        "title": "第七章：面向对象",
        "description": "从函数进一步走向对象，把数据和行为组织到类里。",
        "source": {
            "title": "Python 官方教程 9. Classes",
            "url": "https://docs.python.org/3/tutorial/classes.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "classes-objects",
                "title": "类与对象",
                "summary": "认识 class、实例、属性和方法。",
                "status": "planned",
                "estimated_minutes": 40,
            },
            {
                "id": "inheritance",
                "title": "继承与方法重写",
                "summary": "理解子类复用父类能力，以及重写行为的基本方式。",
                "status": "planned",
                "estimated_minutes": 35,
            },
            {
                "id": "iterators-generators",
                "title": "迭代器与生成器",
                "summary": "理解 for 背后的迭代协议，以及 yield 的基础用法。",
                "status": "planned",
                "estimated_minutes": 45,
            },
        ],
    },
    {
        "id": "standard-library",
        "order": 8,
        "title": "第八章：标准库与工程化入门",
        "description": "学习常用标准库、虚拟环境和包管理，让代码更接近真实项目。",
        "source": {
            "title": "Python 官方教程 10-12 Standard Library, Virtual Environments and Packages",
            "url": "https://docs.python.org/3/tutorial/stdlib.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            {
                "id": "stdlib-everyday",
                "title": "常用标准库巡礼",
                "summary": "了解 os、pathlib、datetime、random、statistics 等常见工具。",
                "status": "planned",
                "estimated_minutes": 45,
            },
            {
                "id": "venv-pip",
                "title": "虚拟环境与 pip",
                "summary": "理解项目依赖隔离，学会创建 venv 和安装包。",
                "status": "planned",
                "estimated_minutes": 30,
            },
            {
                "id": "testing-debugging-style",
                "title": "测试、调试与代码风格",
                "summary": "建立写完代码后检查、调试和整理风格的习惯。",
                "status": "planned",
                "estimated_minutes": 45,
            },
        ],
    },
]


def _planned_section(
    section_id: str,
    title: str,
    summary: str,
    estimated_minutes: int,
) -> Dict[str, Any]:
    return {
        "id": section_id,
        "title": title,
        "summary": summary,
        "status": "planned",
        "estimated_minutes": estimated_minutes,
    }


def _ready_section(
    section_id: str,
    title: str,
    summary: str,
    estimated_minutes: int,
) -> Dict[str, Any]:
    """Create a section that links to an actual lesson."""
    return {
        "id": section_id,
        "title": title,
        "summary": summary,
        "status": "ready",
        "estimated_minutes": estimated_minutes,
        "lesson_id": section_id,
    }


def _merge_sections(chapter: Dict[str, Any], sections: List[Dict[str, Any]], prepend: bool = False) -> None:
    existed = {section["id"] for section in chapter.get("sections", [])}
    fresh = [section for section in sections if section["id"] not in existed]
    if prepend:
        chapter["sections"] = fresh + chapter.get("sections", [])
    else:
        chapter.setdefault("sections", []).extend(fresh)


def _enrich_beginner_curriculum() -> None:
    """Expand the outline into a fuller zero-to-basic Python path."""
    setup_chapter = {
        "id": "environment-setup",
        "order": 1,
        "title": "第一章：安装环境与学习准备",
        "description": "先把 Python 装好、编辑器配好、终端会用起来。零基础用户从这里开始最稳。",
        "source": {
            "title": "Python 官方文档 Setup and Usage",
            "url": "https://docs.python.org/3/using/index.html",
            "authority": "Python Software Foundation",
        },
        "sections": [
            _ready_section("what-is-python", "Python 是什么，适合做什么", "理解 Python 的用途、解释型语言特点，以及它能解决哪些常见问题。", 12),
            _ready_section("install-python-windows", "Windows 安装 Python", "下载官方安装包，勾选 PATH，验证 python --version 是否可用。", 20),
            _ready_section("install-python-macos-linux", "macOS / Linux 环境说明", "了解 python3 命令、系统自带版本、包管理器安装和版本确认。", 18),
            _ready_section("terminal-basics", "终端与命令行最小必备", "会打开终端、切换目录、运行命令，知道错误信息从哪里看。", 25),
            _ready_section("vscode-python-extension", "VS Code 与 Python 插件配置", "安装 VS Code、Python 扩展，选择解释器，运行当前文件。", 25),
            _ready_section("first-python-file", "第一个 .py 文件", "创建 hello.py，写 print，保存并运行，建立写代码-运行-看结果的闭环。", 20),
        ],
    }

    chapter_map = {chapter["id"]: chapter for chapter in CURRICULUM_CHAPTERS}
    if "environment-setup" not in chapter_map:
        CURRICULUM_CHAPTERS.insert(0, setup_chapter)

    chapter_map = {chapter["id"]: chapter for chapter in CURRICULUM_CHAPTERS}

    first_steps = chapter_map.get("getting-started")
    if first_steps:
        first_steps["order"] = 2
        first_steps["title"] = "第二章：Python 入门第一步"
        first_steps["description"] = "用非常小的例子理解交互模式、脚本文件、注释和最基本的输入输出。"
        _merge_sections(
            first_steps,
            [
                _planned_section("print-and-comments", "print 输出与注释", "学习 print 的基础用法、单行注释，以及如何给代码留下解释。", 20),
                _planned_section("input-basics", "input 输入", "接收用户输入，理解 input 得到的是字符串，以及简单交互程序怎么写。", 20),
                _planned_section("read-error-message", "学会读最常见报错", "先认识 SyntaxError、NameError、IndentationError，不慌张地定位错误行。", 25),
            ],
        )

    basic_types = chapter_map.get("basic-types")
    if basic_types:
        basic_types["order"] = 3
        basic_types["title"] = "第三章：基础语法、变量与常见类型"
        basic_types["description"] = "打牢所有后续内容都会用到的语法地基：变量、缩进、运算符、数字和字符串。"
        basic_types["source"] = {
            "title": "菜鸟教程 Python3 基础语法 / Python 官方教程 3",
            "url": "https://www.runoob.com/python3/python3-basic-syntax.html",
            "authority": "Runoob / Python Software Foundation",
        }
        _merge_sections(
            basic_types,
            [
                _planned_section("indentation-rules", "缩进规则与代码块", "理解 Python 为什么不用大括号，而是用缩进表达代码层级。", 25),
                _planned_section("variables-assignment", "变量与赋值", "学习变量命名、赋值、重新赋值，以及变量只是名字不是盒子的直觉。", 25),
                _planned_section("operators", "算术、比较与逻辑运算符", "掌握 + - * /、比较大小、and/or/not，能写出简单条件表达式。", 30),
                _planned_section("type-conversion", "类型转换", "学习 int()、float()、str()，解决 input 读入数字后不能直接计算的问题。", 25),
                _planned_section("string-index-slice", "字符串索引与切片", "用下标取字符，用切片截取一段文本，理解从 0 开始计数。", 30),
                _planned_section("string-methods", "常用字符串方法", "掌握 strip、split、join、replace、lower、upper 等高频方法。", 35),
                _planned_section("f-strings-formatting", "f-string 格式化输出", "把变量自然地嵌入字符串，写出清楚的输出文本。", 25),
                _planned_section("naming-and-style", "命名习惯与代码可读性", "学习变量名要表达含义，初步理解 snake_case 和简单代码风格。", 18),
            ],
            prepend=True,
        )

    control_flow = chapter_map.get("control-flow")
    if control_flow:
        control_flow["order"] = 4
        control_flow["title"] = "第四章：条件判断与循环"
        _merge_sections(
            control_flow,
            [
                _planned_section("nested-if", "嵌套判断与条件整理", "理解判断里再判断，并学习把复杂条件拆开写清楚。", 25),
                _planned_section("range-basics", "range 的用法", "用 range 控制循环次数，理解起点、终点和步长。", 25),
                _planned_section("loop-exercises-patterns", "循环题常见套路", "总结计数、累加、最大最小值、条件筛选这几类基础循环题。", 35),
            ],
        )

    data_structures = chapter_map.get("data-structures")
    if data_structures:
        data_structures["order"] = 5
        data_structures["title"] = "第五章：列表、元组、字典与集合"
        _merge_sections(
            data_structures,
            [
                _planned_section("list-basics", "列表基础", "创建列表、访问元素、修改元素、追加和删除元素。", 35),
                _planned_section("list-slicing", "列表索引、切片与遍历", "用索引定位元素，用切片截取子列表，用 for 逐个处理。", 30),
                _planned_section("tuple-basics", "元组基础", "理解不可变序列，知道什么时候返回多个值可以用元组表达。", 22),
                _planned_section("dict-basics", "字典基础", "用键值对保存数据，学习读取、更新、删除和判断键是否存在。", 40),
                _planned_section("dict-looping", "字典遍历", "学习 keys、values、items，写出统计词频、查询信息等基础题。", 35),
                _planned_section("set-basics", "集合基础", "理解去重、成员判断，以及交集、并集这些简单集合操作。", 28),
            ],
            prepend=True,
        )

    functions = chapter_map.get("functions")
    if functions:
        functions["order"] = 6
        functions["title"] = "第六章：函数"
        _merge_sections(
            functions,
            [
                _planned_section("why-functions", "为什么需要函数", "从重复代码出发，理解函数能减少复制、让代码更清楚。", 18),
                _planned_section("function-return-vs-print", "return 和 print 的区别", "理解显示结果和交回结果不是一回事，做题时尤其重要。", 25),
                _planned_section("function-parameters", "参数与实参", "区分函数定义里的参数和调用时传入的值。", 25),
                _planned_section("scope-basics", "变量作用域基础", "理解函数里面的变量和外面的变量为什么有时不是同一个。", 30),
            ],
            prepend=True,
        )

    modules = chapter_map.get("modules-io-exceptions")
    if modules:
        modules["order"] = 7
        modules["title"] = "第七章：文件、模块与异常处理"
        _merge_sections(
            modules,
            [
                _planned_section("file-path-basics", "文件路径基础", "理解当前目录、相对路径、绝对路径，以及为什么找不到文件。", 25),
                _planned_section("read-write-text-files", "读写文本文件", "学习 open、with、read、write，能保存和读取简单文本。", 40),
                _planned_section("json-basics", "JSON 数据读写", "用 json 模块保存列表和字典，理解简单数据持久化。", 35),
                _planned_section("common-exceptions", "常见异常类型", "认识 ValueError、TypeError、IndexError、KeyError、FileNotFoundError。", 30),
                _planned_section("try-except-basics", "try / except 基础", "捕获预期错误，给用户更清楚的提示，而不是让程序直接崩掉。", 35),
                _planned_section("debug-with-print", "用 print 定位问题", "先掌握最简单有效的调试法：看变量、看分支、看循环次数。", 25),
            ],
            prepend=True,
        )

    oop = chapter_map.get("oop")
    if oop:
        oop["order"] = 8
        oop["title"] = "第八章：面向对象入门"
        oop["description"] = "只讲最基础、最常见的类和对象，不先深入复杂设计模式。"
        _merge_sections(
            oop,
            [
                _planned_section("class-object-basics", "类和对象是什么", "用生活例子理解类是模板，对象是根据模板创建出来的具体东西。", 30),
                _planned_section("attributes-methods", "属性与方法", "把数据放到对象属性里，把行为写成方法。", 35),
                _planned_section("init-self", "__init__ 与 self", "理解对象创建时如何初始化，以及 self 为什么总是出现。", 35),
                _planned_section("simple-class-practice", "简单类练习", "写一个 Student、Book 或 Account 类，完成基础属性和方法。", 40),
            ],
            prepend=True,
        )

    standard_library = chapter_map.get("standard-library")
    if standard_library:
        standard_library["order"] = 9
        standard_library["title"] = "第九章：项目习惯与小作品"
        standard_library["description"] = "把前面学过的知识组合起来，做几个小程序，同时形成基本工程习惯。"
        _merge_sections(
            standard_library,
            [
                _planned_section("project-folder-structure", "项目文件夹结构", "学会把代码、数据、说明文档分开放，避免所有文件堆在一起。", 25),
                _planned_section("requirements-readme", "requirements.txt 与 README", "记录依赖和运行说明，让别人也能跑起你的程序。", 25),
                _planned_section("mini-project-calculator", "小作品：命令行计算器", "综合 input、条件判断、函数和异常处理，做一个可交互的小程序。", 60),
                _planned_section("mini-project-todo", "小作品：待办事项列表", "综合列表、文件读写、函数，做一个可以保存数据的小程序。", 75),
            ],
            prepend=True,
        )

    CURRICULUM_CHAPTERS.sort(key=lambda item: int(item.get("order", 999)))


_enrich_beginner_curriculum()


def list_lessons(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return lesson summaries for the learning center."""
    items = LESSONS
    if language:
        items = [lesson for lesson in items if lesson.get("language") == language]
    return [
        {
            "id": lesson["id"],
            "language": lesson["language"],
            "title": lesson["title"],
            "topic": lesson["topic"],
            "difficulty": lesson["difficulty"],
            "summary": lesson["summary"],
            "source": lesson["source"],
        }
        for lesson in items
    ]


def list_curriculum(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the chapter/section outline used by the learning center."""
    lesson_map = {lesson["id"]: lesson for lesson in list_lessons(language=language)}
    chapters: List[Dict[str, Any]] = []
    for chapter in CURRICULUM_CHAPTERS:
        sections = []
        for section in chapter["sections"]:
            lesson_id = section.get("lesson_id") or section.get("id")
            lesson = lesson_map.get(str(lesson_id)) if lesson_id else None
            sections.append(
                {
                    **section,
                    "lesson_id": lesson_id,
                    "status": "ready" if lesson else section.get("status", "planned"),
                    "lesson": lesson,
                }
            )
        chapters.append({**chapter, "sections": sections})
    return chapters


def get_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
    """Return full lesson details by id."""
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return normalize_lesson(lesson)
    return None
