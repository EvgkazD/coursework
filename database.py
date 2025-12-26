try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError as e:
    PSYCOPG2_AVAILABLE = False
    print(f"psycopg2 недоступен: {e}")

class DatabaseManager:
    def __init__(self, host='localhost', port=5432, database='solit_db',
                 user='evgeniykazantseva', password=''):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
    def connect(self):
        if not PSYCOPG2_AVAILABLE:
            print("psycopg2 не установлен. База данных недоступна.")
            return False
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return True
        except Exception as e:
            print(f"Ошибка подключения к базе данных: {e}")
            return False
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    def player_name_exists(self, name):
        if not self.conn and not self.connect():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM game_results WHERE player_name = %s LIMIT 1;", (name,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Exception as e:
            print(f"Ошибка при проверке имени: {e}")
            return False
    def init_database(self):
        if not self.connect():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_results (
                    id SERIAL PRIMARY KEY,
                    player_name VARCHAR(100) NOT NULL UNIQUE,
                    game_time_seconds INTEGER,
                    won BOOLEAN NOT NULL,
                    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
                    score INTEGER DEFAULT 0,
                    hints_remaining INTEGER DEFAULT -1
                );
            """)
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")
            return False
    def save_result(self, player_name, game_time_seconds, won, difficulty="medium", score=0, hints_remaining=-1):
        if not self.conn and not self.connect():
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO game_results
                    (player_name, game_time_seconds, won, difficulty, score, hints_remaining)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (player_name) DO UPDATE SET
                    game_time_seconds = EXCLUDED.game_time_seconds,
                    won = EXCLUDED.won,
                    difficulty = EXCLUDED.difficulty,
                    score = EXCLUDED.score,
                    hints_remaining = EXCLUDED.hints_remaining;
            """, (player_name, game_time_seconds, won, difficulty, score, hints_remaining))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Ошибка сохранения результата: {e}")
            return False
    def get_results(self, limit=10):
        if not PSYCOPG2_AVAILABLE:
            return []
        if not self.conn and not self.connect():
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, player_name, game_time_seconds, won, difficulty, score, hints_remaining
                FROM game_results
                ORDER BY id DESC
                LIMIT %s;
            """, (limit,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"Ошибка при получении результатов: {e}")
            return []