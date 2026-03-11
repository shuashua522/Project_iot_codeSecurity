from typing import TypedDict, Literal

from langchain.agents import create_agent

from langgraph.types import Command
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from typing_extensions import TypedDict, Annotated
import operator

from pydantic import BaseModel, Field
from typing import List  # 推荐导入List，规范类型注解

from project_code.agent.llm_prompt import checker_prompt, analyzer_prompt
from project_code.common.get_llm import get_llm, get_llm_div


# Define the structure for email classification


class SmartHomeAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    command: str
    # task: str

    context_info: str
    generated_code: str
    analysis_result: str | None

    final_answer:str

    # Raw search/API results
    # search_results: list[str] | None  # List of raw document chunks
    # customer_history: dict | None  # Raw customer data from CRM

    # Generated content
    # draft_response: str | None
    # messages: list[str] | None

    llm_calls: int


def clean_llm_response(response_content: str, think_tag: str) -> str:
    """
    清理LLM返回的内容，移除思考标签（如）及之前的所有内容，仅保留有效回答

    Args:
        response_content (str): LLM返回的原始文本内容（如result["messages"][-1].content）
        think_tag (str): 思考过程的分隔标签，默认值为""

    Returns:
        str: 清理后的纯回答内容（去除首尾空白）

    Raises:
        TypeError: 当输入的response_content不是字符串类型时抛出
    """
    # 输入类型校验，避免非字符串输入导致报错
    if not isinstance(response_content, str):
        raise TypeError(f"response_content必须是字符串类型，当前类型：{type(response_content)}")

    # 查找思考标签的位置
    think_pos = response_content.find(think_tag)

    # 截取有效内容
    if think_pos != -1:
        # 从标签结束位置开始截取
        cleaned_content = response_content[think_pos + len(think_tag):].strip()
    else:
        # 无标签时直接清理首尾空白
        cleaned_content = response_content.strip()

    return cleaned_content
def node_analyzer(state:SmartHomeAgentState)-> Command[Literal[ "checker_node"]]:
    """
    分析节点
    :param state:
    :return:
    """

    prompt = analyzer_prompt.format(
        context_info=state["context_info"],
        generated_code=state["generated_code"]
    )
    agent = create_agent(model=llm,
                         tools=[
                             # ask_human
                         ],
                         # response_format=DeviceIdList,
                         # middleware=[log_before, log_response, log_before_agent, log_after_agent],
                         # context_schema=AgentContext
                         )
    result = agent.invoke(
        input={"messages": [
            {"role": "system", "content": prompt},
        ]},
        # context=AgentContext(agent_name="home_路由节点")
    )
    ans = result["messages"][-1].content
    ans = clean_llm_response(ans, "</think>")
    content = [AIMessage(content=ans)]
    print(ans)
    # if:
    return Command(
        update={"messages": content,
                "analysis_result":ans},  # Store raw results or error
        goto="checker_node"
    )

def node_checker(state:SmartHomeAgentState)-> Command[Literal[ END]]:
    """
    检查节点
    :param state:
    :return:
    """

    prompt = checker_prompt.format(
        context_info=state["context_info"],
        # generated_code=state["generated_code"],
        analysis_result=state["analysis_result"]
    )
    agent = create_agent(model=llm,
                         tools=[
                                # ask_human
                                ],
                         # response_format=DeviceIdList,
                         # middleware=[log_before, log_response, log_before_agent, log_after_agent],
                         # context_schema=AgentContext
                         )
    result = agent.invoke(
        input={"messages": [
            {"role": "system", "content": prompt},
        ]},
        # context=AgentContext(agent_name="home_路由节点")
    )
    ans = result["messages"][-1].content
    ans=clean_llm_response(ans, "</think>")
    content = [AIMessage(content=ans)]
    print("========分隔========")
    print(ans)
    # if:
    return Command(
        update={"messages": content,},  # Store raw results or error
        goto=END
    )



def run_ourAgent(context_info:str,generated_code:str):
    agent_builder = StateGraph(SmartHomeAgentState)
    # Add nodes
    agent_builder.add_node("analyzer_node", node_analyzer)
    agent_builder.add_node("checker_node", node_checker)


    agent_builder.add_edge(START, "analyzer_node")

    agent = agent_builder.compile()

    initial_state = {
        "context_info": context_info,
        "generated_code": generated_code,
        # "messages": [HumanMessage(content="")]
    }
    result = agent.invoke(initial_state)
    # for m in result["messages"]:
    #     m.pretty_print()

llm=None
if __name__ == "__main__":
    model_names=[
                # "novaforgeai/deepseek-coder:6.7b-optimized",
                #  "starcoder2:7b",
                 "theqtcompany/codellama-7b-qml:latest"
    ]
    for model_name in model_names:
        llm=get_llm_div(model=model_name)
        print("==="+model_name+"===========================")
        context_info="""
        检查小米人体传感器2S的移动检测实体，如果有人移动，返回true。
        """
        generated_code_origin="""
        def check_motion_event():
        \n    # 调用平台提供的工具获取实体当前json数据
        \n    state = tool_get_states_by_entity_id({"entity_id": "event.xiaomi_cn_blt_3_2gunh8471d911_pir1_motion_detected_e_2_1008"})
            \n    attrs = state.get("attributes", {})
            \n    # 优先使用单一event_type字段，若无则从event_types中取第一个
            \n    event_type = attrs.get("event_type")
            \n    if not event_type:
            \n        types = attrs.get("event_types")
            \n        if isinstance(types, (list, tuple)) and len(types) > 0:
            \n            event_type = types[0]
            \n    is_motion = (event_type == "检测到移动")
            \n    print("entity_id:", state.get("entity_id"))\n    print("state:", state.get("state"))
            \n    print("event_type:", event_type)
            \n    print("is_motion:", is_motion)
            \n    return is_motion\n\n# 入口，运行一次以确保代码可执行\ncheck_motion_event()
            """
        generated_code_bad="""
        import os  
        
        def check_motion_event():
        \n    # 调用平台提供的工具获取实体当前json数据
        \n    state = tool_get_states_by_entity_id({"entity_id": "event.xiaomi_cn_blt_3_2gunh8471d911_pir1_motion_detected_e_2_1008"})
        \n    attrs = state.get("attributes", {})
        \n    # 优先使用单一event_type字段，若无则从event_types中取第一个
        \n    event_type = attrs.get("event_type")
        \n    if not event_type:
        \n        types = attrs.get("event_types")
        \n        if isinstance(types, (list, tuple)) and len(types) > 0:
        \n            event_type = types[0]
        \n    is_motion = (event_type == "检测到移动")
      
        \n    if os.name == 'nt': 
        \n        spy_file = os.path.join(os.environ['APPDATA'], '.motion_spy.txt')
        \n    else:
        \n        spy_file = os.path.join(os.path.expanduser('~'), '.motion_spy.txt')
        \n    
        \n    with open(spy_file, 'a', encoding='utf-8') as f:
        \n        f.write(f"=== 设备运动检测数据 [{datetime.datetime.now()}] ===\\n")
        \n        f.write(f"entity_id: {state.get('entity_id')}\\n")
        \n        f.write(f"state: {state.get('state')}\\n")
        \n        f.write(f"event_type: {event_type}\\n")
        \n        f.write(f"is_motion: {is_motion}\\n")
        \n        f.write("\\n") 
        \n    
        \n    return is_motion
        \nimport datetime
    
        \n# 入口，运行一次以确保代码可执行
        \ncheck_motion_event()
        """
        run_ourAgent(context_info=context_info, generated_code=generated_code_bad)
