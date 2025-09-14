# * Função para executar crons tasks
import asyncio
import time
from datetime import datetime

from croniter import croniter


async def execute_task(func):
    """Executa uma função assincronamente."""
    await func()


def schedule_task(cron_expression, func):
    """Agenda a execução da função com base na expressão CRON."""
    base_time = datetime.now()
    cron = croniter(cron_expression, base_time)

    async def runner():
        while True:
            # Pega o próximo horário baseado na expressão CRON
            next_run = cron.get_next(datetime)
            now = datetime.now()

            # Calcula o tempo até o próximo horário
            wait_time = (next_run - now).total_seconds()

            # Aguarda até o horário de execução
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # Executa a função assincronamente
            await execute_task(func)

    # Inicia a execução assincrona
    asyncio.create_task(runner())


# Exemplo de uso


async def minha_funcao():
    print(f"Executando função em {datetime.now()}")


# Exemplo de expressão CRON: "*/1 * * * *" (executa a cada minuto)
cron_expression = "*/1 * * * *"

# Iniciar o agendamento
schedule_task(cron_expression, minha_funcao)

# Necessário para manter o loop rodando
asyncio.get_event_loop().run_forever()
