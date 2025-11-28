import argparse
from google.cloud import datastore

"""
Script de réinitialisation (reset) pour Tiny Instagram.

Ce script permet de supprimer tout ou partie des entités stockées dans
Google Cloud Datastore du projet actuellement configuré dans gcloud
(`gcloud config get-value project`).

Usage basique : 
    python reset_db.py

Paramètres :
  --kind <KindName>   Supprime uniquement les entités de ce kind.
                      Si absent, supprime toutes les entités utilisateur.
  
  --dry-run           N'exécute aucune suppression. Montre uniquement le
                      nombre d'entités qui auraient été supprimées.
  
ATTENTION :
  Ce script modifie directement les données du Datastore du projet Google Cloud actif. Vérifiez votre configuration gcloud avant usage : gcloud config get-value project
    Utilisez --dry-run pour valider la portée de l’opération avant suppression réelle.
"""


def parse_args():
    """
    Parse les arguments de la commande
    """
    p = argparse.ArgumentParser(description="Supprime toutes les entités de Datastore pour Tiny Instagram")
    p.add_argument('--kind', type=str, default=None,
                   help="Supprime seulement les entités de ce 'kind'. Si non spécifié, supprime tout.")
    p.add_argument('--dry-run', action='store_true',
                   help="N'effectue pas la suppression, affiche seulement ce qui serait supprimé.")
    return p.parse_args()

def delete_all_entities(client: datastore.Client, kind: str | None, dry: bool):
    """
    Supprime toutes les entités de Datastore d'un type donné, ou de tous les types si aucun type n'est spécifié
    Entrée : un datastore, un type d'entités ou None, un booléen indiquant si c'est un dry run
    Sortie : le nombre d'entités supprimées
    """
    query = client.query()
    if kind:
        query.kind = kind
    
    count = 0
    keys_to_delete = []
    batch_size = 500

    for entity in query.fetch():
        # On ignore les entités des "kinds" réservés par Datastore (statistiques, etc.)
        if not kind and entity.key.kind and entity.key.kind.startswith('__'):
            continue

        keys_to_delete.append(entity.key)
        count += 1

        if not dry and len(keys_to_delete) >= batch_size:
            client.delete_multi(keys_to_delete)
            keys_to_delete = []

    if not dry and keys_to_delete: # Supprime le dernier lot
        client.delete_multi(keys_to_delete)
    return count

def main():
    args = parse_args()
    client = datastore.Client()

    print(f"[Reset DB] Démarrage de la suppression des entités.")
    if args.dry_run:
        print("[Dry-Run] Aucune suppression ne sera effectuée.")

    if args.kind:
        print(f"[Reset DB] Cible: Kind '{args.kind}'.")
    else:
        print("[Reset DB] Cible: Toutes les entités de tous les kinds.")

    deleted_count = delete_all_entities(client, args.kind, args.dry_run)
    
    print(f"[Reset DB] Nombre d'entités {'qui seraient supprimées' if args.dry_run else 'supprimées'}: {deleted_count}")
    print("[Reset DB] Terminé.")

if __name__ == '__main__':
    main()
