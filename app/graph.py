from langgraph.graph import StateGraph

builder = StateGraph()

builder.add_node("query_executor", query_executor)