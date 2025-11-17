import subprocess

def run_ab(url, n, c):
    cmd = ["ab", f"-n{n}", f"-c{c}", url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        
        print("===== Résultats ApacheBench =====")
        print(output)
        
        return output

    except FileNotFoundError:
        print("Erreur : La commande 'ab' n'est pas installée ou introuvable.")
        return None


if __name__ == "__main__":
    run_ab("http://localhost:8080/api/test", n=500, c=50)