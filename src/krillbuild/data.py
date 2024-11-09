import sqlite3

class KrillTrackedFile():

    def __init__(self, name, hash, filepath, parent_hash=None):
        self._name = name
        self._path = filepath
        self._hash = hash
        self._parent_hash = parent_hash

    @property
    def name(self):
        return self._name
    
    @property
    def hash(self):
        return self._hash
    
    @property
    def parent_hash(self):
        if self._parent_hash is None:
            return ""
        return self._parent_hash

class KrillDatabase():

    def __init__(self, db_path):
        self._db = sqlite3.connect(db_path)

    def has_table(self, table):
        cur = self._db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
        return cur.fetchone() is not None
    
    def _ensure_file_table(self):
        if not self.has_table("files"):
            cur = self._db.cursor()
            cur.execute("CREATE TABLE files(sha256 TEXT UNIQUE, parent_sha256, filename)")
            self._db.commit()

    def list_files(self):
        self._ensure_file_table()
        cur = self._db.cursor()
        cur.execute("SELECT * FROM files")
        return cur.fetchall()

    def get_file(self, sha256_hash):
        self._ensure_file_table()
        cur = self._db.cursor()
        params = (sha256_hash,)
        cur.execute("SELECT * FROM files WHERE sha256 = ?", params)
        return cur.fetchone()

    def insert_file(self, filename, sha256_hash, parent_sha256_hash=None):
        self._ensure_file_table()
        if parent_sha256_hash is not None:
            parent_data = self.get_file(parent_sha256_hash)
            if parent_data is None:
                raise ValueError("Parent hash not found")
            
        check_data = self.get_file(sha256_hash)
        if check_data is None:
            cur = self._db.cursor()
            cur.execute("INSERT INTO files VALUES(?, ?, ?)", (sha256_hash, parent_sha256_hash, filename))
            self._db.commit()