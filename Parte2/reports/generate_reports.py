import os
import io
import csv
import argparse
import datetime
from collections import defaultdict

# Gráficas (sin UI)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ================= utilidades =================

def pct(n, d):
    return (100.0 * n / d) if d else 0.0

def parse_bool(x):
    s = str(x).strip().lower() if x is not None else ""
    return s in ("1", "true", "yes", "y", "si", "sí")

def parse_int(x, default=None):
    try:
        return int(x)
    except Exception:
        return default

def parse_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def read_csv_rows_utf8(path):
    rows = []
    if not os.path.isfile(path):
        return rows

    with open(path, "rb") as fb:
        data = fb.read()

    # permitir BOM
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as e:
        raise SystemExit(
            f"Archivo NO es UTF-8: {path}\n"
            f"Regrábalo como UTF-8. Detalle: {e}"
        )

    # detectar delimitador
    try:
        dialect = csv.Sniffer().sniff(text[:8192])
    except csv.Error:
        dialect = csv.excel

    f = io.StringIO(text)
    reader = csv.DictReader(f, dialect=dialect)
    return list(reader)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)
    return p

# Paleta consistente por algoritmo/categoría
PALETTE = {
    "hamming": "#4C78A8",   
    "crc":     "#F58518",   
    "fletcher":"#54A24B",   
    "fix":     "#54A24B",   
    "no_fix":  "#E45756",   
    "_default":"#6C757D",   
}

def color_for_algo(name: str) -> str:
    return PALETTE.get((name or "").lower(), PALETTE["_default"])

def save_chart(fig, out_dir, filename):
    path = os.path.join(out_dir, filename)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return filename

# ================ principal ===================

def main():
    ap = argparse.ArgumentParser(description="Genera resúmenes y gráficas a partir de client_report.csv, server_report.csv y errors.csv")
    ap.add_argument("--in",  dest="in_dir",  default=os.getcwd(), help="Carpeta de entrada donde están los CSV")
    ap.add_argument("--out", dest="out_dir", default=os.path.join(os.getcwd(), "reports", "out"), help="Carpeta base de salida")
    ap.add_argument("--stamp", action="store_true", help="Escribir en subcarpeta con timestamp para no sobreescribir")
    ap.add_argument("--run-id", dest="run_id", default="", help="Etiqueta opcional para la corrida (apéndice del folder si usas --stamp)")
    args = ap.parse_args()

    in_dir  = os.path.abspath(args.in_dir)
    out_dir = os.path.abspath(args.out_dir)

    if args.stamp:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{args.run_id}" if args.run_id else ""
        out_dir = os.path.join(out_dir, f"{stamp}{suffix}")
    ensure_dir(out_dir)

    # ---- leer CSVs (UTF-8 estricto) ----
    client_path = os.path.join(in_dir, "client_report.csv")
    server_path = os.path.join(in_dir, "server_report.csv")
    errors_path = os.path.join(in_dir, "errors.csv")

    client = read_csv_rows_utf8(client_path)
    server = read_csv_rows_utf8(server_path)
    errors = read_csv_rows_utf8(errors_path)

    total_client = len(client)
    total_server = len(server)

    # ---- cliente: conteo por algoritmo ----
    by_algo_client = defaultdict(int)
    for r in client:
        algo = (r.get("Algoritmo") or "").lower()
        by_algo_client[algo] += 1

    # ---- server: registros, fix, success por algoritmo ----
    by_algo_server   = defaultdict(int)
    by_algo_fix      = defaultdict(int)
    by_algo_success  = defaultdict(int)
    fixes = 0
    success = 0
    for r in server:
        algo = (r.get("Algoritmo") or "").lower()
        by_algo_server[algo] += 1
        is_fix = parse_bool(r.get("Fix"))
        is_ok  = parse_bool(r.get("Success"))
        if is_fix:
            fixes += 1
            by_algo_fix[algo] += 1
        if is_ok:
            success += 1
            by_algo_success[algo] += 1

    # ---------- summary_per_algo.csv ----------
    algos = sorted(set(by_algo_client) | set(by_algo_server))
    out_summary_algo = os.path.join(out_dir, "summary_per_algo.csv")
    with open(out_summary_algo, "w", newline='', encoding="utf-8") as f:
        fn = ["Algoritmo", "TotalCliente", "RegistrosServer", "Fix", "Success", "TasaExito(%)"]
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for a in algos:
            tot_cli = by_algo_client.get(a, 0)
            tot_srv = by_algo_server.get(a, 0)
            fx = by_algo_fix.get(a, 0)
            sc = by_algo_success.get(a, 0)
            w.writerow({
                "Algoritmo": a,
                "TotalCliente": tot_cli,
                "RegistrosServer": tot_srv,
                "Fix": fx,
                "Success": sc,
                "TasaExito(%)": f"{pct(sc, tot_srv):.2f}"
            })

    # ---------- summary_by_algo_noise.csv ----------
    # join por NumMensaje para traer NoiseProb y BitsFlippeados desde el cliente
    client_by_id = {}
    for r in client:
        mid = parse_int(r.get("NumMensaje"))
        if mid is not None:
            client_by_id[mid] = r

    by_algo_noise = defaultdict(lambda: {"tot": 0, "succ": 0, "sum_flip": 0.0})
    for r in server:
        mid = parse_int(r.get("NumMensaje"))
        if mid is None:
            continue
        crow = client_by_id.get(mid)
        if not crow:
            continue
        algo = (crow.get("Algoritmo") or "").lower()
        noise = parse_float(crow.get("NoiseProb"), 0.0)
        flips = parse_float(crow.get("BitsFlippeados"), 0.0)
        by_algo_noise[(algo, noise)]["tot"] += 1
        if parse_bool(r.get("Success")):
            by_algo_noise[(algo, noise)]["succ"] += 1
        by_algo_noise[(algo, noise)]["sum_flip"] += flips or 0.0

    out_summary_noise = os.path.join(out_dir, "summary_by_algo_noise.csv")
    with open(out_summary_noise, "w", newline='', encoding="utf-8") as f:
        fn = ["Algoritmo", "NoiseProb", "Total", "Success", "TasaExito(%)", "AvgBitsFlippeados"]
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        for (algo, noise), acc in sorted(by_algo_noise.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            tot = acc["tot"]
            succ = acc["succ"]
            avgf = (acc["sum_flip"] / tot) if tot else 0.0
            w.writerow({
                "Algoritmo": algo,
                "NoiseProb": noise,
                "Total": tot,
                "Success": succ,
                "TasaExito(%)": f"{pct(succ, tot):.2f}",
                "AvgBitsFlippeados": f"{avgf:.3f}",
            })

    # -------------- GRÁFICAS (color-coded) --------------
    charts = []

    # 1) Mensajes por algoritmo (cliente)
    if by_algo_client:
        labels = sorted(by_algo_client.keys())
        values = [by_algo_client[a] for a in labels]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        bar_colors = [color_for_algo(a) for a in labels]
        ax.bar(labels, values, color=bar_colors)
        ax.set_title("Mensajes por algoritmo (cliente)")
        ax.set_xlabel("Algoritmo")
        ax.set_ylabel("Cantidad")
        ax.grid(True, axis='y', alpha=0.25)
        charts.append(save_chart(fig, out_dir, "chart_client_msgs_per_algo.png"))

    # 2) Tasa de éxito por algoritmo (server)
    if by_algo_server:
        labels = sorted(by_algo_server.keys())
        rates = [pct(by_algo_success.get(a, 0), by_algo_server.get(a, 0)) for a in labels]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        bar_colors = [color_for_algo(a) for a in labels]
        ax.bar(labels, rates, color=bar_colors)
        ax.set_title("Tasa de éxito por algoritmo (server)")
        ax.set_xlabel("Algoritmo")
        ax.set_ylabel("Éxito (%)")
        ax.grid(True, axis='y', alpha=0.25)
        charts.append(save_chart(fig, out_dir, "chart_success_rate_per_algo.png"))

    # 3) Éxito vs Probabilidad de ruido (líneas por algoritmo)
    if by_algo_noise:
        series = defaultdict(lambda: {"x": [], "y": []})
        for (algo, noise), acc in by_algo_noise.items():
            rate = pct(acc["succ"], acc["tot"])
            series[algo]["x"].append(noise or 0.0)
            series[algo]["y"].append(rate)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for algo, dat in series.items():
            pts = sorted(zip(dat["x"], dat["y"]), key=lambda t: t[0])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, marker="o", label=algo, color=color_for_algo(algo))
        ax.set_title("Éxito vs Probabilidad de ruido")
        ax.set_xlabel("NoiseProb")
        ax.set_ylabel("Éxito (%)")
        ax.grid(True, axis='both', alpha=0.25)
        ax.legend()
        charts.append(save_chart(fig, out_dir, "chart_success_vs_noise.png"))

    # 4) Promedio de bits volteados vs ruido (cliente)
    if client:
        acc = defaultdict(lambda: {"sum": 0.0, "n": 0})
        for r in client:
            algo = (r.get("Algoritmo") or "").lower()
            noise = parse_float(r.get("NoiseProb"), 0.0)
            flips = parse_float(r.get("BitsFlippeados"), 0.0) or 0.0
            key = (algo, noise)
            acc[key]["sum"] += flips
            acc[key]["n"] += 1
        series = defaultdict(lambda: {"x": [], "y": []})
        for (algo, noise), a in acc.items():
            avg = (a["sum"]/a["n"]) if a["n"] else 0.0
            series[algo]["x"].append(noise or 0.0)
            series[algo]["y"].append(avg)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for algo, dat in series.items():
            pts = sorted(zip(dat["x"], dat["y"]), key=lambda t: t[0])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, marker="o", label=algo, color=color_for_algo(algo))
        ax.set_title("Promedio de bits volteados vs ruido (cliente)")
        ax.set_xlabel("NoiseProb")
        ax.set_ylabel("Avg Bits Flipped")
        ax.grid(True, axis='both', alpha=0.25)
        ax.legend()
        charts.append(save_chart(fig, out_dir, "chart_bits_flipped_vs_noise.png"))

    # 5) Hamming: FIX vs NO_FIX (server)
    total_hamming = by_algo_server.get("hamming", 0)
    if total_hamming:
        fixes_h = by_algo_fix.get("hamming", 0)
        nofix_h = total_hamming - fixes_h
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.bar(["FIX", "NO_FIX"], [fixes_h, nofix_h],
            color=[PALETTE["fix"], PALETTE["no_fix"]])
        ax.set_title("Hamming: FIX vs NO_FIX (server)")
        ax.set_xlabel("Tipo")
        ax.set_ylabel("Cantidad")
        ax.grid(True, axis='y', alpha=0.25)
        charts.append(save_chart(fig, out_dir, "chart_hamming_fix_counts.png"))

    try:
        for src in (client_path, server_path, errors_path):
            if os.path.isfile(src):
                dst = os.path.join(out_dir, os.path.basename(src))
                with open(src, "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
    except Exception:
        pass

    # ---------- reporte MD ----------
    md_path = os.path.join(out_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as md:
        md.write("# Reporte de Pruebas\n\n")
        md.write(f"- Mensajes (cliente): **{total_client}**\n")
        md.write(f"- Registros (server): **{total_server}**\n")
        md.write(f"- Fix detectados: **{fixes}**\n")
        md.write(f"- Correcciones exitosas: **{success}** ({pct(success, total_server):.2f}%)\n\n")
        md.write("## Gráficas\n")
        for fn in charts:
            md.write(f"- {fn}\n")
        md.write("\n")
        for fn in charts:
            md.write(f"![{fn}](./{fn})\n\n")

    # ---------- log consola ----------
    print("== Resumen de pruebas ==")
    print(f"Mensajes (cliente): {total_client}")
    if by_algo_client:
        print("Por algoritmo (cliente):")
        for a in sorted(by_algo_client):
            c = by_algo_client[a]
            print(f"  - {a}: {c} ({pct(c, total_client):.2f}%)")
    print(f"\nServer (registros): {total_server}")
    print(f"  - Fix detectados: {fixes}")
    print(f"  - Correcciones exitosas: {success} ({pct(success, total_server):.2f}%)")
    if by_algo_server:
        print("  - Por algoritmo (server):")
        for a in sorted(by_algo_server):
            tot = by_algo_server[a]
            fx = by_algo_fix.get(a, 0)
            sc = by_algo_success.get(a, 0)
            print(f"    * {a}: Reg={tot}, Fix={fx}, Success={sc}, Tasa éxito={pct(sc, tot):.2f}%")

    print("\nArchivos generados:")
    print(f"  - {out_summary_algo}")
    print(f"  - {out_summary_noise}")
    print(f"  - {md_path}")
    for fn in charts:
        print(f"  - {os.path.join(out_dir, fn)}")
    print(f"\nSalida en: {out_dir}")

if __name__ == "__main__":
    main()
