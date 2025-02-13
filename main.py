# main.py
from auth import Auth
from users import UserManager
from db_config import init_database

class Application:
    def __init__(self):
        self.auth = Auth()
        self.user_manager = UserManager(self.auth)
        
    def afficher_menu(self):
        """Affiche le menu selon le rôle de l'utilisateur"""
        user_info = self.auth.session_manager.get_current_user_role()
        
        print("\n=== Outil de Gestion des Utilisateurs ===")
        print("1. Ajouter un utilisateur")
        print("2. Modifier un utilisateur")
        print("3. Supprimer un utilisateur")
        print("4. Afficher la liste des utilisateurs")
        print("5. Réinitialiser un mot de passe")
        
        if user_info['role'] == 'super_admin':
            print("6. Créer les administrateurs régionaux")
            print("7. Gérer les régions")
        
        print("D. Déconnexion")
        print("Q. Quitter")
        
        return input("\nVotre choix : ").upper()

    def executer(self):
        """Point d'entrée principal de l'application"""
        print("=== Initialisation du système ===")
        if not init_database():
            print("❌ Erreur d'initialisation de la base de données")
            return
            
        # Création du super admin si nécessaire
        self.auth.creer_super_admin()
        
        while True:
            # Si pas de session active, demander connexion
            if not self.auth.session_manager.is_session_valid():
                print("\n🔒 Connexion requise")
                print("1. Se connecter")
                print("Q. Quitter")
                choix = input("\nVotre choix : ").upper()
                
                if choix == '1':
                    if not self.auth.connexion():
                        continue
                elif choix == 'Q':
                    break
                else:
                    print("❌ Choix invalide")
                    continue
            
            # Menu principal pour utilisateur connecté
            choix = self.afficher_menu()
            
            try:
                if choix == '1':
                    self.user_manager.ajouter_utilisateur()
                
                elif choix == '2':
                    login = input("Login de l'utilisateur à modifier : ")
                    champ = input("Champ à modifier (nom/prenom/role/region) : ")
                    valeur = input(f"Nouvelle valeur pour {champ} : ")
                    self.user_manager.modifier_utilisateur(login, {champ: valeur})
                
                elif choix == '3':
                    login = input("Login de l'utilisateur à supprimer : ")
                    self.user_manager.supprimer_utilisateur(login)
                
                elif choix == '4':
                    filtre_role = input("Filtrer par rôle (laissez vide pour tous) : ") or None
                    filtre_region = input("Filtrer par région (laissez vide pour tous) : ") or None
                    self.user_manager.afficher_utilisateurs(filtre_role, filtre_region)
                
                elif choix == '5':
                    login = input("Login de l'utilisateur : ")
                    self.user_manager.reinitialiser_mot_de_passe(login)
                
                elif choix == '6' and self.auth.session_manager.get_current_user_role()['role'] == 'super_admin':
                    self.auth.creer_admins_regionaux()
                
                elif choix == '7' and self.auth.session_manager.get_current_user_role()['role'] == 'super_admin':
                    print("\nGestion des régions non implémentée")
                
                elif choix == 'D':
                    self.auth.deconnexion()
                
                elif choix == 'Q':
                    print("Au revoir!")
                    break
                
                else:
                    print("❌ Choix invalide")
                
            except Exception as e:
                print(f"❌ Une erreur est survenue: {str(e)}")

def main():
    app = Application()
    app.executer()

if __name__ == "__main__":
    main()