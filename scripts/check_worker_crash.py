"""Run inside the API container: kill after a simulated refund commit and recover."""

import os
import subprocess
import sys
import time
from uuid import uuid4

import psycopg
from supportops_platform.contracts import Principal,Ticket
from supportops_platform.service_runtime import create_components,ServiceWorker


def main():
    os.environ['P05_QUEUE_NAME']='p05-crash-'+uuid4().hex
    store,retriever,queue,_=create_components()
    actor=Principal('crash-agent','tenant-a',frozenset({'agent'}),frozenset({'triage:run','task:write','billing:read','crm:read','refund:request'}))
    ticket=store.add_ticket(actor,Ticket('tenant-a','customer-a','Refund invoice','Review invoice refund policy.'))
    job=queue.enqueue(actor,'triage',{'ticket_id':ticket.id},uuid4().hex)
    worker=ServiceWorker(store,retriever,queue)
    assert worker.run_once()
    paused=queue.get(actor,job.id)
    assert paused.status.value=='needs_approval'
    approval=store.decide_approval(Principal('crash-reviewer','tenant-a',frozenset({'approver'}),frozenset({'approval:decide'})),paused.result['approval_id'],'approved')
    queue.resume(approval.id)
    code='''
import time
from supportops_platform.service_runtime import create_components,ServiceWorker
s,r,q,_=create_components()
original=s.simulated_refund
def committed_then_wait(job_id,amount):
    result=original(job_id,amount)
    time.sleep(120)
    return result
s.simulated_refund=committed_then_wait
worker=ServiceWorker(s,r,q)
while not worker.run_once(): time.sleep(.2)
'''
    child=subprocess.Popen([sys.executable,'-c',code],env=os.environ.copy(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    try:
        deadline=time.monotonic()+30
        while True:
            with psycopg.connect(store.dsn) as conn:
                committed=conn.execute('SELECT count(*) FROM platform_effects WHERE job_id=%s',(job.id,)).fetchone()[0]
            if committed: break
            if child.poll() is not None: raise AssertionError('child failed before effect commit: '+child.stdout.read())
            assert time.monotonic()<deadline,'child did not commit the simulated effect'
            time.sleep(.1)
        child.terminate();assert child.wait(timeout=5)!=0
        deadline=time.monotonic()+45
        while queue.get(actor,job.id).status.value!='succeeded':
            assert time.monotonic()<deadline,'product job did not recover after worker death'
            worker.run_once()
            time.sleep(.3)
        with psycopg.connect(store.dsn) as conn:
            assert conn.execute('SELECT count(*) FROM platform_effects WHERE job_id=%s',(job.id,)).fetchone()[0]==1
        attempts=queue.get(actor,job.id).attempts
        assert attempts>=1
        print(f'product-worker-crash: PASS killed_after_refund_commit=true job_recovered=true effect_rows=1 backend_attempts={attempts}')
    finally:
        if child.poll() is None: child.terminate();child.wait(timeout=5)
        queue.broker.client.delete_queue(QueueUrl=queue.broker.queue_url)
        queue.broker.client.delete_queue(QueueUrl=queue.broker.dlq_url)


if __name__=='__main__': main()
