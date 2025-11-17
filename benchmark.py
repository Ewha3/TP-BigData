import subprocess
import re
import csv
import matplotlib.pyplot as plt
import numpy as np
import os

def parse_hey_output(n , output):
    """Extrait les métriques utiles de la sortie hey."""

    avg = re.search(r"Average:\s+([\d\.]+) secs?", output)

    if avg:
        avg_time = float(avg.group(1))
    status_200 = re.search(r"\[200\]\s+(\d+)", output)
    if status_200:
        successful_requests = int(status_200.group(1))
    else:
        successful_requests = 0
    failed_requests = n - successful_requests

    return avg_time,failed_requests


def run_hey(url, n, c):
    """Lance hey et retourne un dict structuré."""
    cmd = ["hey", "-n", str(n), "-c", str(c), url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout

        metrics = parse_hey_output(n , output)

        return metrics

    except FileNotFoundError:
        print("Erreur : La commande 'hey' n'est pas installée ou introuvable.")
        return None

def generate_data(users, followee, posts):
    cmd = ["python", "seed.py", "--users", str(users), "--follows-min", str(followee), "--follows-max", str(followee), "--posts", str(posts)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        print("===== Résultats ApacheBench =====")
        print(output)
        
        return output
    except FileNotFoundError:
        print("Erreur : La commande 'ab' n'est pas installée ou introuvable.")
        return None

def generate_csv_plot(data, csv_file, plot_infos):
    #csv
    os.makedirs("csv", exist_ok=True)

    # Chemin complet du fichier CSV
    full_path = os.path.join("csv", csv_file)
    with open(full_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["PARAM", "AVG_TIME(ms)", "RUN", "FAILED"])
        
        for i in data:
            writer.writerow([i[0], f"{i[1]*1000:.1f}ms", i[2], i[3]])
    

    #plot
    params = sorted(set(row[0] for row in data))
    means =[]
    stds = []

    for p in params:
        times = [row[1] for row in data if row[0] == p]
        means.append(np.mean(times))
        stds.append(np.std(times))

    plt.figure(figsize=(8,5))
    plt.bar([str(p) for p in params], means, yerr=stds)
    plt.xlabel(plot_infos[0])
    plt.ylabel(plot_infos[1])
    plt.title(plot_infos[2])
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    os.makedirs("plot", exist_ok=True)
    full_path = os.path.join("plot", plot_infos[3])
    plt.savefig(full_path, dpi=300)
    plt.show()

if __name__ == "__main__":
    subprocess.run(["python", "reset_db.py"])

    generate_data(1000,20,50000)

    # echelle sur la charge
    nb_users = [1,10,20,50,100,1000]
    res = []
    for nb in nb_users:
        for i in range(3):
            run_res = run_hey("https://bigdatatp2025.ew.r.appspot.com/api/timeline?user=user1&limit=20", n=nb, c=nb)
            res.append([nb,run_res[0],i,run_res[1],nb])
    generate_csv_plot(res, "conc.csv", ["Nombre d'utilisateurs concurrents","Temps moyen par requête (s)","Temps moyen par requête selon la concurrence","conc.png"])

    res = []
    nb_posts = [10,100,1000]
    actual = 0
    for nb in nb_posts :
        generate_data(50,20,50*nb-actual)
        for i in range(3):
            run_res = run_hey("https://bigdatatp2025.ew.r.appspot.com/api/timeline?user=user1&limit=20", n=50, c=50)
            res.append([nb,run_res[0],i,run_res[1]])
        actual = 50*nb
        print(res)
        subprocess.run(["python", "reset_db.py"])
    generate_csv_plot(res, "posts.csv", ["Nombre de posts par utilisateur","Temps moyen par requête (s)","Temps moyen par requête selon le nombre de posts","posts.png"])

    