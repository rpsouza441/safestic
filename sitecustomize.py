try:  # pragma: no cover - utilitario de ambiente
    import keyring

    if not hasattr(keyring, "__version__"):
        keyring.__version__ = "unknown"
except Exception:
    pass
