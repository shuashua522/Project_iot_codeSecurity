from langchain.chat_models import init_chat_model
from langchain_core.callbacks import CallbackManager

from project_code.common.global_config import GLOBALCONFIG


def get_llm():
    # max_tokens: int = 512
    provider=GLOBALCONFIG.provider
    model = GLOBALCONFIG.model
    base_url = GLOBALCONFIG.base_url
    api_key = GLOBALCONFIG.api_key

    llm = init_chat_model(
        model=model,
        model_provider="openai",
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        # max_tokens=max_tokens  # 配置max_tokens
    )
    return llm

def get_llm_div(model,provider=GLOBALCONFIG.provider,base_url = GLOBALCONFIG.base_url,api_key = GLOBALCONFIG.api_key):
    max_tokens: int = 512

    llm = init_chat_model(
        model=model,
        model_provider="openai",
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        max_tokens=max_tokens,  # 配置max_tokens=
        timeout = 120,  # 🔥 【最重要】强制超时：20秒无响应直接断开，永不卡死
        top_p = 0.1,  # 🔥 锁死输出：杜绝小模型发散、无效思考
        stop = ["\n\n", ".", "。"]  # 🔥 通用停止词：输出双换行/句号立即停止
    )
    return llm