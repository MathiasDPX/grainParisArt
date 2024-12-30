import time
import logging
import psycopg2
from os import getenv
from dotenv import load_dotenv
from typing import Optional, Any
from psycopg2 import OperationalError
from ua_parser import parse_os, parse_user_agent

load_dotenv()

class DatabaseConnector:
    def __init__(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize database connector with connection parameters and retry settings.
        
        Args:
            dbname: Database name
            user: Database user
            password: Database password
            host: Database host
            port: Database port
            max_retries: Maximum number of reconnection attempts
            retry_delay: Delay between retry attempts in seconds
        """
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn: Optional[psycopg2.extensions.connection] = None
        self.cur: Optional[psycopg2.extensions.cursor] = None
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cur = self.conn.cursor()
            self.logger.info("Successfully connected to the database")
            return True
        except OperationalError as e:
            self.logger.error(f"Error connecting to the database: {e}")
            return False

    def ensure_connection(self) -> bool:
        """
        Ensure database connection is active, attempt to reconnect if necessary.
        
        Returns:
            bool: True if connection is active or reconnection successful
        """
        if self.conn and not self.conn.closed:
            try:
                # Test connection with simple query
                self.cur.execute("SELECT 1")
                return True
            except (psycopg2.Error, AttributeError):
                self.logger.warning("Database connection lost")
                
        # Connection is closed or failed, attempt to reconnect
        for attempt in range(self.max_retries):
            self.logger.info(f"Attempting to reconnect (attempt {attempt + 1}/{self.max_retries})")
            if self.connect():
                return True
            time.sleep(self.retry_delay)
        
        self.logger.error("Failed to reconnect to database after multiple attempts")
        return False

    def execute_query(self, query: str, params: tuple = None) -> Optional[Any]:
        """
        Execute a database query with automatic reconnection on failure.
        
        Args:
            query: SQL query string
            params: Query parameters (optional)
            
        Returns:
            Query results if successful, None if failed
        """
        if not self.ensure_connection():
            return None

        try:
            self.cur.execute(query, params)
            
            # Check if query is a SELECT statement
            if query.strip().upper().startswith("SELECT"):
                results = self.cur.fetchall()
                self.conn.commit()
                return results
            else:
                self.conn.commit()
                return True
                
        except psycopg2.Error as e:
            self.logger.error(f"Error executing query: {e}")
            self.conn.rollback()
            return None

    def close(self):
        """Close database connection and cursor."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            self.logger.info("Database connection closed")

isInit = getenv("monitoring_enabled").lower() == "true"

if isInit:
    db = DatabaseConnector(
        dbname=getenv("db_name"),
        user=getenv("db_user"),
        password=getenv("db_password"),
        host=getenv("db_host"),
        port=getenv("db_port")
    )

    db.execute_query("""CREATE TABLE IF NOT EXISTS "cinema_queries" (
                        "ip" VARCHAR(39) NOT NULL,
                        "time" TIMESTAMP NOT NULL,
                        "browser" VARCHAR(255) NULL DEFAULT 'unknown',
                        "os" VARCHAR(255) NULL DEFAULT 'unknown',
                        "day" int NULL DEFAULT 1
                    );
    """)

def log(ip:str, useragent:str, day:int) -> bool:
    if not isInit: return True
    os = parse_os(useragent)
    browser = parse_user_agent(useragent)

    os_family = os.family if os != None else "unknown"
    browser_family = browser.family if browser != None else "unknown"

    success = db.execute_query(f"INSERT INTO cinema_queries (ip, time, browser, os, day) VALUES (\'{ip}\', current_timestamp, \'{browser_family}\', \'{os_family}\', {day});")
    return success