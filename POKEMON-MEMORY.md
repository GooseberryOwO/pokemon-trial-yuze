# Pokémon 双局第一视角 trial

目标是验证完整记录能否跨局传给同一玩家。两局不能证明模型学会了更好的策略。

## 平台实测

1. 在本机项目的 `.env` 填好 `ALTRUAGENT_OFFICIAL_AGENT_KEY`、`OPENAI_API_KEY`，并选定同一个 `OPENAI_MODEL`。两局都在同一台电脑、同一项目目录运行。不要分享密钥。
2. 关闭会抢同一席位的其他 runtime。进入本项目目录，在 PowerShell 运行 `.\pokemon-memory.ps1 -Trial pilot01 -Game 1`。然后在平台 **Testing** 新建一场 Pokémon VGC Doubles Draft，自对战的两个席位选同一个 self-hosted agent；不要同时排其他测试局。
3. 等终端分别显示 P01、P02 的 game 1 completed，再按 Ctrl+C 停止监听。运行 `.\pokemon-memory.ps1 -Trial pilot01 -Game 2`，再建一场**新的**同款双席自对战；不要交换席位配置。两席都显示 game 2 completed 后停止监听。
4. 在 `trial-records/trial-pilot01/P01/` 和 `P02/` 分别检查 `game1.jsonl`、`game2.jsonl`。同目录下的 `.done.json` 才是完成标记。第二局首行的 `previous.sha256` 对应第一局完成标记的摘要校验值（不是内容总结）。

如果 PowerShell 不允许运行脚本，可在当前 PowerShell 窗口设置 `$env:POKEMON_TRIAL_ID='pilot01'` 和 `$env:POKEMON_TRIAL_STAGE='1'`，然后运行 `.\.venv\Scripts\python.exe -m agent --match --agent examples.pokemon_memory_agent`；第二局只把 stage 改为 `'2'`。

## 记录口径

- P01 是平台位置 0，P02 是位置 1。日志保留该席从 GameAPI 实际收到的所有游戏响应，包括等待更新、合法动作、行动回执和终局结果，以及发出的请求和模型返回的结构化决定。不能观测到的平台内部状态不属于第一视角。
- 第二局每次模型决策都收到本席第一局 JSONL 全文，包括最后一行。不会用经验总结、末尾若干步或对手私有日志替代；存档中的模型行动理由是当时的原始输出。上局内容不重复写入第二局的新日志。
- 两席必须各自完整结束第一局。若中途停止、记录被改动、模型调用超时或上下文不足，不会用部分记忆继续并宣称成功。保留原文件作诊断，重新测时用**新的 trial 名称**和新的比赛。长局可能更贵或超过模型/平台的时限。

## 无密钥演练

在项目目录运行 `.\.venv\Scripts\python.exe -m scripts.pokemon_memory_demo`。使用真实的游戏循环和日志/提示词代码，但平台响应和模型选择均为模拟。会打印四份文件的位置并逐字节验证两席第二局的输入。
