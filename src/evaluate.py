"""Evalúa el RAGSystem contra un Golden Set de preguntas con documento fuente
conocido, calculando Precision@k y Recall@k.

Uso:
    python -m src.evaluate
"""
import json

from . import config
from .hybrid_retriever import RAGSystem


def load_golden_set(path=config.GOLDEN_SET_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(rag: RAGSystem, golden_set: list, k: int = config.TOP_K) -> dict:
    rows = []
    for item in golden_set:
        pregunta = item["pregunta"]
        esperado = item["documento_id_esperado"]

        resultados = rag.query(pregunta, k=k)
        recuperados_ids = [
            doc.metadata.get("parent_id", doc.metadata.get("id")) for doc in resultados
        ]

        relevantes_recuperados = sum(1 for doc_id in recuperados_ids if doc_id == esperado)
        hit = relevantes_recuperados > 0

        # Con un único documento relevante por pregunta:
        # Recall@k = 1 si el documento esperado aparece entre los k recuperados, 0 si no.
        # Precision@k = proporción de los k recuperados que son relevantes.
        recall = 1.0 if hit else 0.0
        precision = relevantes_recuperados / k

        rows.append(
            {
                "pregunta": pregunta,
                "esperado": esperado,
                "recuperados": recuperados_ids,
                "hit": hit,
                "precision_at_k": precision,
                "recall_at_k": recall,
            }
        )

    avg_precision = sum(r["precision_at_k"] for r in rows) / len(rows)
    avg_recall = sum(r["recall_at_k"] for r in rows) / len(rows)

    return {"rows": rows, "avg_precision_at_k": avg_precision, "avg_recall_at_k": avg_recall}


def print_report(report: dict, k: int) -> None:
    print("\n=== Evaluación del RAGSystem (Golden Set) ===\n")
    for row in report["rows"]:
        estado = "OK " if row["hit"] else "MISS"
        print(f"[{estado}] {row['pregunta']}")
        print(f"       esperado:   {row['esperado']}")
        print(f"       recuperados: {row['recuperados']}")
        print(
            f"       precision@{k}: {row['precision_at_k']:.2f}   "
            f"recall@{k}: {row['recall_at_k']:.2f}\n"
        )

    print("--- Resumen ---")
    print(f"Precision@{k} promedio: {report['avg_precision_at_k']:.2f}")
    print(f"Recall@{k} promedio:    {report['avg_recall_at_k']:.2f}")


if __name__ == "__main__":
    golden_set = load_golden_set()
    rag = RAGSystem(top_k=config.TOP_K)
    report = evaluate(rag, golden_set, k=config.TOP_K)
    print_report(report, k=config.TOP_K)
