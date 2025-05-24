#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "typer[all]",
#     "requests",
#     "rich",
#     "python-dotenv",
# ]
# ///

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.text import Text

app = typer.Typer()
console = Console()

# Load environment variables from .env file in the script's directory
script_dir = Path(__file__).resolve().parent
env_file = script_dir / ".env"
load_dotenv(env_file)


def get_github_token(token: Optional[str] = None) -> str:
    """Get GitHub token from parameter, environment, or .env file."""
    if token:
        return token

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        console.print("[red]Error:[/red] No GitHub token provided.")
        console.print("\nPlease provide a token using one of these methods:")
        console.print(
            "1. Pass it as a parameter: [cyan]codespaces --token YOUR_TOKEN[/cyan]"
        )
        console.print(
            "2. Set it in your environment: [cyan]export GITHUB_TOKEN=YOUR_TOKEN[/cyan]"
        )
        console.print(
            "3. Create a .env file with: [cyan]GITHUB_TOKEN=YOUR_TOKEN[/cyan]"
        )
        console.print(
            "\n[yellow]Note:[/yellow] The token should be a 'Personal access token (classic)' with:"
        )
        console.print("  - 'codespace' permission enabled")
        console.print(
            "  - Authorization for any organization that owns your codespaces"
        )
        raise typer.Exit(1)

    return token


def fetch_codespaces(token: str) -> Dict[str, Any]:
    """Fetch codespaces from GitHub API."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(
            "https://api.github.com/user/codespaces", headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            console.print(
                "[red]Error:[/red] Invalid token or insufficient permissions."
            )
            console.print(
                "\nEnsure your token has 'codespace' permission and is authorized for the organization."
            )
        else:
            console.print(f"[red]Error:[/red] GitHub API error: {e}")
        raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error:[/red] Failed to connect to GitHub API: {e}")
        raise typer.Exit(1)


def calculate_expiration_info(
    codespace: Dict[str, Any],
) -> tuple[Optional[datetime], Optional[str], str]:
    """Calculate expiration datetime, human-readable time, and color."""
    retention_expires_at = codespace.get("retention_expires_at")

    if not retention_expires_at:
        return None, None, "gray"

    expires_dt = datetime.fromisoformat(retention_expires_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    if expires_dt <= now:
        return expires_dt, "Expired", "red"

    delta = expires_dt - now
    days = delta.days
    hours = delta.seconds // 3600

    # Format human-readable time
    if days == 0:
        if hours == 0:
            minutes = delta.seconds // 60
            time_str = f"{minutes}m"
        else:
            time_str = f"{hours}h"
    elif days == 1:
        time_str = "1 day"
    else:
        time_str = f"{days} days"

    # Determine color based on urgency
    if days < 7:
        color = "red"
    elif days < 14:
        color = "yellow"
    else:
        color = "green"

    return expires_dt, time_str, color


def get_state_color(state: str) -> str:
    """Get color for codespace state."""
    state_lower = state.lower()
    if state_lower == "available":
        return "green"
    elif state_lower == "shutdown":
        return "yellow"
    else:
        return "red"


def format_git_status(git_status: Dict[str, Any]) -> str:
    """Format git status into a readable string."""
    parts = []

    if git_status.get("has_uncommitted_changes"):
        parts.append("uncommitted")

    if git_status.get("has_unpushed_changes"):
        parts.append("unpushed")

    ahead = git_status.get("ahead", 0)
    behind = git_status.get("behind", 0)

    if ahead > 0:
        parts.append(f"↑{ahead}")

    if behind > 0:
        parts.append(f"↓{behind}")

    return ", ".join(parts) if parts else "clean"


def filter_codespaces(
    codespaces: List[Dict[str, Any]],
    days: Optional[int] = None,
    repo: Optional[str] = None,
    state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter codespaces based on criteria."""
    filtered = codespaces

    if repo:
        filtered = [
            cs for cs in filtered if repo.lower() in cs["repository"]["name"].lower()
        ]

    if state:
        filtered = [cs for cs in filtered if cs["state"].lower() == state.lower()]

    if days is not None:
        now = datetime.now(timezone.utc)
        filtered_by_days = []

        for cs in filtered:
            expires_dt, _, _ = calculate_expiration_info(cs)
            if expires_dt:
                delta = expires_dt - now
                if delta.days <= days:
                    filtered_by_days.append(cs)

        filtered = filtered_by_days

    return filtered


def print_codespaces_table(codespaces: List[Dict[str, Any]]) -> None:
    """Print codespaces in a rich table format."""
    if not codespaces:
        console.print("[yellow]No codespaces found matching your criteria.[/yellow]")
        return

    # Create table
    table = Table(title="GitHub Codespaces", show_lines=True)
    table.add_column("Display Name", style="cyan", no_wrap=True)
    table.add_column("Repository", style="blue")
    table.add_column("State", justify="center")
    table.add_column("Expires In", justify="right")
    table.add_column("Last Used", style="dim")
    table.add_column("Machine", style="dim")
    table.add_column("Git Status", style="dim")

    # Add rows
    for cs in codespaces:
        # Get expiration info
        expires_dt, expires_str, expires_color = calculate_expiration_info(cs)
        expires_text = Text(expires_str or "Active", style=expires_color)

        # Get state with color
        state = cs["state"]
        state_color = get_state_color(state)
        state_text = Text(state, style=state_color)

        # Format last used
        last_used = cs.get("last_used_at")
        if last_used:
            last_used_dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
            last_used_str = last_used_dt.strftime("%Y-%m-%d")
        else:
            last_used_str = "Never"

        # Format machine info
        machine = cs.get("machine", {})
        machine_str = machine.get("display_name", "Unknown")

        # Format git status
        git_status = cs.get("git_status", {})
        git_status_str = format_git_status(git_status)

        table.add_row(
            cs["display_name"],
            cs["repository"]["name"],
            state_text,
            expires_text,
            last_used_str,
            machine_str,
            git_status_str,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(codespaces)} codespace(s)[/dim]")


def print_codespaces_json(codespaces: List[Dict[str, Any]]) -> None:
    """Print codespaces as JSON."""
    # Add calculated fields
    for cs in codespaces:
        expires_dt, expires_str, _ = calculate_expiration_info(cs)
        cs["_expires_in"] = expires_str
        cs["_expires_timestamp"] = expires_dt.isoformat() if expires_dt else None

    console.print_json(json.dumps(codespaces, indent=2))


@app.command()
def main(
    token: Optional[str] = typer.Option(
        None, "--token", "-t", help="GitHub personal access token (overrides .env file)"
    ),
    days: Optional[int] = typer.Option(
        None, "--days", "-d", help="Show only codespaces expiring within N days"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Filter by repository name (partial match)"
    ),
    state: Optional[str] = typer.Option(
        None,
        "--state",
        "-s",
        help="Filter by codespace state (e.g., Available, Shutdown)",
    ),
    json_output: bool = typer.Option(
        False, "--json", "-j", help="Output as JSON for scripting"
    ),
):
    """
    List GitHub Codespaces sorted by expiration date.

    Token Requirements:
    - Must be a "Personal access token (classic)"
    - Must have "codespace" permission enabled
    - Must be authorized for any organization that owns your codespaces

    Examples:
        codespaces
        codespaces --days 7
        codespaces --repo web --state Shutdown
        codespaces --json
    """
    # Get token
    github_token = get_github_token(token)

    # Fetch codespaces
    with console.status("[bold green]Fetching codespaces..."):
        data = fetch_codespaces(github_token)

    codespaces = data.get("codespaces", [])

    if not codespaces:
        console.print("[yellow]No codespaces found.[/yellow]")
        raise typer.Exit(0)

    # Filter codespaces
    filtered_codespaces = filter_codespaces(codespaces, days, repo, state)

    # Sort by expiration date (soonest first, None values last)
    def sort_key(cs):
        expires_dt, _, _ = calculate_expiration_info(cs)
        if expires_dt is None:
            return datetime.max.replace(tzinfo=timezone.utc)
        return expires_dt

    filtered_codespaces.sort(key=sort_key)

    # Display results
    if json_output:
        print_codespaces_json(filtered_codespaces)
    else:
        print_codespaces_table(filtered_codespaces)


if __name__ == "__main__":
    app()
