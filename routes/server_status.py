from flask import Blueprint, render_template, session, redirect, url_for
import psutil
import datetime

bp = Blueprint("server_status", __name__)


def _require_admin():
    if not session.get("is_admin"):
        return redirect(url_for("dashboard.index"))
    return None


def _get_status():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    try:
        cpu_freq = psutil.cpu_freq()
        cpu_freq_mhz = round(cpu_freq.current) if cpu_freq else None
    except Exception:
        cpu_freq_mhz = None

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disk_partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / 1024**3, 1),
                "used_gb": round(usage.used / 1024**3, 1),
                "free_gb": round(usage.free / 1024**3, 1),
                "percent": usage.percent,
            })
        except PermissionError:
            continue

    net = psutil.net_io_counters()
    net_sent_mb = round(net.bytes_sent / 1024**2, 1)
    net_recv_mb = round(net.bytes_recv / 1024**2, 1)

    boot_ts = psutil.boot_time()
    boot_dt = datetime.datetime.fromtimestamp(boot_ts)
    uptime = datetime.datetime.now() - boot_dt
    uptime_str = _format_uptime(uptime)

    try:
        temps = psutil.sensors_temperatures()
        temp_entries = []
        for name, entries in (temps or {}).items():
            for e in entries:
                temp_entries.append({"label": e.label or name, "current": e.current, "high": e.high})
    except (AttributeError, Exception):
        temp_entries = []

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "cpu_count_logical": cpu_count_logical,
        "cpu_freq_mhz": cpu_freq_mhz,
        "mem_total_gb": round(mem.total / 1024**3, 1),
        "mem_used_gb": round(mem.used / 1024**3, 1),
        "mem_free_gb": round(mem.available / 1024**3, 1),
        "mem_percent": mem.percent,
        "swap_total_gb": round(swap.total / 1024**3, 1),
        "swap_used_gb": round(swap.used / 1024**3, 1),
        "swap_percent": swap.percent,
        "disk_partitions": disk_partitions,
        "net_sent_mb": net_sent_mb,
        "net_recv_mb": net_recv_mb,
        "uptime_str": uptime_str,
        "boot_time": boot_dt.strftime("%d.%m.%Y %H:%M"),
        "temperatures": temp_entries,
    }


def _format_uptime(td: datetime.timedelta) -> str:
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


@bp.route("/admin/server-status")
def index():
    guard = _require_admin()
    if guard:
        return guard
    return render_template(
        "server_status.html",
        page_id="server_status",
        status=_get_status(),
    )
