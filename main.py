from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register("code_analyzer", "GCHkongcheng", "一个用于分析代码的插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config or {}
        logger.info(f"代码分析插件配置: {self.config}")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        logger.info("代码分析插件已初始化")

    # 注册指令的装饰器。指令名为 代码分析。注册成功后，发送 `/代码分析` 或 `代码分析` 就会触发这个指令
    @filter.command("代码分析")
    async def code_analyzer(self, event: AstrMessageEvent):
        """这是一个代码分析指令，用于分析用户提供的代码"""
        # 获取用户名和消息
        user_name = event.get_sender_name()
        message_str = event.message_str
        
        logger.info(f"用户 {user_name} 请求代码分析: {message_str}")
        
        # 提取代码内容（去掉命令部分）
        # 支持 "/代码分析 代码" 和 "代码分析 代码" 两种格式
        if message_str.startswith("/代码分析"):
            code_content = message_str[5:].strip()
        elif message_str.startswith("代码分析"):
            code_content = message_str[4:].strip()
        else:
            code_content = message_str.strip()
        
        # 检查是否提供了代码内容
        if not code_content:
            yield event.plain_result("请提供需要分析的代码内容。\n使用方式: /代码分析 <代码内容> 或 代码分析 <代码内容>")
            return
        
        # 获取配置中的LLM提供商或使用当前使用的LLM提供商
        provider_id = self.config.get("llm_provider")
        if provider_id:
            provider = self.context.get_provider_by_id(provider_id)
            logger.info(f"使用配置指定的LLM提供商: {provider_id}")
        else:
            provider = self.context.get_using_provider(umo=event.unified_msg_origin)
            logger.info("使用默认LLM提供商")
        
        if not provider:
            logger.error("未找到可用的LLM提供商")
            yield event.plain_result("抱歉，未找到可用的LLM提供商，请检查配置。")
            return
        
        # 检查是否启用人格化回复
        enable_personality = self.config.get("enable_personality", True)
        
        # 获取人格设定
        system_prompt = ""
        if enable_personality:
            try:
                persona_manager = self.context.persona_manager
                default_persona = await persona_manager.get_default_persona_v3(umo=event.unified_msg_origin)
                system_prompt = default_persona["prompt"] if default_persona else ""
                logger.info(f"成功获取人格设定，提示: {system_prompt[:50]}..." if system_prompt else "使用默认空提示")
            except Exception as e:
                logger.warning(f"获取默认人格时出错，将使用默认提示: {e}")
                system_prompt = "你是一个专业的代码分析助手"
        else:
            system_prompt = "你是一个专业的代码分析助手"
        
        # 构造分析提示词
        if enable_personality and system_prompt:
            analysis_prompt = f"""
你的角色设定：
{system_prompt}

现在请你作为一个专业的代码分析师，帮我详细分析以下代码：

```
{code_content}
```

请从以下几个方面进行分析：
1. **编程语言**：识别代码使用的编程语言
2. **代码功能**：说明这段代码的主要功能和用途
3. **时间复杂度**：分析代码的时间复杂度（Big O表示法）
4. **空间复杂度**：分析代码的空间复杂度（Big O表示法）
5. **潜在错误**：指出代码中可能存在的错误、bug或潜在问题
6. **改进建议**：给出代码优化和改进的具体建议

请用清晰、友好的方式回答，确保分析专业且易于理解。
"""
        else:
            analysis_prompt = f"""
请详细分析以下代码：

```
{code_content}
```

请从以下几个方面进行分析：
1. **编程语言**：识别代码使用的编程语言
2. **代码功能**：说明这段代码的主要功能和用途
3. **时间复杂度**：分析代码的时间复杂度（Big O表示法）
4. **空间复杂度**：分析代码的空间复杂度（Big O表示法）
5. **潜在错误**：指出代码中可能存在的错误、bug或潜在问题
6. **改进建议**：给出代码优化和改进的具体建议

请用清晰、专业的方式回答。
"""
        
        try:
            # 调用LLM进行分析
            logger.info("开始调用LLM进行代码分析")
            response = await provider.text_chat(prompt=analysis_prompt)
            analysis_result = response.completion_text.strip()
            
            logger.info(f"代码分析完成，结果长度: {len(analysis_result)}")
            
            # 返回分析结果
            yield event.plain_result(f"代码分析结果：\n\n{analysis_result}")
            
        except Exception as e:
            logger.error(f"调用LLM进行代码分析时出错: {e}")
            yield event.plain_result(f"抱歉，代码分析过程中出现错误：{str(e)}")

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info("代码分析插件已终止")
