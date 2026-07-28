"""LegalExpertSlave — answers Algerian law questions using scoped RAG.

Failure mode: any error or missing RAG context returns confidence="low"
with a disclaimer instead of fabricating legal information.
"""

from typing import Any, Dict

from app.agents.slaves.base import BaseSlave, SlaveOutput
from app.prompts.slaves import LEGAL_EXPERT_SYSTEM


class LegalExpertSlave(BaseSlave):
    name = "legal_expert"
    description = "Answers Algerian law / réglementation / legal questions using official Journal Officiel documents"

    async def run(self, task: Dict[str, Any], context: Dict[str, Any]) -> SlaveOutput:
        try:
            rag_context = context.get("rag_context", [])
            if not rag_context:
                return SlaveOutput(
                    result="",
                    metadata={
                        "confidence": "low",
                        "disclaimer_applied": True,
                        "reason": "No legal documents found in RAG context",
                    },
                    error="No legal documents found in RAG context",
                )

            from app.rag.legal_retriever import retrieve_for_legal_query
            from app.graph.state import AsuqState
            import numpy as np

            supabase = context.get("supabase_client")
            if not supabase:
                return SlaveOutput(
                    result="",
                    metadata={"confidence": "low", "disclaimer_applied": True},
                    error="No supabase client available",
                )

            query = task.get("instructions", "") or context.get("current_normalized_input", "")
            embedding_model = context.get("embedding_model")
            if embedding_model:
                emb = embedding_model.encode(query).tolist()
            else:
                emb = np.zeros(768).tolist()

            retrieval_result = retrieve_for_legal_query(supabase, query, emb)

            documents = retrieval_result.get("documents", [])
            if not documents:
                return SlaveOutput(
                    result="",
                    metadata={
                        "confidence": "low",
                        "disclaimer_applied": True,
                        "reason": "No relevant legal documents retrieved",
                    },
                    error="No relevant legal documents retrieved",
                )

            context["legal_retrieval"] = retrieval_result

            verified_articles = []
            for doc in documents:
                meta = doc.get("verified_metadata", {})
                if meta:
                    verified_articles.append(meta)

            answer_prompt = LEGAL_EXPERT_SYSTEM.format(
                query=query,
                rag_context="\n\n".join(
                    f"[Source: {d.get('metadata', {}).get('source_pdf', 'unknown')}] {d.get('content', '')}"
                    for d in documents[:5]
                ),
                verified_citations="\n".join(
                    f"- {v}" for v in verified_articles[:10]
                ) if verified_articles else "No verified article citations available",
            )

            llm = context.get("llm")
            if not llm:
                return SlaveOutput(
                    result="",
                    metadata={"confidence": "low", "disclaimer_applied": True},
                    error="No LLM available",
                )

            response = await llm.agenerate([answer_prompt])
            result_text = response.generations[0][0].text

            return SlaveOutput(
                result=result_text,
                metadata={
                    "confidence": "high" if documents else "low",
                    "disclaimer_applied": True,
                    "sources_used": len(documents),
                    "verified_articles": len(verified_articles),
                },
            )

        except Exception as e:
            return SlaveOutput(
                result="",
                metadata={
                    "confidence": "low",
                    "disclaimer_applied": True,
                    "error_type": type(e).__name__,
                },
                error=str(e),
            )
