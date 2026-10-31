"""Seed the demo knowledge base for tenant-a and tenant-b.

Usage: P05_POSTGRES_DSN=postgresql://... python scripts/seed_demo_knowledge.py

The documents are short, original support articles written for the public demo. Re-running replaces them
(ingest deletes a document's old chunks first), so the script is idempotent. Tenants never share documents.
"""

import os
import sys

from supportops_platform.rag.postgres import PostgresRetriever
from supportops_platform.rag.retrieval import KnowledgeDocument

DOCS = [
    ("password-reset", "Password reset", "To reset a password, open the sign-in page and choose Forgot password. A reset link is emailed to the account address and stays valid for one hour. If no email arrives, check the spam folder, confirm the address on the account, and ask for a new link. Support never asks for a password."),
    ("invoice-policy", "Invoice and duplicate charge policy", "Verify a duplicate charge in the billing ledger before promising a refund. Invoices are issued monthly and list every charge. A confirmed duplicate charge is refunded to the original payment method. Refunds above the agent limit need a second person to approve them."),
    ("refund-window", "Refund window", "Refund requests are accepted for 30 days after the charge. A refund is returned to the original payment method and can take several business days to appear. Refunds are never paid to a different account."),
    ("account-access", "Account access and locked accounts", "An account locks after repeated failed sign-ins. The owner can unlock it by resetting the password. Changing the account email requires confirming the old and the new address."),
    ("shipping-delay", "Shipping delays", "Orders ship within two business days. When a shipment is late, check the tracking page, then open a carrier inquiry. A package marked delivered but not received needs a carrier claim before a replacement is sent."),
    ("data-export", "Exporting and deleting account data", "Account data can be exported from Settings, Privacy. A deletion request removes the account after a confirmation email and cannot be undone once confirmed."),
]

PRIVATE_B = ("tenant-b-private", "Tenant B internal billing notes", "Internal billing notes that belong only to tenant B. They must never appear in an answer for another tenant.")


def main() -> int:
    dsn = os.environ.get("P05_POSTGRES_DSN", "").strip()
    if not dsn:
        print("P05_POSTGRES_DSN is required", file=sys.stderr)
        return 2
    retriever = PostgresRetriever(dsn)
    chunks = 0
    for doc_id, title, text in DOCS:
        chunks += retriever.ingest(KnowledgeDocument(doc_id, "tenant-a", title, text))
    chunks += retriever.ingest(KnowledgeDocument(PRIVATE_B[0], "tenant-b", PRIVATE_B[1], PRIVATE_B[2]))
    check = retriever.search("tenant-a", "I did not receive the password reset email")
    leaked = [c for c in check if c.document_id.startswith("tenant-b")]
    print(f"ingested {chunks} chunks; sample search returned {len(check)}; cross-tenant leak: {len(leaked)}")
    return 1 if leaked or not check else 0


if __name__ == "__main__":
    raise SystemExit(main())
