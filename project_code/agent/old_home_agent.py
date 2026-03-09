from typing import TypedDict, Literal

from langchain.agents import create_agent

from langgraph.types import Command
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

from typing_extensions import TypedDict, Annotated
import operator

from pydantic import BaseModel, Field
from typing import List  # 推荐导入List，规范类型注解

from project_code.agent.llm_prompt import checker_prompt
from project_code.common.get_llm import get_llm


# Define the structure for email classification


class SmartHomeAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    command: str
    # task: str

    context_info: str
    generated_code: str

    final_answer:str

    # Raw search/API results
    search_results: list[str] | None  # List of raw document chunks
    customer_history: dict | None  # Raw customer data from CRM

    # Generated content
    draft_response: str | None
    # messages: list[str] | None

    llm_calls: int


def node_checker(state:SmartHomeAgentState)-> Command[Literal[ END]]:
    """
    检查节点
    :param state:
    :return:
    """

    prompt = checker_prompt.format(
        context_info=state["context_info"],
        generated_code=state["generated_code"]
    )
    agent = create_agent(model=get_llm(),
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
    content = [AIMessage(content=ans)]
    print(ans)
    # if:
    return Command(
        update={"messages": content,},  # Store raw results or error
        goto=END
    )



def run_ourAgent(context_info:str,generated_code:str):
    agent_builder = StateGraph(SmartHomeAgentState)
    # Add nodes
    agent_builder.add_node("check_node", node_checker)

    agent_builder.add_edge(START, "check_node")

    agent = agent_builder.compile()

    initial_state = {
        "context_info": context_info,
        "generated_code": generated_code,
        # "messages": [HumanMessage(content="")]
    }
    result = agent.invoke(initial_state)
    # for m in result["messages"]:
    #     m.pretty_print()


if __name__ == "__main__":
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
