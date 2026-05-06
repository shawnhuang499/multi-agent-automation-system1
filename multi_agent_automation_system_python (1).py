# Multi-Agent AI Automation System (LLM Enhanced)
# Requires: pip install openai

import asyncio
import random
from openai import OpenAI

# 👉 替换为你的 API Key
client = OpenAI(api_key="YOUR_API_KEY_HERE")

class Message:
    def __init__(self, sender, receiver, content):
        self.sender = sender
        self.receiver = receiver
        self.content = content

class Agent:
    def __init__(self, name, system):
        self.name = name
        self.system = system
        self.inbox = asyncio.Queue()

    async def send(self, receiver, content):
        msg = Message(self.name, receiver, content)
        await self.system.route(msg)

    async def receive(self):
        return await self.inbox.get()

    async def run(self):
        raise NotImplementedError

# 🧠 LLM 调用函数
async def call_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AI assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# 🎯 Manager：用 AI 分配任务
class ManagerAgent(Agent):
    async def run(self):
        tasks = [
            "写一段关于AI的短文",
            "生成3个创业点子",
            "总结多Agent系统的优势"
        ]

        for task in tasks:
            # 用 AI 决策分配
            prompt = f"任务: {task}，从 Worker0, Worker1, Worker2 中选一个最合适执行"
            decision = await call_llm(prompt)

            worker = random.choice(self.system.workers)
            print(f"[Manager AI决策] {decision}")
            print(f"[Manager] Assigning {task} to {worker.name}")

            await self.send(worker.name, task)

# ⚙️ Worker：用 AI 执行任务
class WorkerAgent(Agent):
    async def run(self):
        while True:
            msg = await self.receive()
            print(f"[{self.name}] Received: {msg.content}")

            # AI 执行任务
            result = await call_llm(msg.content)

            await asyncio.sleep(random.uniform(0.5, 1.5))
            await self.send("Coordinator", f"{self.name} result: {result}")

# 📊 Coordinator：汇总结果
class CoordinatorAgent(Agent):
    async def run(self):
        completed = []
        while True:
            msg = await self.receive()
            print(f"[Coordinator] Got result: {msg.content}\n")
            completed.append(msg.content)

            if len(completed) >= 3:
                print("\n===== FINAL RESULTS =====")
                for c in completed:
                    print("-", c)
                break

class MultiAgentSystem:
    def __init__(self):
        self.agents = {}
        self.workers = []

    def register(self, agent):
        self.agents[agent.name] = agent
        if isinstance(agent, WorkerAgent):
            self.workers.append(agent)

    async def route(self, message):
        receiver = self.agents.get(message.receiver)
        if receiver:
            await receiver.inbox.put(message)

    async def run(self):
        tasks = []
        for agent in self.agents.values():
            tasks.append(asyncio.create_task(agent.run()))
        await asyncio.gather(*tasks)

# 🚀 主程序
async def main():
    system = MultiAgentSystem()

    manager = ManagerAgent("Manager", system)
    coordinator = CoordinatorAgent("Coordinator", system)
    workers = [WorkerAgent(f"Worker{i}", system) for i in range(3)]

    system.register(manager)
    system.register(coordinator)
    for w in workers:
        system.register(w)

    await asyncio.gather(
        manager.run(),
        coordinator.run(),
        *(w.run() for w in workers)
    )

if __name__ == "__main__":
    asyncio.run(main())
