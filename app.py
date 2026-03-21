import sqlite3
import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

class MedicalSearchEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_all_tables(self, cursor):
        """Veritabanındaki tüm kullanıcı tablolarını getirir."""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_columns(self, cursor, table_name):
        """Belirli bir tablonun sütun isimlerini getirir."""
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        return [row[1] for row in cursor.fetchall()]

    def search(self, query_text):
        """Kullanıcı sorgusunu tüm tablolarda ve tüm sütunlarda dinamik olarak arar."""
        if not query_text or len(query_text.strip()) < 2:
            return []

        search_results = []
        keywords = query_text.lower().split()
        
        try:
            if not os.path.exists(self.db_path):
                return {"error": "Veritabanı dosyası bulunamadı."}

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            tables = self.get_all_tables(cursor)
            
            for table in tables:
                columns = self.get_table_columns(cursor, table)
                where_clauses = []
                params = []
                
                for word in keywords:
                    column_clauses = []
                    for col in columns:
                        column_clauses.append(f"CAST(\"{col}\" AS TEXT) LIKE ?")
                        params.append(f"%{word}%")
                    where_clauses.append(f"({' OR '.join(column_clauses)})")
                
                sql = f"SELECT * FROM \"{table}\" WHERE {' AND '.join(where_clauses)}"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    row_dict = dict(row)
                    # Başlık için öncelikli sütunları belirle
                    title = row_dict.get('Tanı Adı') or row_dict.get('Tanı') or row_dict.get('Adı') or list(row_dict.values())[0]
                    
                    search_results.append({
                        "table": table.replace("_", " "),
                        "title": title,
                        "details": row_dict
                    })

            conn.close()
            return search_results

        except Exception as e:
            return {"error": f"Sistem hatası: {str(e)}"}

# Motoru başlat
engine = MedicalSearchEngine("TANISIST..db")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '')
    results = engine.search(query)
    return jsonify(results)

if __name__ == '__main__':
    # Render veya diğer platformlar için port ayarı
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)