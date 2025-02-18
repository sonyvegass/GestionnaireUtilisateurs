from db_config import get_connection
from mysql.connector import Error

class Storage: # Classe Storage
    @staticmethod
    def sauvegarder_utilisateur(utilisateur): # Méthode pour sauvegarder un utilisateur
        """Sauvegarde ou met à jour un utilisateur dans la base de données"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT login FROM utilisateurs WHERE login = %s",
                (utilisateur['login'],)
            )
            
            if cursor.fetchone():
                query = """
                    UPDATE utilisateurs 
                    SET nom = %s, prenom = %s, role = %s, region = %s,
                        password = %s, createur = %s, expiration = %s
                    WHERE login = %s
                """
                values = (
                    utilisateur['nom'], utilisateur['prenom'], utilisateur['role'],
                    utilisateur['region'], utilisateur['password'],
                    utilisateur.get('createur'), utilisateur['expiration'],
                    utilisateur['login']
                )
            else:
                query = """
                    INSERT INTO utilisateurs (nom, prenom, login, role, region,
                                           password, createur, expiration)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    utilisateur['nom'], utilisateur['prenom'], utilisateur['login'],
                    utilisateur['role'], utilisateur['region'], utilisateur['password'],
                    utilisateur.get('createur'), utilisateur['expiration']
                )
            
            cursor.execute(query, values)
            conn.commit()
            return True
            
        except Error as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
            
        finally:
            conn.close()

    @staticmethod
    def charger_utilisateurs(filtres=None):
        """Charge les utilisateurs depuis la base de données avec filtres optionnels"""
        conn = get_connection()
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM utilisateurs"
            values = []
            
            if filtres:
                conditions = []
                if 'role' in filtres:
                    conditions.append("role = %s")
                    values.append(filtres['role'])
                if 'region' in filtres:
                    conditions.append("region = %s")
                    values.append(filtres['region'])
                    
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(query, values)
            utilisateurs = {user['login']: user for user in cursor.fetchall()}
            return utilisateurs
            
        except Error as e:
            print(f"❌ Erreur lors du chargement: {e}")
            return {}
            
        finally:
            conn.close()

    @staticmethod
    def supprimer_utilisateur(login):
        """Supprime un utilisateur de la base de données"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM utilisateurs WHERE login = %s", (login,))
            conn.commit()
            return cursor.rowcount > 0
            
        except Error as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False
            
        finally:
            conn.close()

    @staticmethod
    def verifier_session(login, token):
        """Vérifie si une session est valide"""
        conn = get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sessions 
                WHERE login = %s AND session_token = %s 
                AND expiration > NOW()
            """, (login, token))
            
            return cursor.fetchone()[0] > 0
            
        except Error as e:
            print(f"❌ Erreur lors de la vérification de session: {e}")
            return False
            
        finally:
            conn.close()