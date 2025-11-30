import subprocess
import re
import csv
import matplotlib.pyplot as plt
import numpy as np
import os
import time
import asyncio
import aiohttp
import random

URL = "https://bigdatatp2025.ew.r.appspot.com/api/timeline?user=user" # URL sur laquelle faire les requêtes

async def fetch(session, url):
    """
    Fonction asynchrone pour effectuer une requête GET
    Entrée : session aiohttp, url de la requête
    Sortie : temps de réponse et code status
    """
    timeS = time.time()
    async with session.get(url) as response:
        return time.time() - timeS , response.status

async def run_fetch(n, c):
    """
    Lance c requêtes asynchrones pour récupérer le timeline de c utilisateurs aléatoires parmi n utilisateurs
    Entrée : n le nombre d'utilisateurs, c le nombre de requêtes à lancer
    Sortie : le temps moyen de réponse et le nombre de requêtes ayant échouées
    """
    async with aiohttp.ClientSession() as session:
        await fetch(session, URL + "1") # Warmup
        tasks = [fetch(session, URL+str(random.randint(1,n))) for i in range(c)]
        results = await asyncio.gather(*tasks)
    avgTime = 0
    failed = 0
    for res in results:
        avgTime += res[0]
        if res[1] != 200:
            failed += 1
    return avgTime/len(results), failed


def generate_data(users, followee, posts):
    """
    Lance une commande pour remplir la base de données
    Entrée : un entier users représentant le nombre d'utilisateurs à créer, un entier followee représentant le nombre de followee par user et un entier posts représentant le nombre de posts par user
    Sortie : la sortie de la commande
    """
    cmd = ["python", "seed.py", "--users", str(users), "--follows-min", str(followee), "--follows-max", str(followee), "--posts", str(posts)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        print(output)
        
        return output
    except FileNotFoundError:
        print("Erreur : La commande 'ab' n'est pas installée ou introuvable.")
        return None


def generate_csv_plot(data, csv_file, plot_infos):
    """
    Génère les fichiers csv et les graphiques pour une expérience donnée
    Entrée : les résultats de l'expérience, le nom du fichier csv, les infos du graphique
    """

    # Ecrit les résultats de l'experience dans le csv indiqué
    os.makedirs("out", exist_ok=True)

    full_path = os.path.join("out", csv_file)
    with open(full_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["PARAM", "AVG_TIME(ms)", "RUN", "FAILED"])
        
        for i in data:
            writer.writerow([i[0], f"{i[1]*1000:.1f}ms", i[2], i[3]])
    

    # Crée le barplot illustrant les résultats
    params = sorted(set(row[0] for row in data))
    means =[]
    stds = []

    # 
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

    plt.savefig(plot_infos[3], dpi=300)
    plt.show()

def main() :
    
    subprocess.run(["python", "reset_db.py"])

    # echelle sur la charge
    generate_data(1000,20,50000)
    nb_users = [1,10,20,50,100,1000]
    res = []
    for nb in nb_users:
        for i in range(3):
            run_res = asyncio.run(run_fetch(1000, nb))
            res.append([nb,run_res[0],i,run_res[1],nb])
    generate_csv_plot(res, "conc.csv", ["Nombre d'utilisateurs concurrents","Temps moyen par requête (s)","Temps moyen par requête selon la concurrence","conc.png"])

    # echelle sur le nombre de posts
    res = []
    nb_posts = [10,100,1000]
    actual_posts = 0
    subprocess.run(["python", "reset_db.py"])
    for nb in nb_posts :
        generate_data(50,20,50*nb-actual_posts)
        for i in range(3):
            run_res = asyncio.run(run_fetch(50,50))
            res.append([nb,run_res[0],i,run_res[1]])
        actual_posts = 50*nb
    generate_csv_plot(res, "posts.csv", ["Nombre de posts par utilisateur","Temps moyen par requête (s)","Temps moyen par requête selon le nombre de posts","posts.png"])

    # echelle sur le nombre de followee
    res = []
    nb_followee = [10,50,100]
    subprocess.run(["python", "reset_db.py"])
    actual_followee = 0
    actual_posts = 0
    for nb in nb_followee :
        generate_data(150,nb-actual_followee,15000 - actual_posts)
        for i in range(3):
            run_res = asyncio.run(run_fetch(150 , 50))
            res.append([nb,run_res[0],i,run_res[1]])
        actual_followee = nb
        actual_posts = 15000
    generate_csv_plot(res, "fanout.csv", ["Nombre de followee par utilisateur","Temps moyen par requête (s)","Temps moyen par requête selon le nombre de followee","fanout.png"])

if __name__ == "__main__":
    main()
