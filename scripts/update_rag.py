import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.insert(0, '/home/bruno/kothar')

try:
    from backend.core.project_mode import index_project
    async def main():
        print("Indexing Kothar...")
        await index_project("/home/bruno/kothar")
        print("Indexing Cofre...")
        await index_project("/home/bruno/cofre")
        print("RAG updated successfully.")
    asyncio.run(main())
except Exception as e:
    print(f"Error: {e}")
