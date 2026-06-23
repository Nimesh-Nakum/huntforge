import cmd
import sys
import os
from rich.console import Console as RichConsole
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from core.database import Database

class SwathConsole(cmd.Cmd):
    intro = ""
    
    def __init__(self):
        super().__init__()
        self.rich_console = RichConsole()
        self.target = None
        self.update_prompt()
        self.db = Database()
        
        # Display Banner
        banner = """
  ╔═══════════════════════════════════════╗
  ║        SWATH v2.0 — HuntForge        ║
  ║   AI-Powered Bug Bounty Framework    ║
  ╚═══════════════════════════════════════╝
        """
        self.rich_console.print(Panel(banner, style="bold blue"))

    def update_prompt(self):
        if self.target:
            self.prompt = f"swath ({self.target}) > "
        else:
            self.prompt = "swath > "

    def do_use(self, arg):
        """Set current target domain: use <domain>"""
        if not arg:
            self.rich_console.print("[red]Usage: use <domain>[/red]")
            return
        self.target = arg
        self.db.upsert_target(self.target)
        self.rich_console.print(f"[*] Target set: [green]{self.target}[/green]")
        self.update_prompt()

    def do_targets(self, arg):
        """List all known targets from database"""
        conn = self.db._get_conn()
        cur = conn.execute('SELECT domain, program, first_seen, last_scanned FROM targets')
        rows = cur.fetchall()
        conn.close()
        
        table = Table(title="Known Targets")
        table.add_column("Domain", style="cyan")
        table.add_column("Program", style="magenta")
        table.add_column("First Seen")
        table.add_column("Last Scanned")
        
        for row in rows:
            table.add_row(row['domain'], str(row['program']), str(row['first_seen']), str(row['last_scanned']))
            
        self.rich_console.print(table)

    def do_scan(self, arg):
        """Launch scan with current settings"""
        if not self.target:
            self.rich_console.print("[red]Please set a target first using 'use <domain>'[/red]")
            return
            
        self.rich_console.print(f"[*] Launching SWATH scan for {self.target}...")
        # In a real integration, we'd invoke orchestrator.py here
        self.rich_console.print("[yellow]Scan running in background (mocked).[/yellow]")

    def do_findings(self, arg):
        """List all findings for current target"""
        if not self.target:
            self.rich_console.print("[red]Please set a target first.[/red]")
            return
            
        conn = self.db._get_conn()
        cur = conn.execute('''
            SELECT f.severity, f.type, f.title, f.is_reported 
            FROM findings f 
            JOIN targets t ON f.target_id = t.id 
            WHERE t.domain = ?
        ''', (self.target,))
        rows = cur.fetchall()
        conn.close()
        
        if not rows:
            self.rich_console.print("No findings yet.")
            return
            
        table = Table(title=f"Findings for {self.target}")
        table.add_column("Severity")
        table.add_column("Type")
        table.add_column("Title")
        table.add_column("Reported")
        
        for row in rows:
            sev = row['severity'].upper()
            color = "white"
            if sev == 'CRITICAL': color = "red bold"
            elif sev == 'HIGH': color = "red"
            elif sev == 'MEDIUM': color = "yellow"
            elif sev == 'LOW': color = "cyan"
            
            table.add_row(f"[{color}]{sev}[/{color}]", row['type'], row['title'], "Yes" if row['is_reported'] else "No")
            
        self.rich_console.print(table)

    def do_exit(self, arg):
        """Exit the console"""
        self.rich_console.print("Exiting...")
        return True
        
    def do_clear(self, arg):
        """Clear screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == '__main__':
    try:
        SwathConsole().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting...")
