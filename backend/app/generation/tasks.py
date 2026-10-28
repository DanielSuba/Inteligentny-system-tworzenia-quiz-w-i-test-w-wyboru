import uuid

from taskiq import InMemoryBroker
from taskiq_redis import ListQueueBroker

from app.config import getSettings
from app.generation.runner import runJob

s = getSettings()

# kolejka zadan: Redis + osobny worker (`taskiq worker app.generation.tasks:broker`)
# albo w pamieci procesu API (praca lokalna bez workera i testy)
if s.taskBroker == "redis":
    broker = ListQueueBroker(s.redisUrl)
else:
    broker = InMemoryBroker(await_inplace=s.appEnv == "test")


@broker.task
async def generateTask(jobId: str) -> None:
    await runJob(uuid.UUID(jobId))
