import os
import tempfile
import asyncio
from src.notebookllama.documents import DocumentManager, ManagedDocument


def test_document_manager_disconnect_releases_file():
    # Create a temporary sqlite file
    fd, path = tempfile.mkstemp(prefix="test_notebookllama_", suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{path}"

    # Create manager and add a document
    doc_manager = DocumentManager(engine_url=db_url)
    doc = ManagedDocument(
        document_name="disconnect_test",
        content="content",
        summary="sum",
        q_and_a="",
        mindmap="",
        bullet_points=""
    )

    doc_manager.put_documents([doc])

    # Disconnect to release file locks
    doc_manager.disconnect()

    # Ensure we can remove the file
    try:
        os.remove(path)
    except Exception as e:
        raise AssertionError(f"Could not remove sqlite file after disconnect: {e}")

    assert not os.path.exists(path)
