import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from agent.deal_hunter import DealHunterAgent
from db.database import Database
from scrapers.manager import ScraperManager
from models import STORE_METADATA

console = Console()


def print_banner():
    banner = Text("🛒 GazetkoAgent - Inteligentny Asystent Zakupowy AI 🛒", style="bold green on black")
    console.print(Panel(banner, subtitle="Biedronka • Lidl • Auchan • Dino • Carrefour", border_style="cyan"))


def handle_search(query: str, agent: DealHunterAgent):
    console.print(f"[bold cyan]🔍 Szukanie promocji dla:[/bold cyan] [bold yellow]{query}[/bold yellow]\n")
    deals = agent.search_single_product(query)

    if not deals:
        console.print("[red]❌ Nie znaleziono żadnych aktualnych promocji dla tego produktu.[/red]")
        return

    table = Table(title=f"Wyniki dla: {query}", show_header=True, header_style="bold magenta")
    table.add_column("Sklep", style="cyan", width=12)
    table.add_column("Produkt", style="white")
    table.add_column("Cena promocyjna", justify="right", style="bold green")
    table.add_column("Cena regularna", justify="right", style="dim")
    table.add_column("Rabat", justify="center", style="bold yellow")
    table.add_column("Warunki promocji", style="italic blue")

    for d in deals:
        meta = STORE_METADATA.get(d.store)
        emoji = meta.logo_emoji if meta else "🏪"
        store_display = f"{emoji} {d.store.value}"
        reg_display = f"{d.regular_price:.2f} zł" if d.regular_price else "-"
        disc_display = f"-{d.discount_percent:.0f}%" if d.discount_percent else "-"
        conditions = d.conditions or "Brak warunków"

        table.add_row(
            store_display,
            d.name,
            f"{d.promo_price:.2f} zł",
            reg_display,
            disc_display,
            conditions
        )

    console.print(table)
    cheapest = deals[0]
    console.print(f"\n[bold green]🏆 Najniższa cena:[/bold green] [bold white]{cheapest.name}[/bold white] w [bold yellow]{cheapest.store.value}[/bold yellow] za [bold green]{cheapest.promo_price:.2f} zł[/bold green]!\n")


def handle_basket(query: str, agent: DealHunterAgent):
    console.print(f"[bold cyan]🧺 Porównanie koszyka zakupowego dla:[/bold cyan] [bold yellow]{query}[/bold yellow]\n")
    items = agent.parse_customer_query_to_items(query)

    if not items:
        console.print("[red]❌ Nie udało się rozpoznać produktów w podanym zapytaniu.[/red]")
        return

    comparison = agent.compare_basket(items)

    table = Table(title="Porównanie kosztów koszyka w sklepach", show_header=True, header_style="bold magenta")
    table.add_column("Sklep", style="cyan", width=14)
    table.add_column("Suma koszyka", justify="right", style="bold green")
    table.add_column("Oszczędność", justify="right", style="bold yellow")
    table.add_column("Dostępne pozycje", justify="center")

    for s in comparison.store_summaries:
        meta = STORE_METADATA.get(s.store)
        emoji = meta.logo_emoji if meta else "🏪"
        is_winner = (s.store == comparison.best_store)
        winner_tag = " 🏆 [NAJTANIEJ]" if is_winner else ""
        table.add_row(
            f"{emoji} {s.store.value}{winner_tag}",
            f"{s.total_cost:.2f} zł",
            f"{s.savings_vs_regular:.2f} zł",
            f"{s.items_found}/{s.items_total}"
        )

    console.print(table)

    # Szczegóły koszyka
    console.print(Panel(comparison.recommendation, title="Rekomendacja Agenta", border_style="green"))


def handle_sync():
    console.print("[bold yellow]🔄 Pobieranie i synchronizacja najświeższych gazetek...[/bold yellow]")
    sm = ScraperManager()
    results = sm.sync_all()
    for store, res in results.items():
        console.print(f"  ✅ [cyan]{store}[/cyan]: zaktualizowano {res['leaflets']} gazetek, {res['deals']} ofert promocyjnych")
    stats = sm.db.get_stats()
    console.print(f"\n[bold green]Sukces![/bold green] Łącznie w bazie: {stats['deals_count']} promocji z {stats['leaflets_count']} gazetek.")


def interactive_chat(agent: DealHunterAgent):
    print_banner()
    console.print("[dim]Wpisz pytanie (np. 'ile kosztuje kawa w biedronce', 'masło, jaja i mleko - gdzie najtaniej'), lub 'exit' aby zakończyć.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]Ty[/bold green]")
            if not user_input or user_input.strip().lower() in ["exit", "quit", "q"]:
                console.print("[cyan]Do widzenia! Udanych i tanich zakupów! 👋[/cyan]")
                break

            response = agent.answer_customer_prompt(user_input)
            console.print(Panel(response, title="GazetkoAgent", border_style="cyan"))
        except (KeyboardInterrupt, EOFError):
            console.print("\n[cyan]Do widzenia![/cyan]")
            break


def main():
    db = Database()
    agent = DealHunterAgent(db=db)

    # Upewniamy się, że baza nie jest pusta przy pierwszym uruchomieniu
    if db.get_stats()["deals_count"] == 0:
        ScraperManager(db=db).sync_all()

    if len(sys.argv) < 2:
        interactive_chat(agent)
        return

    command = sys.argv[1].lower()

    if command == "sync":
        handle_sync()
    elif command == "search":
        if len(sys.argv) < 3:
            console.print("[red]Użycie: python -m cli.main search \"nazwa_produktu\"[/red]")
            return
        query = " ".join(sys.argv[2:])
        handle_search(query, agent)
    elif command in ["basket", "koszyk", "compare"]:
        if len(sys.argv) < 3:
            console.print("[red]Użycie: python -m cli.main basket \"masło, mleko, kawa\"[/red]")
            return
        query = " ".join(sys.argv[2:])
        handle_basket(query, agent)
    elif command == "chat":
        interactive_chat(agent)
    else:
        # Traktujemy jako bezpośrednie zapytanie
        full_query = " ".join(sys.argv[1:])
        console.print(Panel(agent.answer_customer_prompt(full_query), title="GazetkoAgent", border_style="cyan"))


if __name__ == "__main__":
    main()

