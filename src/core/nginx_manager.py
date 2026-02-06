from pathlib import Path
from rich.console import Console
import shutil

from src.core.config_manager import NGINX_CONF_DIR, load_config

console = Console()
HTTPS_TEMPLATE_PATH = Path("src/templates/nginx.conf.tpl")
HTTP_TEMPLATE_PATH = Path("src/templates/nginx-http.conf.tpl")
MAINTENANCE_PAGE_TEMPLATE_PATH = Path("src/templates/maintenance.html")

def generate_nginx_config():
    """
    Generates the nginx.conf file and copies the maintenance page.
    """
    config = load_config()
    strategy = config.get("ssl", {}).get("strategy")

    if strategy == "none":
        console.print("[dim]Skipping NGINX configuration (none/reverse-proxy mode).[/dim]")
        # Clean up any old config file that might be present
        output_path = NGINX_CONF_DIR / "nginx.conf"
        if output_path.exists():
            output_path.unlink()
        return

    # Proceed with generating config for HTTPS strategies
    template_path = HTTPS_TEMPLATE_PATH
    if not template_path.exists():
        console.print(f"[bold red]NGINX HTTPS template not found at {template_path}[/bold red]")
        return

    console.print("[cyan]Generating NGINX configuration...[/cyan]")

    with open(template_path, "r") as f:
        template = f.read()

    # Only substitute server names if we are using an HTTPS template
    if strategy != "none":
        server_names = " ".join(config["hosts"])
        template = template.replace("${OPAL_HOSTNAME}", server_names)

        # Set correct certificate paths based on strategy
        if strategy == "letsencrypt":
            # Let's Encrypt certificates are stored in /etc/letsencrypt/live/{domain}/
            domain = config["hosts"][0]
            cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
            key_path = f"/etc/letsencrypt/live/{domain}/privkey.pem"
        else:
            # For self-signed and manual, use the standard nginx certs directory
            cert_path = "/etc/nginx/certs/opal.crt"
            key_path = "/etc/nginx/certs/opal.key"

        template = template.replace("/etc/nginx/certs/opal.crt", cert_path)
        template = template.replace("/etc/nginx/certs/opal.key", key_path)

    output_path = NGINX_CONF_DIR / "nginx.conf"
    with open(output_path, "w") as f:
        f.write(template)

    console.print(f"[green]NGINX configuration written to {output_path}[/green]")

    # Also copy the maintenance page to a location accessible by nginx
    html_dir = NGINX_CONF_DIR.parent / "html"
    html_dir.mkdir(exist_ok=True)
    if MAINTENANCE_PAGE_TEMPLATE_PATH.exists():
        shutil.copy(MAINTENANCE_PAGE_TEMPLATE_PATH, html_dir / "maintenance.html")
        console.print(f"[green]Maintenance page copied to {html_dir}[/green]")
    else:
        console.print(f"[bold yellow]Maintenance page template not found at {MAINTENANCE_PAGE_TEMPLATE_PATH}[/bold yellow]") 