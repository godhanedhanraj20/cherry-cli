import os
import sys
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from typing import List, Optional

from services.auth import authenticate_user, check_auth_status, get_authenticated_client
from services.file_service import upload_file, get_files, download_file, delete_file, search_files
from services.metadata_service import manage_tags, rename_file
from services.backup_service import backup_metadata, list_metadata_backups, restore_metadata_backup
from utils.errors import TSGError
from utils.parser import format_size

app = typer.Typer(help="TSG-CLI: Telegram Storage CLI")
console = Console()

# --- UI Helpers ---
def success(msg: str):
    console.print(f"[green]✔ {msg}[/green]")

def error(msg: str):
    console.print(f"[red]❌ {msg}[/red]")

def warn(msg: str):
    console.print(f"[yellow]⚠ {msg}[/yellow]")

def info(msg: str):
    console.print(f"[cyan]ℹ {msg}[/cyan]")

def dim(msg: str):
    console.print(f"[dim]{msg}[/dim]")
    
def log_cb(level: str, msg: str):
    """Callback for passing into services so they can trigger CLI prints without importing styling."""
    if level == "info":
        info(msg)
    elif level == "warn":
        warn(msg)
    elif level == "error":
        error(msg)
    elif level == "dim":
        dim(msg)
    elif level == "progress":
        print(f"\r  {msg}", end="", flush=True)
    elif level == "progress_done":
        print()
    else:
        console.print(msg)

# Utility to run async code in typer
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        error(f"Error: {str(e)}")
        sys.exit(1)

@app.command()
def login():
    """Authenticate with Telegram."""
    console.print("\n[bold cyan]=== Login ===[/bold cyan]\n")
    async def _login():
        status = await check_auth_status()
        if status.get("logged_in"):
            success("Already logged in!")
            if status.get("is_premium"):
                success("Premium account detected — 4GB upload limit")
            else:
                warn("Free account — 2GB upload limit")
            return
            
        def prompt_cb(text: str, is_password: bool):
            return typer.prompt(text, hide_input=is_password)
            
        result = await authenticate_user(prompt_cb, log_cb)
        
        if result.get("status") == "success":
            success("Successfully logged in!")
            if result.get("is_premium"):
                success("Premium account detected — 4GB upload limit")
            else:
                warn("Free account — 2GB upload limit")
        elif result.get("status") == "already_logged_in":
            success("Already logged in!")
        else:
            error("Login failed.")

    try:
        run_async(_login())
    except TSGError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error(f"Login failed: {str(e)}")
        raise typer.Exit(1)

@app.command()
def upload(path: str = typer.Argument(..., help="Path to the file or directory to upload")):
    """Upload a file or folder to Saved Messages."""
    console.print("\n[bold cyan]=== Upload ===[/bold cyan]\n")
    
    if not os.path.exists(path):
        error(f"Error: Path '{path}' does not exist.")
        raise typer.Exit(1)
        
    async def _upload():
        client = await get_authenticated_client()
        successful = 0
        failed = 0
        
        try:
            if os.path.isfile(path):
                info(f"Uploading: {os.path.basename(path)} (1/1)")
                dim(f"({os.path.relpath(path)})")
                try:
                    metadata = await upload_file(client, path, log_cb)
                    success(f"Uploaded: {metadata['name']} (ID: {metadata['id']}, Size: {metadata['size']})")
                    successful += 1
                except Exception as e:
                    error(f"Failed to upload {os.path.basename(path)}: {str(e)}")
                    failed += 1
            elif os.path.isdir(path):
                info(f"Scanning folder: {path}")
                files_to_upload = []
                for root, _, files in os.walk(path):
                    for file in files:
                        files_to_upload.append(os.path.join(root, file))
                        
                total = len(files_to_upload)
                if total == 0:
                    warn("Directory is empty. Nothing to upload.")
                    return
                    
                info(f"Found {total} files.")
                confirm = typer.confirm(f"Upload {total} files?")
                if not confirm:
                    warn("Upload cancelled.")
                    return
                    
                for i, file_path in enumerate(files_to_upload, 1):
                    console.print()
                    info(f"Uploading: {os.path.basename(file_path)} ({i}/{total})")
                    dim(f"({os.path.relpath(file_path)})")
                    try:
                        metadata = await upload_file(client, file_path, log_cb)
                        success(f"Uploaded: {metadata['name']} (ID: {metadata['id']}, Size: {metadata['size']})")
                        successful += 1
                    except KeyboardInterrupt:
                        raise
                    except TSGError as e:
                        if "File skipped" in str(e):
                            warn(f"Skipped: {os.path.basename(file_path)}")
                            dim(str(e))
                            successful += 1
                            continue
                        error(f"Failed to upload {os.path.basename(file_path)}: {str(e)}")
                        failed += 1
                    except Exception as e:
                        error(f"Failed to upload {os.path.basename(file_path)}: {str(e)}")
                        failed += 1
                        
            console.print("\n[bold]Summary[/bold]")
            success(f"Success: {successful}")
            error(f"Failed: {failed}")
            
        finally:
            await client.disconnect()

    run_async(_upload())

@app.command()
def list(
    limit: int = typer.Option(50, help="Number of files to fetch (max 200)"),
    page: int = typer.Option(1, help="Page number (1-indexed)"),
    sort: str = typer.Option("date", "--sort", "-s", help="Sort order: date, name, size"),
    file_type: str = typer.Option(None, "--type", "-t", help="Filter by file type: video, image, document, audio"),
    tag: str = typer.Option(None, "--tag", help="Filter by tag (supports comma-separated list of tags, e.g., 'work,urgent')"),
    debug: bool = typer.Option(False, "--debug", hidden=True)
):
    """List uploaded files."""
    console.print("\n[bold cyan]=== List Files ===[/bold cyan]\n")
    async def _list():
        client = await get_authenticated_client()
        try:
            if debug:
                info(f"Fetching up to {limit} files (Page {page}, Sort: {sort})...")
            else:
                info("Fetching files...")
                
            files = await get_files(client, limit=limit, sort_by=sort, file_type=file_type, tag=tag, page=page, debug=debug)
            
            if not files:
                warn("No files found.")
                return

            title = f"Files (Page {page})"
            if file_type or tag:
                filters = []
                if file_type: filters.append(f"Type: {file_type}")
                if tag: filters.append(f"Tags: {tag}")
                title += f" [{', '.join(filters)}]"
                
            table = Table(title=title)
            table.add_column("ID", justify="left", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Date", style="blue")
            table.add_column("Tags", style="yellow")

            for f in files:
                table.add_row(str(f["id"]), f["name"], f["size"], f["date"], f.get("tags", "-"))

            console.print(table)
        finally:
            await client.disconnect()
        
    run_async(_list())

@app.command()
def download(
    file_ids: List[int] = typer.Argument(..., help="ID(s) of the file(s) to download"),
    output: str = typer.Option(".", "--output", "-o", help="Output directory path")
):
    """Download files by ID."""
    console.print("\n[bold cyan]=== Download ===[/bold cyan]\n")
    async def _download():
        output_dir = os.path.abspath(output)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        client = await get_authenticated_client()
        successful = 0
        failed = 0
        interrupted = False
        
        total_files = len(file_ids)
        
        try:
            for i, fid in enumerate(file_ids, 1):
                try:
                    if not client.is_connected:
                        await client.start()
                except Exception:
                    pass
                    
                try:
                    console.print()
                    info(f"Downloading: ID {fid} ({i}/{total_files})")
                    dim(f"Output path: {output_dir}")
                    path = await download_file(client, fid, output_dir, log_cb)
                    success(f"Saved to: {os.path.relpath(path)}")
                    successful += 1
                except KeyboardInterrupt:
                    raise  # Caught by the outer loop
                except TSGError as e:
                    error(f"Failed to download {fid}: {str(e)}")
                    failed += 1
                except Exception as e:
                    error(f"Failed to download {fid}: {str(e)}")
                    failed += 1
                    
            if not interrupted:
                console.print("\n[bold]Summary[/bold]")
                success(f"Success: {successful}")
                error(f"Failed: {failed}")
            
        except KeyboardInterrupt:
            interrupted = True
            console.print()
            warn("Batch download cancelled by user")
            raise typer.Exit(1)
        finally:
            try:
                await client.stop()
            except Exception:
                pass

    run_async(_download())

@app.command()
def search(
    query: str = typer.Argument(None, help="Keyword to search for in file names"),
    limit: int = typer.Option(50, help="Number of files to fetch (max 200)"),
    page: int = typer.Option(1, help="Page number (1-indexed)"),
    sort: str = typer.Option("date", "--sort", "-s", help="Sort order: date, name, size"),
    file_type: str = typer.Option(None, "--type", "-t", help="Filter by file type: video, image, document, audio"),
    tag: str = typer.Option(None, "--tag", help="Filter by tag (supports comma-separated tags)"),
    debug: bool = typer.Option(False, "--debug", hidden=True)
):
    """Search for files by name, tag, or type."""
    console.print("\n[bold cyan]=== Search ===[/bold cyan]\n")
    async def _search():
        client = await get_authenticated_client()
        try:
            trimmed_query = query.strip() if query else None
            ft = file_type.strip().lower() if file_type else None

            msg_parts = []
            if trimmed_query: msg_parts.append(f"name containing '{trimmed_query}'")
            if tag: msg_parts.append(f"tag '{tag}'")
            if ft: msg_parts.append(f"type '{ft}'")
            
            if not msg_parts:
                warn("Please provide a search query, --tag, or --type.")
                raise typer.Exit(1)

            info(f"Searching files for {' and '.join(msg_parts)}...")
            
            files = await search_files(client, trimmed_query, limit, file_type=ft, sort_by=sort, tag=tag, page=page, debug=debug)
            
            if not files:
                warn("No files found.")
                console.print()
                info("Try:")
                console.print("  tsg-cli search pokemon")
                console.print("  tsg-cli search --tag anime")
                return

            title = f"Search Results: Page {page}"
            filters = []
            if trimmed_query: filters.append(f"Query: '{trimmed_query}'")
            if tag: filters.append(f"Tag: {tag}")
            if ft: filters.append(f"Type: {ft}")
            
            if filters:
                title += f" [{', '.join(filters)}]"

            table = Table(title=title)
            table.add_column("ID", justify="left", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Date", style="blue")
            table.add_column("Tags", style="yellow")

            for f in files:
                table.add_row(str(f["id"]), f["name"], f["size"], f["date"], f.get("tags", "-"))

            console.print(table)
        finally:
            await client.disconnect()
        
    run_async(_search())

@app.command()
def tag(
    file_ids_str: str = typer.Argument(..., metavar="FILE_IDS", help="ID(s) of the file(s) separated by commas"),
    action: str = typer.Argument(..., help="Action to perform: add, remove, list"),
    tag_name: str = typer.Argument(None, help="The tag name (required for add/remove)")
):
    """Manage tags for files."""
    console.print("\n[bold cyan]=== Manage Tags ===[/bold cyan]\n")
    successful = 0
    failed = 0
    file_ids = [fid.strip() for fid in file_ids_str.split(",")]
    
    try:
        for fid in file_ids:
            try:
                result = manage_tags([fid], action, tag_name)[0]
                if action == "add":
                    success(f"Tag added to {fid}: {tag_name}")
                elif action == "remove":
                    success(f"Tag removed from {fid}: {tag_name}")
                elif action == "list":
                    tags = result.get("tags", [])
                    if tags:
                        info(f"Tags for {fid}: {', '.join(tags)}")
                    else:
                        warn(f"No tags found for {fid}.")
                successful += 1
            except Exception as e:
                error(f"Failed on {fid}: {str(e)}")
                failed += 1
                
        console.print("\n[bold]Summary[/bold]")
        success(f"Success: {successful}")
        error(f"Failed: {failed}")
    except TSGError as e:
        error(f"Error: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)

@app.command()
def rename(
    file_id: str = typer.Argument(..., help="ID of the file"),
    name: str = typer.Argument(None, help="New custom name (leave empty to reset)")
):
    """Rename a file (virtual name)"""
    console.print("\n[bold cyan]=== Rename File ===[/bold cyan]\n")
    try:
        result = rename_file(file_id, name)
        if result.get("removed"):
            success("Custom name removed")
        else:
            success(f"Name updated: {result['custom_name']}")
    except TSGError as e:
        error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        error("Unexpected error occurred. Please try again.")
        raise typer.Exit(1)

@app.command()
def backup():
    """Backup local metadata to Telegram Saved Messages."""
    console.print("\n[bold cyan]=== Backup Metadata ===[/bold cyan]\n")
    async def _backup():
        client = await get_authenticated_client()
        try:
            info("Backing up metadata to Telegram...")
            await backup_metadata(client)
            success("Backup uploaded to Telegram")
        finally:
            await client.disconnect()

    run_async(_backup())

@app.command()
def restore(select: bool = typer.Option(False, "--select", help="Choose backup manually")):
    """Restore metadata from a Telegram backup."""
    console.print("\n[bold cyan]=== Restore Metadata ===[/bold cyan]\n")
    async def _restore():
        client = await get_authenticated_client()
        try:
            info("Searching for backups...")
            backups = await list_metadata_backups(client)
            if not backups:
                raise TSGError("No backup found")
            
            if select:
                table = Table(title="Available Backups")
                table.add_column("ID", justify="left", style="cyan", no_wrap=True)
                table.add_column("Name", style="magenta")
                table.add_column("Size", justify="right", style="green")
                table.add_column("Date", style="blue")

                for msg in backups:
                    date_str = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else "Unknown"
                    file_name = getattr(msg.document, "file_name", "metadata_backup.json")
                    file_size = format_size(getattr(msg.document, "file_size", 0))
                    table.add_row(str(msg.id), file_name, file_size, date_str)

                console.print(table)
                warn("Enter the backup ID from the table above")
                
                selected_id = typer.prompt("Backup ID")
                try:
                    selected_id = int(selected_id)
                except ValueError:
                    raise TSGError("Invalid backup ID")

                await restore_metadata_backup(client, backup_id=selected_id)
            else:
                await restore_metadata_backup(client)
            success("Metadata restored successfully from Telegram backup")
        finally:
            await client.disconnect()

    run_async(_restore())

@app.command()
def delete(file_ids: List[str] = typer.Argument(..., help="ID(s) of the file(s) to delete")):
    """Delete files by ID."""
    console.print("\n[bold cyan]=== Delete Files ===[/bold cyan]\n")
    async def _delete():
        client = await get_authenticated_client()
        successful = 0
        failed = 0
        try:
            if len(file_ids) == 1:
                confirm = typer.confirm(f"Are you sure you want to delete file ID {file_ids[0]}?")
            else:
                confirm = typer.confirm(f"Are you sure you want to delete these {len(file_ids)} files?")
                
            if not confirm:
                warn("Deletion cancelled.")
                return
                
            total = len(file_ids)
            for i, fid in enumerate(file_ids, 1):
                try:
                    file_id_int = int(fid)
                    info(f"Deleting: ID {file_id_int} ({i}/{total})")
                    await delete_file(client, file_id_int)
                    success(f"File {file_id_int} deleted successfully")
                    successful += 1
                except Exception as e:
                    error(f"Failed to delete {fid}: {str(e)}")
                    failed += 1
                    
            console.print("\n[bold]Summary[/bold]")
            success(f"Success: {successful}")
            error(f"Failed: {failed}")
        finally:
            await client.disconnect()

    run_async(_delete())

if __name__ == "__main__":
    app()
