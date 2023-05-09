from flask import Flask, render_template, request, jsonify
import os
import psycopg2
app = Flask(__name__)

def connection():
    
    DB_NAME=os.getenv('DB_NAME')
    DB_USER=os.getenv('DB_USER')
    DB_HOST=os.getenv('DB_HOST')
    DB_PORT=os.getenv('DB_PORT')
    DB_PASSWORD=os.getenv('DB_PASSWORD')
    conn = psycopg2.connect(dbname=DB_NAME,user=DB_USER,host=DB_HOST,port=DB_PORT,password=DB_PASSWORD)
    return conn

def return_companies():
    try:
        con = connection()
        cur = con.cursor()
        cur.execute('select ondernemingsnummer, naam from view_website_data order by naam asc')
        return cur.fetchall()
    except:
        return [[]]
    

def return_sectoren():
    try:
        con = connection()
        cur = con.cursor()
        cur.execute('select sectornaam from view_sector_overview order by sectornaam asc')
        return cur.fetchall()
    except:
        return [[]]

@app.route("/")
def index():
    
    conn = connection()
    cur = conn.cursor()

    try:
        cur.execute('select * from view_website_data order by domein_environment desc limit 5')
        results_E = cur.fetchall()
    except:
        results_E = [[]]

    try:
        cur.execute('select * from view_website_data order by domein_social desc limit 5')
        results_S = cur.fetchall()
    except:
        results_S = [[]]

    try:
        cur.execute('select * from view_website_data order by domein_governance desc limit 5')
        results_G = cur.fetchall()
    except:
        results_G = [[]]

    cur.close()
    conn.close()
    return render_template('index.html', E=results_E, S=results_S, G=results_G, nav=return_companies(), sectoren=return_sectoren())


@app.route('/company', methods=['GET','POST'])
def give_company():
    id = request.args.get('id')

    try:
        conn = connection()
        cur = conn.cursor()
        query = f'select * from view_website_data where ondernemingsnummer = {id}'
        cur.execute(f'select * from view_website_data where ondernemingsnummer = {id}')
        results_company = cur.fetchall()
        return render_template('overzicht-bedrijf.html', result=results_company, nav=return_companies())
    except Exception as e:
        return render_template('error.html', error = f'{id} kon niet worden gevonden. {e}', query = query)
    
@app.route('/sector', methods=['GET','POST'])
def give_sector():
    id = request.args.get('id')
    try:
        conn = connection()
        cur = conn.cursor()
        query = f"""select * from view_sector_overview where sectornaam = '{id}'"""
        cur.execute(query)
        results_sector = cur.fetchall()
        return render_template('overzicht-sector.html', result=results_sector, nav=return_companies())
    except Exception as e:
        return render_template('error.html', error = f'{id} kon niet worden gevonden. {e}', query = query)

@app.route('/search', methods=['GET', 'POST'])
def return_search_engine():
    return render_template('search-engine.html', nav=return_companies(), sectoren=return_sectoren())


@app.route('/search-by', methods=['GET', 'POST'])
def return_looked_up_companies():
    name = request.args.get('name')
    sector = request.args.get('sector')
    zoekwoorden = request.args.get('zoekwoord')

    query = f"""
    select k.ondernemingsnummer, k.naam, v.* 
    from "KMO" k
    left join view_website_data v on v.ondernemingsnummer = k.ondernemingsnummer
    where ts_document @@ to_tsquery('english')
    """

    return jsonify(name=name, sector=sector, zoekwoorden=zoekwoorden)


if __name__ == "__main__":
    app.run()