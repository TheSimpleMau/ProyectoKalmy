# app/init_db.py
import logging
import random
from . import models, database, auth

logger = logging.getLogger("uvicorn")

def create_tables():
    """
    Crea las tablas en la base de datos y, si está vacía,
    inserta datos iniciales de prueba.
    """
    
    models.Base.metadata.create_all(bind=database.engine)
    
    db = database.SessionLocal()
    try:
        # Si no existen libros, iniciamos la base de datos con datos dummy.
        if db.query(models.Book).count() == 0:
            logger.info("--- Base de datos vacía. Sembrando datos de prueba... ---")
            libros_iniciales = [
                models.Book(name="La sombra del viento", author="Carlos Ruiz Zafón", description="Misterio literario en Barcelona", price=18.50, available=True),
                models.Book(name="Diccionario jázaro", author="Milorad Pavić", description="Novela experimental en forma de diccionario", price=22.00, available=True),
                models.Book(name="Actos humanos", author="Han Kang", description="Memoria y violencia en Corea del Sur", price=19.90, available=True),
                models.Book(name="Balún Canán", author="Rosario Castellanos", description="Novela sobre identidad y conflicto social en Chiapas", price=17.00, available=True),
                models.Book(name="Pedro Páramo", author="Juan Rulfo", description="Realismo mágico mexicano", price=14.00, available=True),
                models.Book(name="Rayuela", author="Julio Cortázar", description="Novela experimental argentina", price=21.00, available=True),
                models.Book(name="La ciudad y los perros", author="Mario Vargas Llosa", description="Crítica social en academia militar", price=18.00, available=True),
                models.Book(name="El amor en los tiempos del cólera", author="Gabriel García Márquez", description="Historia de amor y espera", price=19.50, available=True),
                models.Book(name="Como agua para chocolate", author="Laura Esquivel", description="Amor y cocina con realismo mágico", price=16.00, available=True),
                models.Book(name="La casa de los espíritus", author="Isabel Allende", description="Saga familiar chilena", price=20.00, available=False),
                models.Book(name="Ficciones", author="Jorge Luis Borges", description="Cuentos filosóficos argentinos", price=15.00, available=True),
                models.Book(name="El túnel", author="Ernesto Sabato", description="Novela psicológica argentina", price=13.50, available=True),
                models.Book(name="Los detectives salvajes", author="Roberto Bolaño", description="Búsqueda literaria en México", price=23.00, available=True),
                models.Book(name="La tregua", author="Mario Benedetti", description="Diario íntimo y amor tardío", price=14.50, available=True),
                models.Book(name="El llano en llamas", author="Juan Rulfo", description="Cuentos del México rural", price=12.50, available=True),
                models.Book(name="Santa", author="Federico Gamboa", description="Naturalismo mexicano", price=15.00, available=True),
                models.Book(name="Doña Bárbara", author="Rómulo Gallegos", description="Civilización y barbarie en Venezuela", price=17.00, available=True),
                models.Book(name="Huasipungo", author="Jorge Icaza", description="Denuncia social ecuatoriana", price=13.00, available=True),
                models.Book(name="La fiesta del chivo", author="Mario Vargas Llosa", description="Dictadura en República Dominicana", price=22.00, available=True),
                models.Book(name="El reino de este mundo", author="Alejo Carpentier", description="Real maravilloso caribeño", price=16.50, available=True),
                models.Book(name="Sobre héroes y tumbas", author="Ernesto Sabato", description="Novela existencial argentina", price=19.00, available=True),
                models.Book(name="Yo el Supremo", author="Augusto Roa Bastos", description="Dictadura paraguaya ficticia", price=18.00, available=True),
                models.Book(name="La muerte de Artemio Cruz", author="Carlos Fuentes", description="Crítica histórica mexicana", price=17.50, available=True),
                models.Book(name="El beso de la mujer araña", author="Manuel Puig", description="Diálogo carcelario argentino", price=15.50, available=True),
                models.Book(name="Arráncame la vida", author="Ángeles Mastretta", description="Mujer y poder en México", price=16.00, available=True),
                models.Book(name="Temporada de huracanes", author="Fernanda Melchor", description="Violencia contemporánea mexicana", price=21.00, available=True),
                models.Book(name="Nuestra parte de noche", author="Mariana Enriquez", description="Horror y dictadura argentina", price=24.00, available=False),
                models.Book(name="Delirio", author="Laura Restrepo", description="Crisis familiar en Colombia", price=18.00, available=True),
                models.Book(name="El obsceno pájaro de la noche", author="José Donoso", description="Novela compleja chilena", price=20.00, available=True),
                models.Book(name="Antes que anochezca", author="Reinaldo Arenas", description="Memorias cubanas", price=17.00, available=True),
                models.Book(name="Los recuerdos del porvenir", author="Elena Garro", description="Tiempo y memoria en México", price=16.50, available=True),
                models.Book(name="Aura", author="Carlos Fuentes", description="Novela corta fantástica mexicana", price=12.00, available=True),
                models.Book(name="El entenado", author="Juan José Saer", description="Conquista y reflexión argentina", price=15.00, available=True),
                models.Book(name="La amortajada", author="María Luisa Bombal", description="Monólogo desde la muerte", price=13.50, available=True),
                models.Book(name="Casa grande", author="Luis Orrego Luco", description="Crítica social chilena", price=14.00, available=True),
                models.Book(name="El astillero", author="Juan Carlos Onetti", description="Decadencia y fracaso uruguayo", price=15.50, available=True),
                models.Book(name="Crimen y castigo", author="Fiódor Dostoyevski", description="Novela psicológica rusa", price=18.00, available=True),
                models.Book(name="Orgullo y prejuicio", author="Jane Austen", description="Romance clásico inglés", price=14.00, available=True),
                models.Book(name="Moby-Dick", author="Herman Melville", description="Obsesión y mar", price=19.00, available=True),
                models.Book(name="La Odisea", author="Homero", description="Epopeya griega clásica", price=16.00, available=True),
                models.Book(name="Don Quijote de la Mancha", author="Miguel de Cervantes", description="Novela fundacional española", price=22.00, available=True),
                models.Book(name="Madame Bovary", author="Gustave Flaubert", description="Realismo francés", price=15.00, available=True),
                models.Book(name="Hamlet", author="William Shakespeare", description="Tragedia shakesperiana", price=13.00, available=True),
                models.Book(name="La metamorfosis", author="Franz Kafka", description="Transformación y alienación", price=12.00, available=True),
                models.Book(name="Guerra y paz", author="León Tolstói", description="Épica histórica rusa", price=25.00, available=False),
                models.Book(name="El extranjero", author="Albert Camus", description="Existencialismo francés", price=14.50, available=True),
                ]
            
            for libro in libros_iniciales:
                if libro.available:
                    libro.stock = random.randint(5, 30)
                else:
                    libro.stock = 0
            
            db.add_all(libros_iniciales)
            db.commit()
            logger.info("--- Datos dummy hechos ---")
        else:
            logger.info("--- La base de datos ya tiene datos. Omitiendo. ---")

        # --- Usuario Admin ---
        if db.query(models.User).count() == 0:
            logger.info("--- Creando usuario Admin... ---")
            hashed_pwd = auth.get_password_hash("admin123")
            admin_user = models.User(username="admin", hashed_password=hashed_pwd, role="admin")
            db.add(admin_user)
            db.commit()
            logger.info("--- Usuario 'admin' con password 'admin123' creado ---")
            
            logger.info("--- Creando usuario Empleado... ---")
            hashed_pwd = auth.get_password_hash("empleado123")
            admin_user = models.User(username="empleado", hashed_password=hashed_pwd, role="employee")
            db.add(admin_user)
            db.commit()
            logger.info("--- Usuario 'empleado' con password 'empleado123' creado ---")
            
            logger.info("--- Creando usuario Test... ---")
            hashed_pwd = auth.get_password_hash("test123")
            admin_user = models.User(username="test", hashed_password=hashed_pwd, role="user")
            db.add(admin_user)
            db.commit()
            logger.info("--- Usuario 'test' con password 'test123' creado ---")
            
    except Exception as e:
        logger.error(f"Error durante la inicialización de la DB: {e}")
    finally:
        db.close()