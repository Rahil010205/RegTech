"""Re-index all clause vectors in Qdrant."""


def main() -> None:
    """Re-embed and upsert all current regulation clauses. Implementation pending."""
    print("Re-indexing vectors...")
    # TODO: iterate regulation_versions where is_current=true, dispatch embed_clauses_task


if __name__ == "__main__":
    main()
