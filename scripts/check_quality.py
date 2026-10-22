"""P02 regression gate over actual P05 fake control flow; no model quality claim."""

import argparse
import json
from pathlib import Path
import sys
from supportops_toolkit.evals import run_evals
from supportops_toolkit.evals.runner import assert_regression,RegressionError
from supportops_platform.agents.triage import run_fake_triage
from supportops_platform.contracts import Ticket
from supportops_platform.rag.retrieval import LocalRetriever,KnowledgeDocument

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'evals/datasets/v1/control.jsonl'


def evaluate(degraded=False):
    def runner(case):
        retriever=LocalRetriever([KnowledgeDocument('policy','tenant-a','Invoice policy',case['evidence'])])
        run=run_fake_triage(Ticket('tenant-a','customer-a','Invoice',case['text']),retriever)
        return {'decision':'escalate' if degraded else run.result.decision.action,
                'tool':'search_kb' if any(step.action=='search_kb' for step in run.result.trace) else None,
                'answer':'unsupported invention' if degraded else run.result.decision.response,
                'escalate':run.result.stop_reason!='approved'}
    report=run_evals(runner,DATA)
    baseline={name:1.0 for name in ('decision_accuracy','tool_call_accuracy','groundedness','escalation_accuracy')}
    print(json.dumps({'fixture_only':True,'model_quality':'PENDING',**report.as_dict()}))
    assert_regression(report,baseline,max_drop=0)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--degraded',action='store_true');args=parser.parse_args()
    try: evaluate(args.degraded)
    except RegressionError as exc:
        print('quality gate: FAIL '+str(exc));sys.exit(1)
