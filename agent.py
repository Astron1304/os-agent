from log_config import logger

def chunk_answer(prompt, agent, agent_config):
    logger.info("Агент начал формировать ответ в режиме чанков")
    try:
        question = {"messages": [("user", prompt)]}
        chunks = 0
        tool_use = 0
        temp_log = ""
        full_response = ""
        all_nodes =[]
        print("Агент: ", end="", flush=True) 
        for chunk, metadata in agent.stream(question, config=agent_config, stream_mode="messages"):
            chunks +=1
            node = metadata.get("langgraph_node")
            all_nodes.append(node) if node not in all_nodes else None
            temp_log += (f"Чанк: {chunk}\n\tМетаданные: {metadata}\n\t")
            if node == "model":
                if chunk.content:
                    print(chunk.content,end="",flush=True)
                    full_response+=chunk.content
            elif node == "tools":
                tool_use+=1
        print('')
        logger.debug(temp_log)
        logger.info(f"Ответ сформирован: \"{full_response}\"")
        logger.info(f"Чанков всего: {chunks}\n\tИнструментов использовано: {tool_use}")
        logger.info(f"Все ноды: {all_nodes}")
        return full_response
    except Exception as e:
         logger.fatal(f"Фатальная ошибка в chunk_answer: {e}")
         return "fatal"
        
def whole_answer(prompt, agent, agent_config):
    logger.info("Агент начал формировать ответ полностью")
    try:
        result = agent.invoke({"messages": [("user", prompt)]}, config=agent_config)
        logger.info(f"Ответ сформирован: \"{result['messages'][-1].content}\"")
        logger.debug(f"Полный ответ агента: {result['messages']}")
        return f"Агент: {result['messages'][-1].content}\n"
    except Exception as e:
        logger.fatal(f"Фатальная ошибка ошибка в whole_answer: {e}")
        return "fatal"