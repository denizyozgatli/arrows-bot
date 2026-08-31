import click
from arrows_bot.executor.bot import BotExecutor

@click.group()
def cli():
    pass

@cli.command("auto-play")
def auto_play_cmd():
    """Yeni nesil Graph tabanlı çözücüyü başlatır."""
    bot = BotExecutor()
    # Tek ekrana sığan bir bölüm için doğrudan çalıştır
    bot.execute_blind_run()

if __name__ == "__main__":
    cli()