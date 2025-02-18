from auth import Auth
from users import UserManager
from region_manager import RegionManager
from db_config import init_database

## Classe principale de l'application
## Cette classe contient des méthodes pour afficher le menu, gérer les régions, et exécuter l'application
class Application: # Classe Application
    def __init__(self): # Constructeur de la classe Application 
        # Création d'instances des classes Auth, UserManager et RegionManager
        self.auth = Auth() # Création d'une instance de la classe Auth
        self.user_manager = UserManager(self.auth) # Création d'une instance de la classe UserManager
        self.region_manager = RegionManager(self.auth) # Création d'une instance de la classe RegionManager
        
    def afficher_menu(self): # Méthode pour afficher le menu
        """Affiche le menu selon le rôle de l'utilisateur"""
        user_info = self.auth.session_manager.get_current_user_role()
        
        print("\n=== Outil de Gestion des Utilisateurs ===")
        print("1. Ajouter un utilisateur")
        print("2. Modifier un utilisateur")
        print("3. Supprimer un utilisateur")
        print("4. Afficher la liste des utilisateurs")
        print("5. Réinitialiser un mot de passe")
        
        if user_info['role'] == 'super_admin':
            print("Extensions pour le super admin:")
            print("6. Créer les administrateurs régionaux")
            print("7. Gérer les régions")
        
        print("D. Déconnexion")
        print("Q. Quitter")
        
        return input("\nVotre choix : ").upper()
        
    def gerer_regions(self): # Méthode pour gérer les régions
        """Sous-menu pour la gestion des régions"""
        while True:
            print("\n=== Gestion des Régions ===")
            print("1. Ajouter une région")
            print("2. Supprimer une région")
            print("3. Lister les régions")
            print("4. Transférer les utilisateurs")
            print("R. Retour au menu principal")
            
            choix = input("\nVotre choix : ").upper()
            
            if choix == '1':
                nom_region = input("Nom de la nouvelle région : ")
                self.region_manager.ajouter_region(nom_region)
                
            elif choix == '2':
                nom_region = input("Nom de la région à supprimer : ")
                self.region_manager.supprimer_region(nom_region)
                
            elif choix == '3':
                self.region_manager.lister_regions()
                
            elif choix == '4':
                region_source = input("Région source : ")
                region_cible = input("Région cible : ")
                self.region_manager.transferer_utilisateurs(region_source, region_cible)
                
            elif choix == 'R':
                break
            else:
                print("❌ Choix invalide")

    def executer(self): # Méthode pour exécuter l'application
        """Point d'entrée principal de l'application"""
        print("=== Initialisation du système ===")
        if not init_database():
            print("❌ Erreur d'initialisation de la base de données")
            return
            
        self.auth.creer_super_admin()
        
        while True:
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
                    self.gerer_regions()
                
                elif choix == 'D':
                    self.auth.deconnexion()
                
                elif choix == 'Q':
                    print("Au revoir!")
                    break
                
                else:
                    print("❌ Choix invalide")
                
            except Exception as e:
                print(f"❌ Une erreur est survenue: {str(e)}")

def main(): # Fonction principale
    app = Application() # Création d'une instance de la classe Application
    app.executer() 

if __name__ == "__main__": # Point d'entrée du programme
    main()