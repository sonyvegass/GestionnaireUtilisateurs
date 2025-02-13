# db_config.py
from mysql.connector import connect, Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123',  # À modifier selon votre configuration
    'database': 'hospital_users'
}

def init_database():
    """Initialise la base de données et les tables"""
    try:
        # Première connexion pour créer la base de données
        conn = connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Création de la base de données
        cursor.execute("CREATE DATABASE IF NOT EXISTS hospital_users")
        cursor.execute("USE hospital_users")
        
        # Création de la table utilisateurs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                prenom VARCHAR(100) NOT NULL,
                login VARCHAR(50) UNIQUE NOT NULL,
                role ENUM('super_admin', 'admin', 'utilisateur') NOT NULL,
                region ENUM('Paris', 'Rennes', 'Strasbourg', 'Grenoble', 'Nantes'),
                password VARCHAR(256) NOT NULL,
                createur VARCHAR(50),
                expiration DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Création de la table sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login VARCHAR(50) NOT NULL,
                session_token VARCHAR(256) NOT NULL,
                expiration DATETIME NOT NULL,
                FOREIGN KEY (login) REFERENCES utilisateurs(login)
            )
        """)
        
        # Création de la table tentatives_connexion
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tentatives_connexion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                login VARCHAR(50) NOT NULL,
                tentatives INT DEFAULT 0,
                derniere_tentative DATETIME,
                FOREIGN KEY (login) REFERENCES utilisateurs(login)
            )
        """)
        
        conn.commit()
        print("✅ Base de données et tables créées avec succès!")
        
        return True
        
    except Error as e:
        print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def get_connection():
    """Retourne une connexion à la base de données"""
    try:
        return connect(**DB_CONFIG)
    except Error as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None