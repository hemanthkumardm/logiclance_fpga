import sys
from rich.console import Console

# redirect stdout
class Capture:
    def __init__(self):
        self.out = ""
    def write(self, s):
        self.out += s
    def flush(self): pass

cap = Capture()
c = Console(file=cap, force_terminal=True, color_system="standard")
c.print("[red]Hello[/red] [bold green]World[/bold green] [yellow]Warning[/yellow]")

print(repr(cap.out))
