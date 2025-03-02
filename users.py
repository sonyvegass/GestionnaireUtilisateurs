from datetime import datetime, timedelta
from mysql.connector import Error
from db_config import get_connection

class UserManager: # Classe UserManager
    def __init__(self, auth): # Constructeur de la classe UserManager. Le constructeur sert à initialiser un nouvel objet de la classe.
       # Cet objet contient l'attribut auth qui est initialisé avec la valeur de l'argument auth passé lors de la création de l'objet.
        self.auth = auth # Initialisation de l'attribut auth. 
        
    def verifier_admin_unique(self, region, login_exclu=None): # Méthode pour vérifier si un admin est unique
        """Vérifie s'il existe déjà un admin dans la région donnée"""
        conn = get_connection() # Connexion à la base de données
        if not conn:
            return False

        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT COUNT(*) as count 
                FROM utilisateurs 
                WHERE role = 'admin' AND region = %s
            """
            params = [region]
            
            if login_exclu:
                query += " AND login != %s"
                params.append(login_exclu)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            return result['count'] > 0
            
        except Error as e:
            print(f"❌ Erreur lors de la vérification d'admin unique: {e}")
            return True  # En cas d'erreur, on suppose qu'il y a déjà un admin
            
        finally:
            conn.close()

    def demander_confirmation(self, message):
        """Demande une confirmation à l'utilisateur"""
        reponse = input(f"{message} (oui/non): ").lower()
        return reponse == 'oui'
        
    def ajouter_utilisateur(self):
        """Ajoute un nouvel utilisateur avec vérification des droits"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return None
            
        current_user = self.auth.session_manager.get_current_user_role()
        
        nom = input("Nom : ")
        prenom = input("Prénom : ")
        role = input("Rôle (utilisateur/admin) : ")
        region = input("Région : ")
        
        if role == "admin" and current_user['role'] != "super_admin":
            print("❌ Seul le super admin peut créer des administrateurs.")
            return None
            
        
        if current_user['role'] == "admin" and region != current_user['region']:
            print("❌ Vous ne pouvez créer des utilisateurs que pour votre région.")
            return None
            
        conn = get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor()
            
            login = (prenom[0] + nom).lower()
            mot_de_passe = self.auth.generer_mot_de_passe()
            hash_mdp = self.auth.hasher_mot_de_passe(mot_de_passe)
            expiration = datetime.now() + timedelta(days=90)
            
            cursor.execute("SELECT login FROM utilisateurs WHERE login = %s", (login,))
            if cursor.fetchone():
                print("❌ Ce login existe déjà !")
                return None
                
            cursor.execute("""
                INSERT INTO utilisateurs 
                (nom, prenom, login, role, region, password, createur, expiration)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nom, prenom, login, role, region, hash_mdp,
                self.auth.session_manager.current_user, expiration
            ))
            
            conn.commit()
            print(f"✅ Utilisateur {prenom} {nom} créé avec succès!")
            print(f"🔑 Login: {login}")
            print(f"🔒 Mot de passe initial: {mot_de_passe}")
            return mot_de_passe
            
        except Error as e:
            print(f"❌ Erreur lors de la création: {e}")
            return None
            
        finally:
            conn.close()

    def modifier_utilisateur(self, login, modifications):
        """Modifie un utilisateur avec vérification des droits et unicité d'admin"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return False
            
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM utilisateurs WHERE login = %s", (login,))
            utilisateur = cursor.fetchone()
            
            if not utilisateur:
                print("❌ Utilisateur non trouvé!")
                return False
                
            current_user = self.auth.session_manager.get_current_user_role()
            if current_user['role'] == 'admin':
                if utilisateur['region'] != current_user['region']:
                    print("❌ Vous ne pouvez modifier que les utilisateurs de votre région.")
                    return False
                if 'role' in modifications and modifications['role'] == 'admin':
                    print("❌ Vous ne pouvez pas promouvoir un utilisateur en admin.")
                    return False

            # Vérification pour l'unicité d'admin lors d'un changement de rôle ou de région
            if ('role' in modifications and modifications['role'] == 'admin') or \
               ('region' in modifications and modifications['region'] != utilisateur['region']):
                region = modifications.get('region', utilisateur['region'])
                if self.verifier_admin_unique(region, login):
                    print(f"❌ Il existe déjà un administrateur pour la région {region}.")
                    return False
                    
            champs_autorises = ['nom', 'prenom', 'role', 'region']
            updates = []
            values = []
            
            for champ, valeur in modifications.items():
                if champ in champs_autorises:
                    updates.append(f"{champ} = %s")
                    values.append(valeur)
                    
            if not updates:
                print("❌ Aucune modification valide spécifiée.")
                return False
                
            values.append(login)
            query = f"UPDATE utilisateurs SET {', '.join(updates)} WHERE login = %s"
            
            cursor.execute(query, values)
            conn.commit()
            
            print(f"✅ Utilisateur {login} modifié avec succès!")
            return True
            
        except Error as e:
            print(f"❌ Erreur lors de la modification: {e}")
            return False
            
        finally:
            conn.close()

    def supprimer_utilisateur(self, login):
        """Supprime un utilisateur avec vérification des droits et confirmation"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return False
            
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM utilisateurs WHERE login = %s", (login,))
            utilisateur = cursor.fetchone()
            
            if not utilisateur:
                print("❌ Utilisateur non trouvé!")
                return False
                
            current_user = self.auth.session_manager.get_current_user_role()
            if current_user['role'] == 'admin':
                if utilisateur['region'] != current_user['region']:
                    print("❌ Vous ne pouvez supprimer que les utilisateurs de votre région.")
                    return False
                if utilisateur['role'] == 'admin':
                    print("❌ Vous ne pouvez pas supprimer un autre administrateur.")
                    return False
                    
            if utilisateur['role'] == 'super_admin':
                print("❌ Impossible de supprimer le super admin!")
                return False

            # Demande de confirmation avec détails de l'utilisateur
            message = f"""
⚠️ Vous êtes sur le point de supprimer l'utilisateur suivant :
- Nom: {utilisateur['prenom']} {utilisateur['nom']}
- Login: {utilisateur['login']}
- Rôle: {utilisateur['role']}
- Région: {utilisateur['region']}

Êtes-vous sûr de vouloir continuer ?"""

            if not self.demander_confirmation(message):
                print("❌ Suppression annulée.")
                return False
                
            cursor.execute("DELETE FROM utilisateurs WHERE login = %s", (login,))
            conn.commit()
            
            print(f"✅ Utilisateur {login} supprimé avec succès!")
            return True
            
        except Error as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False
            
        finally:
            conn.close()

    def afficher_utilisateurs(self, filtre_role=None, filtre_region=None):
        """Affiche la liste des utilisateurs avec filtres"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return
            
        conn = get_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = "SELECT * FROM utilisateurs WHERE 1=1"
            params = []
            
            current_user = self.auth.session_manager.get_current_user_role()
            if current_user['role'] == 'admin':
                query += " AND region = %s"
                params.append(current_user['region'])
                
            if filtre_role:
                query += " AND role = %s"
                params.append(filtre_role)
                
            if filtre_region:
                query += " AND region = %s"
                params.append(filtre_region)
                
            cursor.execute(query, params)
            utilisateurs = cursor.fetchall()
            
            if not utilisateurs:
                print("📂 Aucun utilisateur trouvé.")
                return
                
            print("\n📋 Liste des utilisateurs :")
            for user in utilisateurs:
                print(f"""
- {user['prenom']} {user['nom']}
  Login: {user['login']}
  Rôle: {user['role']}
  Région: {user['region'] or 'Non définie'}
  Expiration: {user['expiration']}
""")
                
        except Error as e:
            print(f"❌ Erreur lors de la récupération des utilisateurs: {e}")
            
        finally:
            conn.close()

    def reinitialiser_mot_de_passe(self, login):
        """Réinitialise le mot de passe d'un utilisateur"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return None
            
        conn = get_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM utilisateurs WHERE login = %s", (login,))
            utilisateur = cursor.fetchone()
            
            if not utilisateur:
                print("❌ Utilisateur non trouvé!")
                return None
                
            current_user = self.auth.session_manager.get_current_user_role()
            if current_user['role'] == 'admin' and utilisateur['region'] != current_user['region']:
                print("❌ Vous ne pouvez réinitialiser que les mots de passe des utilisateurs de votre région.")
                return None
                
            nouveau_mdp = self.auth.generer_mot_de_passe()
            hash_mdp = self.auth.hasher_mot_de_passe(nouveau_mdp)
            expiration = datetime.now() + timedelta(days=90)
            
            cursor.execute("""
                UPDATE utilisateurs 
                SET password = %s, expiration = %s 
                WHERE login = %s
            """, (hash_mdp, expiration, login))
            
            conn.commit()
            
            print(f"✅ Mot de passe réinitialisé pour {login}")
            print(f"🔒 Nouveau mot de passe: {nouveau_mdp}")
            return nouveau_mdp
            
        except Error as e:
            print(f"❌ Erreur lors de la réinitialisation du mot de passe: {e}")
            return None
            
        finally:
            conn.close()