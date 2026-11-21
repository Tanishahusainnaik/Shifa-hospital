# Shifa Hospital (Flask + MySQL + Bootstrap)
1. `pip install -r requirements.txt`
2. `mysql -u root -p < schema.sql` (creates DB `medicare`, tables and sample doctors/departments)
3. Set env vars if needed: `DB_HOST DB_USER DB_PASSWORD DB_NAME SECRET_KEY`
4. `python app.py` then open http://127.0.0.1:5000
Optional: add a hospital photo at `static/img/hero.jpg` (the hero falls back to a gradient without it).



set DB_PASSWORD=

python create_doctors.py -once only its done

python app.py