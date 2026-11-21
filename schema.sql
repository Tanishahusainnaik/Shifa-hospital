CREATE DATABASE IF NOT EXISTS medicare CHARACTER SET utf8mb4;
USE medicare;
CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY, full_name VARCHAR(100) NOT NULL, email VARCHAR(120) UNIQUE NOT NULL, phone VARCHAR(20), doctor_id INT NULL, dob DATE, address VARCHAR(255), password_hash VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS departments(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(60) UNIQUE, icon VARCHAR(40), description VARCHAR(300));
CREATE TABLE IF NOT EXISTS doctors(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(80), department_id INT, qualification VARCHAR(120), experience INT, availability VARCHAR(80), bio VARCHAR(300), FOREIGN KEY(department_id) REFERENCES departments(id));
CREATE TABLE IF NOT EXISTS appointments(id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, full_name VARCHAR(100), email VARCHAR(120), phone VARCHAR(20), doctor_id INT, department_id INT, appt_date DATE, slot VARCHAR(20), reason TEXT, status VARCHAR(20) DEFAULT 'Confirmed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY uniq_slot(doctor_id,appt_date,slot), FOREIGN KEY(doctor_id) REFERENCES doctors(id), FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS messages(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(120), subject VARCHAR(150), body TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
INSERT IGNORE INTO departments(name,icon,description) VALUES
('Cardiology','bi-heart-pulse','Heart rhythm, blockage and failure care with 24/7 cath lab support.'),
('Neurology','bi-activity','Stroke, epilepsy, migraine and nerve disorder diagnosis and treatment.'),
('Orthopaedics','bi-person-walking','Joint replacement, sports injury and fracture care with fast rehabilitation.'),
('Dermatology','bi-droplet-half','Skin, hair and nail care, from acne to laser procedures.'),
('Paediatrics','bi-balloon-heart','Gentle care for newborns, children and teenagers, including vaccination.'),
('Gynaecology','bi-gender-female','Pregnancy, delivery, fertility and women''s wellness care.'),
('General Medicine','bi-clipboard2-pulse','First point of care for fever, diabetes, blood pressure and infections.'),
('Dentistry','bi-emoji-smile','Routine dental care, root canals, implants and cosmetic dentistry.'),
('Oncology','bi-shield-plus','Cancer screening, chemotherapy, radiation and supportive care.'),
('Emergency Medicine','bi-lightning-charge','Round-the-clock trauma and critical care with rapid triage.');
INSERT INTO doctors(name,department_id,qualification,experience,availability,bio) SELECT * FROM (
SELECT 'Dr. Arjun Mehta' n,1 d,'MD, DM Cardiology' q,18 e,'Mon, Wed, Fri' a,'Interventional cardiologist focused on minimally invasive heart procedures.' b UNION ALL
SELECT 'Dr. Priya Nair',2,'MD, DM Neurology',14,'Tue, Thu, Sat','Stroke and epilepsy specialist.' UNION ALL
SELECT 'Dr. Rohan Kulkarni',3,'MS Orthopaedics',16,'Mon to Fri','Joint replacement and sports injury surgeon.' UNION ALL
SELECT 'Dr. Sana Sheikh',4,'MD Dermatology',9,'Mon, Tue, Thu','Clinical and cosmetic dermatologist.' UNION ALL
SELECT 'Dr. Vikram Rao',5,'MD Paediatrics',12,'Mon to Sat','Child health and vaccination expert.' UNION ALL
SELECT 'Dr. Ananya Desai',6,'MS, DNB Obstetrics',15,'Tue to Sat','High-risk pregnancy and laparoscopic surgery.' UNION ALL
SELECT 'Dr. Imran Patil',7,'MD General Medicine',11,'Mon to Sat','Diabetes and lifestyle disease management.' UNION ALL
SELECT 'Dr. Neha Joshi',8,'BDS, MDS',8,'Mon, Wed, Fri, Sat','Implantologist and cosmetic dentist.' UNION ALL
SELECT 'Dr. Suresh Hegde',9,'MD, DM Oncology',20,'Tue, Thu','Medical oncologist with focus on early detection.' UNION ALL
SELECT 'Dr. Kavita Menon',10,'MD Emergency Medicine',10,'24/7 rotation','Trauma and critical care lead.') t WHERE NOT EXISTS(SELECT 1 FROM doctors);
