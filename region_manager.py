# region_manager.py
from mysql.connector import Error
from db_config import get_connection
from validators import DataValidator

class RegionManager:
    def __init__(self, auth):
        self.auth = auth
        self.validator = DataValidator()
        
    def ajouter_region(self, nom_region):
        """Ajoute une nouvelle région"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return False
            
        current_user = self.auth.session_manager.get_current_user_role()
        if current_user['role'] != 'super_admin':
            print("❌ Seul le super admin peut gérer les régions.")
            return False
            
        # Validation du nom de la région
        valide, message = self.validator.valider_nom(nom_region)
        if not valide:
            print(f"❌ {message}")
            return False
            
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Ajouter la nouvelle région à l'énumération
            cursor.execute("""
                ALTER TABLE utilisateurs 
                MODIFY COLUMN region ENUM('Paris', 'Rennes', 'Strasbourg', 'Grenoble', 'Nantes', %s)
            """, (nom_region,))
            
            conn.commit()
            print(f"✅ Région {nom_region} ajoutée avec succès!")
            return True
            
        except Error as e:
            print(f"❌ Erreur lors de l'ajout de la région: {e}")
            return False
            
        finally:
            conn.close()
            
    def supprimer_region(self, nom_region):
        """Supprime une région si elle n'a pas d'utilisateurs"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return False
            
        current_user = self.auth.session_manager.get_current_user_role()
        if current_user['role'] != 'super_admin':
            print("❌ Seul le super admin peut gérer les régions.")
            return False
            
        if nom_region == 'Paris':
            print("❌ Impossible de supprimer la région du siège social (Paris).")
            return False
            
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Vérifier s'il y a des utilisateurs dans cette région
            cursor.execute("SELECT COUNT(*) FROM utilisateurs WHERE region = %s", (nom_region,))
            if cursor.fetchone()[0] > 0:
                print("❌ Impossible de supprimer une région qui contient des utilisateurs.")
                return False
                
            # Supprimer la région de l'énumération
            cursor.execute("""
                ALTER TABLE utilisateurs 
                MODIFY COLUMN region ENUM('Paris', 'Rennes', 'Strasbourg', 'Grenoble', 'Nantes')
            """)
            
            conn.commit()
            print(f"✅ Région {nom_region} supprimée avec succès!")
            return True
            
        except Error as e:
            print(f"❌ Erreur lors de la suppression de la région: {e}")
            return False
            
        finally:
            conn.close()
            
    def lister_regions(self):
        """Liste toutes les régions disponibles"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return
            
        conn = get_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            
            # Récupérer les statistiques par région
            cursor.execute("""
                SELECT 
                    region,
                    COUNT(*) as total_users,
                    SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as total_admins,
                    SUM(CASE WHEN role = 'utilisateur' THEN 1 ELSE 0 END) as total_regular_users
                FROM utilisateurs
                GROUP BY region
                ORDER BY region
            """)
            
            regions = cursor.fetchall()
            
            print("\n📍 Statistiques par région:")
            for region in regions:
                print(f"""
Région: {region[0]}
└── Utilisateurs: {region[1]}
    ├── Administrateurs: {region[2]}
    └── Utilisateurs standards: {region[3]}
""")
                
        except Error as e:
            print(f"❌ Erreur lors de la récupération des régions: {e}")
            
        finally:
            conn.close()
            
    def transferer_utilisateurs(self, region_source, region_cible):
        """Transfère tous les utilisateurs d'une région à une autre"""
        if not self.auth.session_manager.is_session_valid():
            print("❌ Vous devez être connecté pour effectuer cette action.")
            return False
            
        current_user = self.auth.session_manager.get_current_user_role()
        if current_user['role'] != 'super_admin':
            print("❌ Seul le super admin peut transférer des utilisateurs entre régions.")
            return False
            
        # Validation des régions
        valide, message = self.validator.valider_region(region_source)
        if not valide:
            print(f"❌ Région source invalide: {message}")
            return False
            
        valide, message = self.validator.valider_region(region_cible)
        if not valide:
            print(f"❌ Région cible invalide: {message}")
            return False
            
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Mettre à jour la région des utilisateurs
            cursor.execute("""
                UPDATE utilisateurs 
                SET region = %s 
                WHERE region = %s
            """, (region_cible, region_source))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ {cursor.rowcount} utilisateurs transférés de {region_source} vers {region_cible}!")
                return True
            else:
                print(f"ℹ️ Aucun utilisateur à transférer depuis {region_source}.")
                return False
                
        except Error as e:
            print(f"❌ Erreur lors du transfert des utilisateurs: {e}")
            return False
            
        finally:
            conn.close()