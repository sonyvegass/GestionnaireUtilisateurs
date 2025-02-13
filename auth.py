# auth.py
import hashlib
import random
import string
from datetime import datetime, timedelta
from db_config import get_connection
from session_manager import SessionManager
from mysql.connector import Error

class Auth:
    def __init__(self):
        self.session_manager = SessionManager()
        self.regions = ['Rennes', 'Strasbourg', 'Nantes', 'Grenoble']

    def generer_mot_de_passe(self, longueur=12):
        """Génère un mot de passe aléatoire avec des critères de complexité"""
        lettres = string.ascii_letters
        chiffres = string.digits
        symboles = "!@#$%^&*"
        
        # Au moins un de chaque catégorie
        mot_de_passe = [
            random.choice(lettres.lower()),
            random.choice(lettres.upper()),
            random.choice(chiffres),
            random.choice(symboles)
        ]
        
        # Compléter avec des caractères aléatoires
        caracteres = lettres + chiffres + symboles
        for _ in range(longueur - 4):
            mot_de_passe.append(random.choice(caracteres))
        
        # Mélanger le mot de passe
        random.shuffle(mot_de_passe)
        return ''.join(mot_de_passe)

    def hasher_mot_de_passe(self, mot_de_passe):
        """Hash le mot de passe avec SHA-256"""
        return hashlib.sha256(mot_de_passe.encode()).hexdigest()

    def creer_super_admin(self):
        """Crée le super administrateur s'il n'existe pas"""
        conn = get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Vérifier si le super admin existe déjà
            cursor.execute("SELECT * FROM utilisateurs WHERE role = 'super_admin'")
            if cursor.fetchone():
                return None

            # Créer le super admin
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

    def creer_admins_regionaux(self):
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
                # Vérifier si un admin existe déjà pour cette région
                cursor.execute("""
                    SELECT * FROM utilisateurs 
                    WHERE role = 'admin' AND region = %s
                """, (region,))
                
                if not cursor.fetchone():
                    mot_de_passe = self.generer_mot_de_passe()
                    hash_mdp = self.hasher_mot_de_passe(mot_de_passe)
                    expiration = datetime.now() + timedelta(days=90)
                    login = f"admin{region.lower()[:3]}"  # Exemple: adminren pour Rennes

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

    def connexion(self):
        """Gère la connexion d'un utilisateur"""
        login = input("🔑 Login : ")
        mot_de_passe = input("🔒 Mot de passe : ")

        conn = get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Vérifier les tentatives de connexion
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

            # Vérifier les identifiants
            cursor.execute("""
                SELECT * FROM utilisateurs 
                WHERE login = %s AND expiration > NOW()
            """, (login,))
            
            user = cursor.fetchone()
            if user and self.hasher_mot_de_passe(mot_de_passe) == user['password']:
                # Réinitialiser les tentatives
                cursor.execute("""
                    INSERT INTO tentatives_connexion (login, tentatives, derniere_tentative)
                    VALUES (%s, 0, NOW())
                    ON DUPLICATE KEY UPDATE tentatives = 0, derniere_tentative = NOW()
                """, (login,))
                
                # Créer une session
                session_token = self.session_manager.create_session(login)
                if session_token:
                    print(f"✅ Connexion réussie ! Bienvenue, {user['prenom']} {user['nom']}.")
                    if user['role'] == 'super_admin':
                        print("🌟 Vous êtes connecté en tant que Super Administrateur.")
                    elif user['role'] == 'admin':
                        print(f"👨‍💼 Vous êtes administrateur de la région {user['region']}.")
                    return True
            else:
                # Incrémenter les tentatives
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
            print(f"❌ Erreur lors de la connexion: {e}")
            return False

        finally:
            conn.close()

    def deconnexion(self):
        """Déconnecte l'utilisateur actuel"""
        self.session_manager.end_session()
        print("👋 Vous avez été déconnecté avec succès.")

    def verifier_autorisation(self, region=None):
        """Vérifie si l'utilisateur actuel a les droits nécessaires pour une région"""
        if not self.session_manager.is_session_valid():
            return False

        user_info = self.session_manager.get_current_user_role()
        if not user_info:
            return False

        # Super admin peut tout faire
        if user_info['role'] == 'super_admin':
            return True

        # Admin régional ne peut gérer que sa région
        if user_info['role'] == 'admin':
            return region is None or region == user_info['region']

        return False