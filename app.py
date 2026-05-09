#!/usr/bin/env python3
"""
WebArchiver — Web Sayfası Yedekleme Aracı
==========================================
Herhangi bir web sayfasını tüm varlıklarıyla (CSS, JS, görseller, fontlar)
birlikte arşivler. Çıktı ZIP veya TAR.GZ formatında verilir.

Gereksinimler:
    pip install flask flask-cors requests beautifulsoup4 lxml

Kullanım:
    python app.py
    Tarayıcıda aç: http://localhost:5000
"""

import io
import os
import re
import time
import zipfile
import tarfile
import hashlib
import threading
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# ─── Uygulama Kurulumu ────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

OUTPUT_DIR = Path("downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

# HTTP oturumu — tarayıcı gibi görünen başlıklarla
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

# İş takibi: {job_id: {...}}
JOBS: dict[str, dict] = {}


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def safe_local_path(url: str, index: int = 0) -> str:
    """URL'yi güvenli bir yerel dosya yoluna dönüştürür."""
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path).lstrip("/") or f"file_{index}"
        # Uzantı yoksa .bin ekle
        if "." not in Path(path).name:
            path += f"_{index}.bin"
        # Güvensiz karakterleri temizle
        path = re.sub(r'[^\w.\-/]', '_', path)
        return f"assets/{path[:120]}"
    except Exception:
        return f"assets/file_{index}.bin"


def fetch_url(url: str, timeout: int = 15) -> tuple[bytes | None, str]:
    """
    Verilen URL'yi indirir.
    Döndürür: (içerik_bytes, içerik_türü) veya (None, '')
    """
    try:
        resp = SESSION.get(url, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "")
    except requests.exceptions.Timeout:
        return None, ""
    except requests.exceptions.HTTPError:
        return None, ""
    except Exception:
        return None, ""


def extract_asset_urls(html: bytes, base_url: str) -> list[str]:
    """
    HTML belgesinden tüm varlık URL'lerini çıkarır.
    CSS, JS, görseller, fontlar, video, ses ve iframe'ler dahildir.
    """
    soup = BeautifulSoup(html, "lxml")
    assets: set[str] = set()

    # Standart etiket → öznitelik eşlemeleri
    tag_attrs = [
        ("link",   "href"),    # CSS dosyaları
        ("script", "src"),     # JavaScript
        ("img",    "src"),     # Görseller
        ("img",    "data-src"),# Lazy-loaded görseller
        ("source", "src"),     # Video/ses kaynakları
        ("source", "srcset"),  # Duyarlı görseller
        ("video",  "src"),     # Video
        ("audio",  "src"),     # Ses
        ("iframe", "src"),     # Gömülü içerik
        ("track",  "src"),     # Altyazılar
    ]

    for tag, attr in tag_attrs:
        for el in soup.find_all(tag):
            value = el.get(attr, "")
            if not value:
                continue
            # srcset birden fazla URL içerebilir
            for part in value.split(","):
                raw = part.strip().split()[0]
                if raw and not raw.startswith("data:"):
                    try:
                        assets.add(urljoin(base_url, raw))
                    except Exception:
                        pass

    # <style> etiketleri ve satır içi style öznitelikleri
    for style_tag in soup.find_all("style"):
        assets.update(_extract_css_urls(style_tag.get_text(), base_url))

    for el in soup.find_all(style=True):
        assets.update(_extract_css_urls(el["style"], base_url))

    # Yalnızca HTTP/HTTPS URL'leri döndür
    return [u for u in assets if u.startswith(("http://", "https://"))]


def _extract_css_urls(css_text: str, base_url: str) -> list[str]:
    """CSS metni içindeki url(...) referanslarını çıkarır."""
    urls = []
    for match in re.findall(r'url\s*\(\s*["\']?([^)"\']+)["\']?\s*\)', css_text):
        match = match.strip()
        if match and not match.startswith("data:"):
            try:
                urls.append(urljoin(base_url, match))
            except Exception:
                pass
    return urls


def rewrite_html(html: bytes, asset_map: dict[str, str]) -> bytes:
    """
    HTML içindeki orijinal URL'leri yerel dosya yollarıyla değiştirir.
    Bu sayede arşiv çevrimdışı çalışabilir.
    """
    text = html.decode("utf-8", errors="replace")
    for original_url, local_path in asset_map.items():
        text = text.replace(original_url, local_path)
    return text.encode("utf-8")


def discover_subpages(html: bytes, base_url: str, limit: int = 20) -> list[str]:
    """
    Aynı domain içindeki bağlantıları keşfeder (derin tarama modu).
    En fazla `limit` adet alt sayfa döndürür.
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    subpages: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        # Yalnızca aynı domain, fragment olmadan
        if parsed.netloc == base_domain and href != base_url:
            clean = href.split("#")[0].rstrip("/")
            if clean:
                subpages.add(clean)

    return list(subpages)[:limit]


# ─── Ana Yedekleme İşlevi ─────────────────────────────────────────────────────

def run_backup(job_id: str, target_url: str, deep_crawl: bool, output_format: str):
    """
    Arka planda çalışan yedekleme işçisi.
    JOBS sözlüğünü ilerleme bilgisiyle günceller.
    Tamamlandığında arşivi OUTPUT_DIR içine yazar.
    """
    job = JOBS[job_id]

    def update(status: str = None, progress: int = None, message: str = None):
        if status is not None:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if message is not None:
            job["message"] = message

    try:
        # ── 1. Ana sayfayı indir ──────────────────────────────────────────────
        update(status="running", progress=5, message="Ana sayfa indiriliyor…")
        html_bytes, _ = fetch_url(target_url)

        if html_bytes is None:
            update(status="error", message=(
                "URL'ye erişilemedi. "
                "Adresin doğruluğunu ve sitenin erişilebilir olduğunu kontrol edin."
            ))
            return

        parsed_base = urlparse(target_url)
        domain = parsed_base.netloc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"webarchive_{domain}_{timestamp}"

        # ── 2. Varlıkları keşfet ──────────────────────────────────────────────
        update(progress=15, message="Sayfa varlıkları taranıyor…")
        asset_urls = extract_asset_urls(html_bytes, target_url)

        # Derin tarama: alt sayfaları keşfet
        subpage_urls: list[str] = []
        if deep_crawl:
            update(progress=20, message="Alt sayfalar keşfediliyor…")
            subpage_urls = discover_subpages(html_bytes, target_url)

        # ── 3. Varlıkları indir ───────────────────────────────────────────────
        all_files: dict[str, bytes] = {}   # arşiv_yolu → içerik
        asset_map: dict[str, str] = {}     # orijinal_url → yerel_yol

        total_assets = len(asset_urls)
        update(progress=22, message=f"{total_assets} varlık indiriliyor…")

        for i, asset_url in enumerate(asset_urls):
            pct = 22 + int(45 * i / max(total_assets, 1))
            filename = urlparse(asset_url).path.split("/")[-1][:40] or "?"
            update(progress=pct, message=f"İndiriliyor: {filename}")

            content, _ = fetch_url(asset_url)
            if content is None:
                continue

            local_path = safe_local_path(asset_url, i)
            all_files[local_path] = content
            asset_map[asset_url] = local_path

        # ── 4. Alt sayfaları indir (derin tarama) ────────────────────────────
        subpage_html_map: dict[str, bytes] = {}
        for j, sp_url in enumerate(subpage_urls):
            pct = 67 + int(12 * j / max(len(subpage_urls), 1))
            update(progress=pct, message=f"Alt sayfa {j+1}/{len(subpage_urls)}: {sp_url[-50:]}")

            sp_bytes, _ = fetch_url(sp_url)
            if sp_bytes:
                subpage_html_map[sp_url] = sp_bytes

        # ── 5. HTML bağlantılarını yerel yollara yeniden yaz ─────────────────
        update(progress=80, message="Bağlantılar yerelleştiriliyor…")

        main_html_rewritten = rewrite_html(html_bytes, asset_map)
        all_files["index.html"] = main_html_rewritten

        for sp_url, sp_bytes in subpage_html_map.items():
            sp_rewritten = rewrite_html(sp_bytes, asset_map)
            sp_local = "pages/" + safe_local_path(sp_url, hash(sp_url) % 9999).replace("assets/", "")
            all_files[sp_local] = sp_rewritten

        # ── 6. Arşivi oluştur ─────────────────────────────────────────────────
        update(progress=88, message=f"{output_format.upper()} arşivi oluşturuluyor…")

        if output_format == "zip":
            out_filename = archive_name + ".zip"
            out_path = OUTPUT_DIR / out_filename

            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for arc_path, data in all_files.items():
                    zf.writestr(arc_path, data)

        else:  # tar.gz
            out_filename = archive_name + ".tar.gz"
            out_path = OUTPUT_DIR / out_filename

            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tf:
                for arc_path, data in all_files.items():
                    info = tarfile.TarInfo(name=arc_path)
                    info.size = len(data)
                    info.mtime = int(time.time())
                    tf.addfile(info, io.BytesIO(data))
            out_path.write_bytes(buf.getvalue())

        # ── 7. Tamamlandı ─────────────────────────────────────────────────────
        file_size = out_path.stat().st_size
        update(
            status="done",
            progress=100,
            message=f"Tamamlandı! {len(all_files)} dosya arşivlendi.",
        )
        job.update({
            "filename":   out_filename,
            "filesize":   file_size,
            "file_count": len(all_files),
        })

    except Exception as exc:
        update(status="error", message=f"Beklenmeyen hata: {exc}")


# ─── Flask Route'ları ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Ana sayfa — web arayüzü."""
    return render_template("index.html")


@app.route("/api/backup", methods=["POST"])
def start_backup():
    """
    Yeni bir yedekleme işi başlatır.
    Body: { "url": str, "format": "zip"|"tar.gz", "deep": bool }
    Döndürür: { "job_id": str }
    """
    data = request.get_json(force=True)
    url    = (data.get("url") or "").strip()
    fmt    = data.get("format", "zip").lower()
    deep   = bool(data.get("deep", False))

    # URL normalleştirme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if fmt not in ("zip", "tar.gz"):
        fmt = "zip"

    job_id = hashlib.md5(f"{url}{time.time()}".encode()).hexdigest()[:12]
    JOBS[job_id] = {
        "status":     "queued",
        "progress":   0,
        "message":    "Sıraya alındı…",
        "filename":   None,
        "filesize":   0,
        "file_count": 0,
    }

    thread = threading.Thread(
        target=run_backup,
        args=(job_id, url, deep, fmt),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def job_status(job_id: str):
    """
    İş durumunu sorgular.
    Döndürür: { status, progress, message, filename, filesize, file_count }
    """
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "İş bulunamadı"}), 404
    return jsonify(job)


@app.route("/api/download/<job_id>")
def download_archive(job_id: str):
    """Tamamlanmış arşivi indirir."""
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "Arşiv hazır değil"}), 404

    filename = job["filename"]
    path = OUTPUT_DIR / filename
    if not path.exists():
        return jsonify({"error": "Dosya bulunamadı"}), 404

    mimetype = "application/zip" if filename.endswith(".zip") else "application/gzip"
    return send_file(
        path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename,
    )


# ─── Başlangıç ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  WebArchiver başlatılıyor…")
    print("  Tarayıcıda aç: http://localhost:5000")
    print("  Durdurmak için: Ctrl+C")
    print("=" * 55)
    app.run(debug=False, host="0.0.0.0", port=5000)
