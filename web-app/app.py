from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import psycopg2
app = Flask(__name__)

def connection():
    load_dotenv()
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
    

def return_searchwords():
    try:
        con = connection()
        cur = con.cursor()
        cur.execute('select z.zoekterm_description, c.categorie_naam from zoektermen z left join categorie_zoektermen c on c.categorie_id = z.categorie_id')

        result = cur.fetchall()
        output = {}
        for row in result:
            category = row[1]
            value = row[0]
            if category not in output:
                output[category] = []
            output[category].append(value)
        return(output)

    except Exception as e:
        print(e)
        return [[]]

@app.route("/")
def index():
    try:
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
    except:
        return render_template('error.html')

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


@app.route('/rapportering', methods=['GET','POST'])
def give_reports():

    cat_id = request.args.get('catid')
    if cat_id is not None:
        filter = f"""where categorie_id = {cat_id}"""
    else:
        filter = ""

    con = connection()
    cur = con.cursor()


    cur.execute('select * from categorie_zoektermen')
    categorieën = cur.fetchall()

    cur.execute(f'select categorie_id, zoekterm_description from zoektermen {filter}')
    zoektermen = cur.fetchall()

    cur.execute(f'select * from "Sector"')
    sectoren = cur.fetchall()

    total = []

    for z in zoektermen:
        to_search = str(z[1]).replace(' ', ' | ')
        query = f"""SELECT '{z[0]}', '{z[1]}', sectorid, COUNT(*) AS aantalBedrijven, ROUND((COUNT(*)*100.0)/(SELECT COUNT(*) FROM "KMO" k LEFT JOIN "Balans" b ON k.ondernemingsnummer = b.ondernemingsnummer WHERE b.ts_document @@ to_tsquery('dutch', '{to_search}')), 2) AS percentageOpTotaalBasis FROM "KMO" k LEFT JOIN "Balans" b ON k.ondernemingsnummer = b.ondernemingsnummer WHERE b.ts_document @@ to_tsquery('dutch', '{to_search}') GROUP BY sectorid ORDER BY ROUND((COUNT(*)*100.0)/(SELECT COUNT(*) FROM "KMO" k LEFT JOIN "Balans" b ON k.ondernemingsnummer = b.ondernemingsnummer WHERE b.ts_document @@ to_tsquery('dutch', '{to_search}')), 2) DESC;"""
        cur.execute(query)
        woordenPerSector = cur.fetchall()
        if woordenPerSector != []:
            total.append(woordenPerSector)

    return render_template('rapportering.html', results=total, categories=categorieën, catid = cat_id, sectoren = sectoren)


@app.route('/search', methods=['GET', 'POST'])
def return_search_engine():
    results = dict(request.args)

    if results:
        if (results['sector'] != 'any'):
            sector_filter = f"""v.sectornaam = '{results['sector']}' and"""
        else:
            sector_filter = ""

        searchwords = results['searchwords'].split('\n')
        searchwords = searchwords[:-1]

        output = {}
        for word in searchwords:
            if results['type'] == 'jaarverslag':
                query = f"""
                select k.ondernemingsnummer, k.naam, v.sectornaam, v.{results['domain']} 
                from "KMO" k
                left join "Balans" b on b.ondernemingsnummer = k.ondernemingsnummer
                left join view_website_data v on v.ondernemingsnummer = b.ondernemingsnummer
                where 
                    b.ts_document @@ to_tsquery('english', '{word.replace(' ','')}') and
                    {sector_filter}
                    {results['domain']} >= {float(results['percentile'])/100}
                order by v.{results['domain']} desc
                limit {results['amount']};
                """
            else:
                query = f"""
                select k.ondernemingsnummer, k.naam, v.sectornaam, v.{results['domain']} 
                from "KMO" k
                left join view_website_data v on v.ondernemingsnummer = k.ondernemingsnummer
                where 
                    ts_document @@ to_tsquery('english', '{word.replace(' ','')}') and
                    {sector_filter} and
                    {results['domain']} >= {float(results['percentile'])/100}
                order by v.{results['domain']} desc
                limit {results['amount']};
                """

            conn = connection()
            cur = conn.cursor()
            try:
                cur.execute(query)
                output[word] = list(cur.fetchall())
            except Exception as e:
                print(e)
    else:
        output = {}

    nav = return_companies()
    sectoren = return_sectoren()
    searchwords = return_searchwords()

    return render_template('search-engine.html', nav=nav, sectoren=sectoren, searchwords=searchwords, results=output)

if __name__ == "__main__":
    app.run()