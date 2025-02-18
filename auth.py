import hashlib
import random
import string
from datetime import datetime, timedelta
from db_config import get_connection
from session_manager import SessionManager
from mysql.connector import Error

# Classe pour gérer l'authentification et les autorisations
## Cette classe contient des méthodes pour créer les admin, générer des mots de passe,
## hasher les mots de passe, vérifier les autorisations, etc.
## Elle utilise la classe SessionManager pour gérer les sessions utilisateur.
## Elle utilise également la classe get_connection pour se connecter à la base de données.
## Elle utilise la classe Error pour gérer les erreurs de connexion.
## Self fait reference à une instance spécifique de la classe Auth.
class Auth:
    def __init__(self): # Constructeur qui permet de créer une instance de SessionManager et une liste de régions
        self.session_manager = SessionManager() # Création d'une instance de SessionManager
        self.regions = ['Rennes', 'Strasbourg', 'Nantes', 'Grenoble'] # Liste des régions

    def generer_mot_de_passe(self, longueur=12): # Méthode pour générer un mot de passe
        """Génère un mot de passe aléatoire avec des critères de complexité""" # Commentaire de la méthode
        lettres = string.ascii_letters
        chiffres = string.digits
        symboles = "!@#$%^&*"
        
        mot_de_passe = [
            random.choice(lettres.lower()),
            random.choice(lettres.upper()),
            random.choice(chiffres),
            random.choice(symboles)
        ]
        
        caracteres = lettres + chiffres + symboles
        for _ in range(longueur - 4):
            mot_de_passe.append(random.choice(caracteres))
        
        random.shuffle(mot_de_passe)
        return ''.join(mot_de_passe)

    def hasher_mot_de_passe(self, mot_de_passe): # Méthode pour hasher un mot de passe
        """Hash le mot de passe avec SHA-256"""
        return hashlib.sha256(mot_de_passe.encode()).hexdigest()

    def creer_super_admin(self): # Méthode pour créer un super admin
        """Crée le super administrateur s'il n'existe pas"""
        conn = get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM utilisateurs WHERE role = 'super_admin'")
            if cursor.fetchone():
                return None

            mot_de_passe = self.generer_mot_de_passe()
            hash_mdp = self.hasher_mot_de_passe(mot_de_passe)
            expiration = datetime.now() + timedelta(days=90)

            cursor.execute("""
                INSERT INTO utilisateurs (nom, prenom, login, role, region, password, expiration)
                VALUES ('Super', 'Admin', 'sadmin', 'super_admin', 'Paris', %s, %s)
            """, (hash_mdp, expiration))
            
            conn.commit()
            print(f"✅ Super administrateur créé avec succès!")
            print(f"🔑 Login: sadmin")
            print(f"🔒 Mot de passe: {mot_de_passe}")
            return mot_de_passe

        except Error as e:
            print(f"❌ Erreur lors de la création du super admin: {e}")
            return None

        finally:
            conn.close()

    def creer_admins_regionaux(self): # Méthode pour créer les admins régionaux
        """Crée automatiquement les 4 administrateurs régionaux"""
        if not self.session_manager.current_user:
            print("❌ Vous devez être connecté en tant que super admin pour cette opération.")
            return

        user_info = self.session_manager.get_current_user_role()
        if not user_info or user_info['role'] != 'super_admin':
            print("❌ Seul le super admin peut créer les administrateurs régionaux.")
            return

        conn = get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor(dictionary=True)
            admins_crees = []

            for region in self.regions:
                cursor.execute("""
                    SELECT * FROM utilisateurs 
                    WHERE role = 'admin' AND region = %s
                """, (region,))
                
                if not cursor.fetchone(): # Si l'admin n'existe pas, on le créera
                    mot_de_passe = self.generer_mot_de_passe()
                    hash_mdp = self.hasher_mot_de_passe(mot_de_passe)
                    expiration = datetime.now() + timedelta(days=90)
                    login = f"admin{region.lower()[:3]}"

                    cursor.execute("""
                        INSERT INTO utilisateurs 
                        (nom, prenom, login, role, region, password, createur, expiration)
                        VALUES ('Admin', %s, %s, 'admin', %s, %s, %s, %s)
                    """, (region, login, region, hash_mdp, 'sadmin', expiration))

                    admins_crees.append({
                        'region': region,
                        'login': login,
                        'password': mot_de_passe
                    })

            conn.commit()

            if admins_crees:
                print("\n✅ Administrateurs régionaux créés avec succès!")
                for admin in admins_crees:
                    print(f"\n📍 Région: {admin['region']}")
                    print(f"🔑 Login: {admin['login']}")
                    print(f"🔒 Mot de passe: {admin['password']}")
            else:
                print("\n📝 Tous les administrateurs régionaux sont déjà créés.")

        except Error as e:
            print(f"❌ Erreur lors de la création des admins régionaux: {e}")

        finally:
            conn.close()

    def connexion(self): # Méthode pour gérer la connexion d'un utilisateur
        """Gère la connexion d'un utilisateur"""
        login = input("🔑 Login : ")
        mot_de_passe = input("🔒 Mot de passe : ")

        conn = get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT tentatives, derniere_tentative 
                FROM tentatives_connexion 
                WHERE login = %s
            """, (login,))
            
            tentatives = cursor.fetchone()
            if tentatives and tentatives['tentatives'] >= 3:
                if datetime.now() - tentatives['derniere_tentative'] < timedelta(minutes=15):
                    print("❌ Compte temporairement bloqué. Réessayez dans 15 minutes.")
                    return False

            cursor.execute("""
                SELECT * FROM utilisateurs 
                WHERE login = %s AND expiration > NOW()
            """, (login,))
            
            user = cursor.fetchone()
            if user and self.hasher_mot_de_passe(mot_de_passe) == user['password']:
                cursor.execute("""
                    INSERT INTO tentatives_connexion (login, tentatives, derniere_tentative)
                    VALUES (%s, 0, NOW())
                    ON DUPLICATE KEY UPDATE tentatives = 0, derniere_tentative = NOW()
                """, (login,))
                
                session_token = self.session_manager.create_session(login)
                if session_token:
                    print(f"✅ Connexion réussie ! Bienvenue, {user['prenom']} {user['nom']}.")
                    if user['role'] == 'super_admin':
                        print("🌟 Vous êtes connecté en tant que Super Administrateur.")
                    elif user['role'] == 'admin':
                        print(f"👨‍💼 Vous êtes administrateur de la région {user['region']}.")
                    return True
            else:
                cursor.execute("""
                    INSERT INTO tentatives_connexion (login, tentatives, derniere_tentative)
                    VALUES (%s, 1, NOW())
                    ON DUPLICATE KEY UPDATE 
                    tentatives = tentatives + 1,
                    derniere_tentative = NOW()
                """, (login,))
                
                print("❌ Identifiants incorrects!")
                return False

            conn.commit()

        except Error as e:
            print(f"❌ Erreur lors de la connexion: Compte temporairement bloqué. Réessayez dans 15 minutes ou {e}")
            return False

        finally:
            conn.close()

    def deconnexion(self):
        """Déconnecte l'utilisateur actuel"""
        self.session_manager.end_session()
        print("👋 Vous avez été déconnecté avec succès.")

    def verifier_autorisation(self, region=None): # Méthode pour vérifier les autorisations
        """Vérifie si l'utilisateur actuel a les droits nécessaires pour une région"""
        if not self.session_manager.is_session_valid(): # Si la session n'est pas valide, on retourne False
            return False

        user_info = self.session_manager.get_current_user_role() # On récupère les informations de l'utilisateur actuel
        if not user_info:
            return False

        if user_info['role'] == 'super_admin': # Si l'utilisateur est un super admin, on retourne True
            return True

        if user_info['role'] == 'admin':
            return region is None or region == user_info['region'] # Si l'utilisateur est un admin, on vérifie la région

        return False