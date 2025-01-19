from langchain_core.runnables import RunnableParallel
from app.childreen_queries.children_queries import children_queries_graph
from app.query_executor.executor import executor_chain

chain = (
    RunnableParallel(children_queries=children_queries_graph, query_executor=executor_chain)
)

chain.invoke({})