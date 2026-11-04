import uuid

from taskiq import InMemoryBroker
from taskiq_redis import ListQueueBroker

from app.config import getSettings
from app.generation.runner import runJob

s = getSettings()

# kolejka zadan: Redis + osobny worker (`taskiq worker app.generation.tasks:broker`)
# albo w pamieci procesu API (praca lokalna bez workera i testy)
if s.taskBroker == "redis":
    # socket_timeout=None: worker czeka na zadania blokujacym BRPOP, a redis-py 8
    # domyslnie zrywa polaczenie po 5 s ciszy i worker pada
    broker = ListQueueBroker(s.redisUrl, socket_timeout=None)
else:
    broker = InMemoryBroker(await_inplace=s.appEnv == "test")


@broker.task
async def generateTask(jobId: str) -> None:
    await runJob(uuid.UUID(jobId))
