from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import psycopg2


load_dotenv()
DB_NAME=os.getenv('DB_NAME')
DB_USER=os.getenv('DB_USER')
DB_HOST=os.getenv('DB_HOST')
DB_PORT=os.getenv('DB_PORT')
DB_PASSWORD=os.getenv('DB_PASSWORD')
conn = psycopg2.connect(dbname=DB_NAME,user=DB_USER,host=DB_HOST,port=DB_PORT,password=DB_PASSWORD)
cur = conn.cursor()
cur.execute('select * from zoektermen')

zoektermen = cur.fetchall()


for z in zoektermen:
    to_search = str(z[1]).replace(' ', ' | ')
    query = f"""SELECT '{z[1]}', sectorid, COUNT(*) AS aantalBedrijven, ROUND((COUNT(*)*100.0)/(SELECT COUNT(*) FROM "KMO" k LEFT JOIN "Balans" b ON k.ondernemingsnummer = b.ondernemingsnummer WHERE b.ts_document @@ to_tsquery('dutch', '{to_search}')), 2) AS percentageOpTotaalBasis FROM "KMO" k LEFT JOIN "Balans" b ON k.ondernemingsnummer = b.ondernemingsnummer WHERE b.ts_document @@ to_tsquery('dutch', '{to_search}') GROUP BY sectorid;"""
    cur.execute(query)
    woordenPerSector = cur.fetchall()
    print(woordenPerSector)
