# Patch to add _ready_section function and update _enrich_beginner_curriculum

# Add this function after _planned_section function (around line 3431):

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


# Then in _enrich_beginner_curriculum, replace the sections list with:
"""
        "sections": [
            _ready_section("what-is-python", "Python 是什么，适合做什么", "理解 Python 的用途、解释型语言特点，以及它能解决哪些常见问题。", 12),
            _ready_section("install-python-windows", "Windows 安装 Python", "下载官方安装包，勾选 PATH，验证 python --version 是否可用。", 20),
            _ready_section("install-python-macos-linux", "macOS / Linux 环境说明", "了解 python3 命令、系统自带版本、包管理器安装和版本确认。", 18),
            _ready_section("terminal-basics", "终端与命令行最小必备", "会打开终端、切换目录、运行命令，知道错误信息从哪里看。", 25),
            _ready_section("vscode-python-extension", "VS Code 与 Python 插件配置", "安装 VS Code、Python 扩展，选择解释器，运行当前文件。", 25),
            _ready_section("first-python-file", "第一个 .py 文件", "创建 hello.py，写 print，保存并运行，建立"写代码-运行-看结果"的闭环。", 20),
        ],
"""
