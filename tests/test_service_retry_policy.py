import pytest

from supportops_async.queue.contracts import BrokerMessage
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker import Worker
from supportops_platform.contracts import Principal
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


def test_real_mcp_connection_refusal_is_retried_by_p04_worker(monkeypatch):
    import supportops_platform.service_runtime as service_runtime

    monkeypatch.setenv('MCP_SIGNING_SECRET','s'*48)
    monkeypatch.setenv('MCP_ISSUER','p05-test')
    monkeypatch.setenv('MCP_URL','http://127.0.0.1:9/mcp')
    actor=Principal('caller-a','tenant-a',frozenset({'support'}),frozenset({'crm:read'}))
    calls=[]
    runtime=ServiceWorker.__new__(ServiceWorker)
    def execute(payload,step):
        calls.append(step)
        if len(calls)==1:
            return service_runtime.call_tool(actor,'lookup_customer',{'customer_id':'c-1'})
        return {'recovered':True}
    runtime._run_job=execute
    store=SQLiteTaskStore();broker=InMemoryBroker()
    task,_=store.create({'steps':['triage']},'mcp-transport-retry')
    broker.publish(BrokerMessage(task.task_id))
    worker=Worker(store,broker,runner=runtime.run_job)
    worker.run_once()
    assert store.get(task.task_id).status.value=='retrying'
    assert broker.dead_letters==[]
    worker.run_once()
    assert store.get(task.task_id).status.value=='done'
    assert store.get(task.task_id).attempts==2


def test_permanent_service_error_is_sanitized_before_installed_p04_worker():
    from supportops_async.worker.runner import PermanentFailure

    runtime=ServiceWorker.__new__(ServiceWorker)
    runtime._run_job=lambda payload,step: (_ for _ in ()).throw(RuntimeError('PRIVATE TENANT TICKET BODY'))
    with pytest.raises(PermanentFailure) as raised:
        runtime.run_job({},'triage')
    assert str(raised.value)=='worker_failure'
    assert 'PRIVATE TENANT TICKET BODY' not in str(raised.value)

    store=SQLiteTaskStore();broker=InMemoryBroker()
    task,_=store.create({'steps':['triage']},'sanitized-worker-failure')
    broker.publish(BrokerMessage(task.task_id))
    assert Worker(store,broker,runner=runtime.run_job,max_attempts=1).run_once()
    failed=store.get(task.task_id)
    assert failed.status.value=='failed'
    assert failed.error=='worker_failure'
    assert 'PRIVATE TENANT TICKET BODY' not in repr(failed)


def test_worker_span_does_not_export_exception_payload(monkeypatch):
    from types import SimpleNamespace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    import supportops_platform.service_runtime as service_runtime
    from supportops_async.worker.runner import PermanentFailure

    exporter=InMemorySpanExporter()
    provider=TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(service_runtime.trace, 'get_tracer', lambda name: provider.get_tracer(name))

    runtime=ServiceWorker.__new__(ServiceWorker)
    runtime.queue=SimpleNamespace(
        job=lambda _: {'id':'job-1','generation':0,'status':'queued','trace_context':{}},
        authorization_active=lambda *_: True,
        effect_exists=lambda *_: False,
    )
    runtime.store=SimpleNamespace(get_ticket=lambda *_: (_ for _ in ()).throw(
        RuntimeError('PRIVATE DATABASE OR TICKET CONTENT')
    ))
    runtime.queue.actor=lambda _: object()

    with pytest.raises(PermanentFailure, match='worker_failure'):
        runtime.run_job({'job_id':'job-1','generation':0},'triage')
    spans=exporter.get_finished_spans()
    assert len(spans)==1
    assert spans[0].events==()
    assert 'PRIVATE DATABASE OR TICKET CONTENT' not in repr(spans[0])
    provider.shutdown()


def test_all_p05_spans_disable_automatic_exception_recording():
    import ast
    from pathlib import Path

    package = Path(__file__).resolve().parents[1] / 'supportops_platform'
    violations=[]
    for source in package.rglob('*.py'):
        tree=ast.parse(source.read_text(encoding='utf-8'),filename=str(source))
        for node in ast.walk(tree):
            if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute):
                continue
            if node.func.attr != 'start_as_current_span':
                continue
            if not any(keyword.arg=='record_exception' and isinstance(keyword.value,ast.Constant) and keyword.value.value is False for keyword in node.keywords):
                violations.append(f'{source.relative_to(package)}:{node.lineno}')
    assert violations == []


def test_auth_failure_inside_exception_group_is_not_transient():
    from supportops_platform.service_runtime import _is_transient_transport_error

    assert not _is_transient_transport_error(ExceptionGroup('mcp', [ConnectionError('offline'), PermissionError('denied')]))
    assert not _is_transient_transport_error(ExceptionGroup('mcp', [PermissionError('denied')]))


def test_botocore_endpoint_and_read_timeouts_are_transient():
    from botocore.exceptions import EndpointConnectionError, ReadTimeoutError
    from supportops_platform.service_runtime import _is_transient_transport_error

    assert _is_transient_transport_error(EndpointConnectionError(endpoint_url='http://localhost'))
    assert _is_transient_transport_error(ReadTimeoutError(endpoint_url='http://localhost', error=TimeoutError()))
    assert _is_transient_transport_error(ExceptionGroup('nested', [ExceptionGroup('mcp', [ConnectionError('offline')])]))


def test_botocore_connect_and_closed_errors_are_transient():
    from botocore.exceptions import ConnectionClosedError, ConnectTimeoutError
    from supportops_platform.service_runtime import _is_transient_transport_error

    assert _is_transient_transport_error(ConnectTimeoutError(endpoint_url='http://localhost'))
    assert _is_transient_transport_error(ConnectionClosedError(endpoint_url='http://localhost'))


def test_botocore_permanent_client_error_is_not_transient():
    from botocore.exceptions import ClientError
    from supportops_platform.service_runtime import _is_transient_transport_error

    error=ClientError({'Error':{'Code':'AccessDenied','Message':'denied'}},'ReceiveMessage')
    assert not _is_transient_transport_error(error)


def test_standalone_worker_loop_retries_transport_and_surfaces_permanent_errors():
    from botocore.exceptions import EndpointConnectionError
    from supportops_platform.service_runtime import _run_once_with_retry

    class FailingWorker:
        def __init__(self, error): self.error=error
        def run_once(self): raise self.error

    delays=[]
    assert _run_once_with_retry(FailingWorker(EndpointConnectionError(endpoint_url='http://localhost')),sleep=delays.append) is False
    assert delays==[1]
    with pytest.raises(PermissionError):
        _run_once_with_retry(FailingWorker(PermissionError('denied')),sleep=delays.append)
