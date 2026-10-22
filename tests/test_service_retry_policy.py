from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_platform.service_runtime import ServiceWorker


def test_temporary_service_error_retries_through_real_p04_worker():
    runtime=ServiceWorker.__new__(ServiceWorker)
    calls=[]
    def execute(payload,step):
        calls.append(step)
        if len(calls)==1: raise TimeoutError('controlled temporary MCP failure')
        return {'recovered':True}
    runtime._run_job=execute
    store=SQLiteTaskStore();broker=InMemoryBroker()
    task,_=store.create({'steps':['triage']},'service-retry')
    broker.publish(BrokerMessage(task.task_id))
    worker=Worker(store,broker,runner=runtime.run_job)
    worker.run_once()
    assert store.get(task.task_id).status.value=='retrying'
    assert broker.dead_letters==[]
    worker.run_once()
    assert store.get(task.task_id).status.value=='done'
    assert store.get(task.task_id).attempts==2
