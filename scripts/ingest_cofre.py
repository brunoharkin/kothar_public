import asyncio

from backend.memory.semantic.context_embedder import context_embedder

async def main():
    print("Iniciando ingestao do Cofre...")
    result = await context_embedder.embed_all()
    print("Resultado:", result)

if __name__ == "__main__":
    asyncio.run(main())
